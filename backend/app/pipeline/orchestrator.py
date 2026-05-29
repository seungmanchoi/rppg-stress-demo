"""Run all algorithm adapters on one video and aggregate per-algorithm results."""
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

import numpy as np

from app.models.registry import get_meta
from app.pipeline.hrv.freq_domain import freq_domain_hrv
from app.pipeline.hrv.nonlinear import poincare
from app.pipeline.hrv.peak_detect import bvp_to_ibi
from app.pipeline.hrv.time_domain import time_domain_hrv
from app.pipeline.preprocess.face_roi import extract_roi_signal
from app.pipeline.preprocess.frame_decoder import decode_video
from app.pipeline.preprocess.quality_gate import assess
from app.pipeline.reliability.scoring import reliability_grade, reliability_score
from app.pipeline.reliability.snr import bvp_snr_db
from app.pipeline.stress.baevsky import baevsky_si
from app.pipeline.stress.composite import composite_level, composite_stress

log = logging.getLogger(__name__)

UNSUP_IDS = {"POS", "CHROM", "OMIT"}
SUPERVISED_IDS = {"TS-CAN", "EfficientPhys", "PhysFormer", "RhythmFormer", "BigSmall"}

ProgressCb = Callable[[float, str], Awaitable[None]]


def _adapter_for(algo_id: str):
    if algo_id == "POS":
        from app.pipeline.algorithms.unsupervised.pos import PosAdapter
        return PosAdapter()
    if algo_id == "CHROM":
        from app.pipeline.algorithms.unsupervised.chrom import ChromAdapter
        return ChromAdapter()
    if algo_id == "OMIT":
        from app.pipeline.algorithms.unsupervised.omit import OmitAdapter
        return OmitAdapter()
    if algo_id == "TS-CAN":
        from app.pipeline.algorithms.supervised.ts_can import TsCanAdapter
        return TsCanAdapter()
    if algo_id == "EfficientPhys":
        from app.pipeline.algorithms.supervised.efficientphys import EfficientPhysAdapter
        return EfficientPhysAdapter()
    if algo_id == "PhysFormer":
        from app.pipeline.algorithms.supervised.physformer import PhysFormerAdapter
        return PhysFormerAdapter()
    if algo_id == "RhythmFormer":
        from app.pipeline.algorithms.supervised.rhythmformer import RhythmFormerAdapter
        return RhythmFormerAdapter()
    if algo_id == "BigSmall":
        from app.pipeline.algorithms.supervised.bigsmall import BigSmallAdapter
        return BigSmallAdapter()
    raise KeyError(algo_id)


def _downsample(arr: np.ndarray, n: int = 150) -> list[float]:
    if len(arr) == 0:
        return []
    if len(arr) <= n:
        return arr.astype(float).tolist()
    idx = np.linspace(0, len(arr) - 1, n).astype(int)
    return arr[idx].astype(float).tolist()


def _run_one(algo_id: str, rgb_signal, frames, fs):
    t0 = time.perf_counter()
    try:
        adapter = _adapter_for(algo_id)
        bvp = adapter.estimate_bvp(rgb_signal, frames, fs)
        return algo_id, bvp, (time.perf_counter() - t0) * 1000, None
    except Exception as e:  # noqa: BLE001
        return algo_id, None, (time.perf_counter() - t0) * 1000, f"{type(e).__name__}: {e}"


