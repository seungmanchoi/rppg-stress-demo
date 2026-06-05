"""Run all algorithm adapters on one video and aggregate per-algorithm results."""
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

import numpy as np

from app.models.registry import get_meta
from app.pipeline.experimental.spo2_rgb import estimate_spo2_rgb
from app.pipeline.hrv.freq_domain import freq_domain_hrv
from app.pipeline.hrv.nonlinear import nonlinear_hrv, poincare
from app.pipeline.hrv.peak_detect import bvp_to_ibi
from app.pipeline.hrv.time_domain import time_domain_hrv
from app.pipeline.morphology.bvp_quality import bvp_quality
from app.pipeline.preprocess.face_roi import extract_roi_signal
from app.pipeline.preprocess.frame_decoder import decode_video
from app.pipeline.preprocess.quality_gate import assess
from app.pipeline.reliability.scoring import reliability_grade, reliability_score
from app.pipeline.reliability.snr import bvp_snr_db
from app.pipeline.respiration.bvp_resp import respiration_from_bvp
from app.pipeline.stress.baevsky import baevsky_si
from app.pipeline.stress.coherence import cardiac_coherence
from app.pipeline.stress.composite import composite_level, composite_stress, composite_stress_breakdown
from app.pipeline.stress.composite_v2 import composite_stress_v2
from app.pipeline.stress.kubios import kubios_indices

log = logging.getLogger(__name__)

UNSUP_IDS = {"POS", "CHROM", "OMIT", "GREEN", "ICA"}
SUPERVISED_IDS = {
    "TS-CAN", "EfficientPhys", "PhysFormer", "RhythmFormer", "BigSmall",
    "PhysNet", "DeepPhys",
}

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
    if algo_id == "GREEN":
        from app.pipeline.algorithms.unsupervised.green import GreenAdapter
        return GreenAdapter()
    if algo_id == "ICA":
        from app.pipeline.algorithms.unsupervised.ica import IcaAdapter
        return IcaAdapter()
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
    if algo_id == "PhysNet":
        from app.pipeline.algorithms.supervised.physnet import PhysNetAdapter
        return PhysNetAdapter()
    if algo_id == "DeepPhys":
        from app.pipeline.algorithms.supervised.deepphys import DeepPhysAdapter
        return DeepPhysAdapter()
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
        nl = nonlinear_hrv(ibi)
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
        v1 = composite_stress_breakdown(bv.si, fd.lf_hf_ratio, td.rmssd_ms)
        snr = bvp_snr_db(bvp, fs)
        kubios = kubios_indices(
            mean_rr_ms=td.ibi_mean_ms,
            rmssd_ms=td.rmssd_ms,
            hf_nu=fd.hf_nu,
            hr_bpm=td.hr_bpm,
            baevsky_si=bv.si,
            lf_nu=fd.lf_nu,
        )
        coh = cardiac_coherence(ibi)
        resp = respiration_from_bvp(bvp, fs)
        bvp_q = bvp_quality(bvp, fs)
        spo2 = estimate_spo2_rgb(rgb_signal, fs)
        v2 = composite_stress_v2(
            baevsky_si=bv.si,
            lf_hf=fd.lf_hf_ratio,
            rmssd_ms=td.rmssd_ms,
            sns_index=kubios.sns_index,
            pns_index=kubios.pns_index,
            sample_entropy=nl.sample_entropy,
            dfa_alpha1=nl.dfa_alpha1,
            coherence=coh.score,
            respiration_rpm=resp.rate_rpm,
        )
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
                "nonlinear": nl,
                "baevsky": bv,
                "composite": v1.score,
                "composite_v1": v1,
                "composite_v2": v2,
                "snr_db": snr,
                "kubios": kubios,
                "coherence": coh,
                "respiration": resp,
                "bvp_quality": bvp_q,
                "spo2": spo2,
                "compute_ms": compute_ms,
            }
        )
    # Reference HR from unsupervised algorithms only (POS/CHROM/OMIT) —
    # they don't share the supervised models' harmonic-lock failure mode.
    unsup_hrs = [
        a["hrv"].hr_bpm
        for a in per_algo
        if a.get("available") and a["id"] in UNSUP_IDS and a["hrv"].hr_bpm > 0
    ]
    reference_hr = float(np.median(unsup_hrs)) if len(unsup_hrs) >= 2 else 0.0

    # HR sanity check: any card whose HR is >25 BPM off the unsupervised reference
    # is almost certainly harmonic-locked or otherwise broken. Demote it.
    HR_SANITY_TOLERANCE_BPM = 25.0
    if reference_hr > 0:
        for a in per_algo:
            if not a.get("available"):
                continue
            hr_dev = abs(a["hrv"].hr_bpm - reference_hr)
            if hr_dev > HR_SANITY_TOLERANCE_BPM:
                meta = a["meta"]
                a.clear()
                a.update(
                    {
                        "id": meta["id"],
                        "meta": meta,
                        "available": False,
                        "error": (
                            f"심박수 추정 실패 — {int(round(hr_dev))} BPM 벗어남 "
                            f"(기준 {int(round(reference_hr))} BPM)"
                        ),
                        "compute_ms": 0,
                    }
                )

    median_hr = (
        float(np.median([a["hrv"].hr_bpm for a in per_algo if a.get("available") and a["hrv"].hr_bpm > 0]))
        if any(a.get("available") for a in per_algo)
        else 0.0
    )

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