async def run_pipeline(
    video_path: Path,
    algorithm_ids: list[str],
    progress_cb: ProgressCb | None = None,
) -> dict:
    import time as _time
    t_start = _time.perf_counter()

    async def _emit(p: float, stage: str):
        if progress_cb:
            await progress_cb(p, stage)

    await _emit(0.05, "decode")
    t0 = _time.perf_counter()
    frames, fs, (h, w) = decode_video(video_path, target_fps=30)
    decode_ms = (_time.perf_counter() - t0) * 1000
    duration_s = float(len(frames) / fs)

    await _emit(0.25, "face_roi")
    t0 = _time.perf_counter()
    rgb_signal, detected, _ = extract_roi_signal(frames, roi_crops=False)
    face_ms = (_time.perf_counter() - t0) * 1000

    await _emit(0.45, "quality")
    t0 = _time.perf_counter()
    quality = assess(frames, detected)
    quality_ms = (_time.perf_counter() - t0) * 1000

    await _emit(0.55, "algorithms")
    loop = asyncio.get_running_loop()
    results_raw: list[tuple[str, np.ndarray | None, float, str | None]] = []
    for aid in algorithm_ids:
        res = await loop.run_in_executor(None, _run_one, aid, rgb_signal, frames, fs)
        results_raw.append(res)
        progress = 0.55 + 0.4 * (len(results_raw) / max(1, len(algorithm_ids)))
        await _emit(progress, f"done:{aid}")

    # Per-algorithm HRV + stress
    per_algo: list[dict] = []
    hr_values: list[float] = []
    for aid, bvp, compute_ms, err in results_raw:
        meta = get_meta(aid)
        if err or bvp is None or len(bvp) == 0:
            per_algo.append(
                {
                    "id": aid,
                    "meta": meta.to_dict(),
                    "available": False,
                    "error": err or "no signal",
                    "compute_ms": compute_ms,
                }
            )
            continue
        ibi = bvp_to_ibi(bvp, fs)
        # IBI 추출 실패 — 측정 자체가 실패한 케이스로 표시 (stress=0이 카드에 노출되는 것 방지)
        if len(ibi) < 16:
            per_algo.append(
                {
                    "id": aid,
                    "meta": meta.to_dict(),
                    "available": False,
                    "error": f"맥파에서 박동을 충분히 검출하지 못함 (IBI {len(ibi)}개, 16개 필요)",
                    "compute_ms": compute_ms,
                }
            )
            continue
        td = time_domain_hrv(ibi)
        fd = freq_domain_hrv(ibi)
        pc = poincare(ibi)
        bv = baevsky_si(ibi)
        # 주파수 분석이 실패한 (LF/HF=0) 케이스도 측정 부정확으로 강등
        if fd.lf_hf_ratio == 0 and bv.si == 0:
            per_algo.append(
                {
                    "id": aid,
                    "meta": meta.to_dict(),
                    "available": False,
                    "error": "심박 간격의 주파수 분석 실패 — 신호가 부족합니다",
                    "compute_ms": compute_ms,
                }
            )
            continue
        comp = composite_stress(bv.si, fd.lf_hf_ratio, td.rmssd_ms)
        snr = bvp_snr_db(bvp, fs)
        if td.hr_bpm > 0:
            hr_values.append(td.hr_bpm)
        per_algo.append(
            {
                "id": aid,
                "meta": meta.to_dict(),
                "available": True,
                "bvp": bvp,
                "ibi": ibi,
                "hrv": td,
                "freq": fd,
                "poincare": pc,
                "baevsky": bv,
                "composite": comp,
                "snr_db": snr,
                "compute_ms": compute_ms,
            }
        )
    median_hr = float(np.median(hr_values)) if hr_values else 0.0

    # Reliability
    for a in per_algo:
        if not a["available"]:
            continue
        rel = reliability_score(
            snr_db=a["snr_db"],
            tracking=quality.detected_ratio,
            motion_px=quality.mean_motion_px,
            hr_dev=a["hrv"].hr_bpm - median_hr if median_hr else 0,
        )
        a["reliability"] = rel
        a["reliability_grade"] = reliability_grade(rel)

    await _emit(1.0, "done")
    total_ms = (_time.perf_counter() - t_start) * 1000

    return {
        "timing": {
            "total_ms": total_ms,
            "decode_ms": decode_ms,
            "face_roi_ms": face_ms,
            "quality_ms": quality_ms,
            "video_duration_s": duration_s,
        },
        "per_algo": per_algo,
        "median_hr": median_hr,
        "quality": quality,
        "video_meta": {
            "duration_s": duration_s,
            "fps": float(fs),
            "resolution": [int(h), int(w)],
        },
    }
