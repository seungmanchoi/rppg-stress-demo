from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from sse_starlette.sse import EventSourceResponse

from app.core.config import settings
from app.core.events import bus
from app.core.jobs import store
from app.models.registry import all_ids, get_meta
from app.pipeline.consensus import build_consensus
from app.pipeline.orchestrator import run_pipeline
from app.schemas.measurement import (
    AlgorithmMetaOut,
    AlgorithmResult,
    CompositeBreakdown,
    ConsensusResult,
    HemodynamicMetrics,
    HRVMetrics,
    MeasurementResponse,
    Reliability,
    ReliabilityComponents,
    RespirationMetrics,
    SignalQuality,
    StressComponent,
    StressIndices,
    VideoMeta,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/measurements", tags=["measurements"])


def _downsample(arr, n: int = 150) -> list[float]:
    import numpy as np

    if arr is None or len(arr) == 0:
        return []
    if len(arr) <= n:
        return arr.astype(float).tolist()
    idx = np.linspace(0, len(arr) - 1, n).astype(int)
    return arr[idx].astype(float).tolist()


def _algorithm_results(per_algo: list[dict], quality, median_hr: float) -> list[AlgorithmResult]:
    out: list[AlgorithmResult] = []
    for a in per_algo:
        meta = AlgorithmMetaOut(**a["meta"])
        if not a["available"]:
            out.append(
                AlgorithmResult(
                    meta=meta,
                    available=False,
                    error=a.get("error"),
                    compute_ms=a.get("compute_ms", 0),
                )
            )
            continue
        hrv = HRVMetrics(
            hr_bpm=a["hrv"].hr_bpm,
            ibi_mean_ms=a["hrv"].ibi_mean_ms,
            sdnn_ms=a["hrv"].sdnn_ms,
            rmssd_ms=a["hrv"].rmssd_ms,
            sdsd_ms=a["hrv"].sdsd_ms,
            pnn50_pct=a["hrv"].pnn50_pct,
            pnn20_pct=a["hrv"].pnn20_pct,
            cvnn_pct=a["hrv"].cvnn_pct,
            hrv_triangular_index=a["hrv"].hrv_triangular_index,
            vlf_power=a["freq"].vlf_power,
            lf_power=a["freq"].lf_power,
            hf_power=a["freq"].hf_power,
            total_power=a["freq"].total_power,
            lf_hf_ratio=a["freq"].lf_hf_ratio,
            lf_nu=a["freq"].lf_nu,
            hf_nu=a["freq"].hf_nu,
            sd1=a["poincare"].sd1,
            sd2=a["poincare"].sd2,
            sd_ratio=a["poincare"].sd_ratio,
            ellipse_area=a["poincare"].ellipse_area,
            sample_entropy=a["nonlinear"].sample_entropy,
            approximate_entropy=a["nonlinear"].approximate_entropy,
            shannon_entropy=a["nonlinear"].shannon_entropy,
            dfa_alpha1=a["nonlinear"].dfa_alpha1,
            higuchi_fd=a["nonlinear"].higuchi_fd,
        )
        v1 = a["composite_v1"]
        v2 = a["composite_v2"]
        v3 = a["composite_v3"]
        v4 = a["composite_v4"]

        def _to_breakdown(b) -> CompositeBreakdown:
            return CompositeBreakdown(
                score=b.score,
                level=b.level,
                components=[
                    StressComponent(
                        name=c.name,
                        label=c.label,
                        weight=c.weight,
                        raw_value=c.raw_value,
                        raw_unit=c.raw_unit,
                        normalized=c.normalized,
                        contribution=c.contribution,
                        tier=c.tier,
                    )
                    for c in b.components
                ],
            )

        stress = StressIndices(
            baevsky_si=a["baevsky"].si,
            baevsky_level=a["baevsky"].level,
            baevsky_mo_s=a["baevsky"].mo_s,
            baevsky_amo_pct=a["baevsky"].amo_pct,
            baevsky_mxdmn_s=a["baevsky"].mxdmn_s,
            composite_score=v1.score,
            composite_level=v1.level,
            composite_v1=_to_breakdown(v1),
            composite_score_v2=v2.score,
            composite_level_v2=v2.level,
            composite_v2=_to_breakdown(v2),
            composite_score_v3=v3.score,
            composite_level_v3=v3.level,
            composite_v3=_to_breakdown(v3),
            composite_score_v4=v4.score,
            composite_level_v4=v4.level,
            composite_v4=_to_breakdown(v4),
            pns_index=a["kubios"].pns_index,
            sns_index=a["kubios"].sns_index,
            coherence_score=a["coherence"].score,
            coherence_peak_hz=a["coherence"].peak_freq_hz,
        )
        rel = Reliability(
            score=a["reliability"],
            grade=a["reliability_grade"],
            components=ReliabilityComponents(
                snr_db=a["snr_db"],
                face_tracking_pct=quality.detected_ratio * 100,
                deviation_from_consensus=(
                    a["hrv"].hr_bpm - median_hr if median_hr else 0
                ),
                motion_penalty=quality.mean_motion_px,
            ),
        )
        respiration = RespirationMetrics(
            rate_rpm=a["respiration"].rate_rpm,
            confidence=a["respiration"].confidence,
        )
        hemodynamic = HemodynamicMetrics(
            spo2_pct=a["spo2"].spo2_pct,
            spo2_confidence=a["spo2"].confidence,
            pulse_rise_time_ms=a["bvp_quality"].pulse_rise_time_ms,
        )
        signal_quality = SignalQuality(
            pqi=a["bvp_quality"].pqi,
            spectral_entropy=a["bvp_quality"].spectral_entropy,
        )
        out.append(
            AlgorithmResult(
                meta=meta,
                available=True,
                hrv=hrv,
                stress=stress,
                reliability=rel,
                respiration=respiration,
                hemodynamic=hemodynamic,
                signal_quality=signal_quality,
                beat_count=int(len(a["ibi"])) if "ibi" in a else None,
                bvp_sparkline=_downsample(a["bvp"]),
                compute_ms=a.get("compute_ms", 0),
            )
        )
    return out


def _consensus(per_algo: list[dict]) -> ConsensusResult | None:
    c = build_consensus(per_algo)
    if not c:
        return None
    return ConsensusResult(
        stress_score=c["stress_score"],
        stress_level=c["stress_level"],
        stress_score_v2=c.get("stress_score_v2", 0.0),
        stress_level_v2=c.get("stress_level_v2", "low"),
        stress_score_v3=c.get("stress_score_v3", 0.0),
        stress_level_v3=c.get("stress_level_v3", "low"),
        stress_score_v4=c.get("stress_score_v4", 0.0),
        stress_level_v4=c.get("stress_level_v4", "low"),
        hr_bpm=c["hr_bpm"],
        rmssd_ms=c["rmssd_ms"],
        sdnn_ms=c.get("sdnn_ms", 0.0),
        pnn50_pct=c.get("pnn50_pct", 0.0),
        lf_hf_ratio=c["lf_hf_ratio"],
        hf_nu=c.get("hf_nu", 0.0),
        baevsky_si=c["baevsky_si"],
        sd2_sd1=c.get("sd2_sd1", 0.0),
        sample_entropy=c.get("sample_entropy", 0.0),
        dfa_alpha1=c.get("dfa_alpha1", 0.0),
        higuchi_fd=c.get("higuchi_fd", 0.0),
        sns_index=c.get("sns_index", 0.0),
        pns_index=c.get("pns_index", 0.0),
        coherence_score=c.get("coherence_score", 0.0),
        respiration_rpm=c.get("respiration_rpm", 0.0),
        reliability=Reliability(
            score=c["reliability"]["score"],
            grade=c["reliability"]["grade"],
            components=ReliabilityComponents(
                snr_db=0, face_tracking_pct=0, deviation_from_consensus=0, motion_penalty=0
            ),
        ),
        contributing_algorithms=c["contributing_algorithms"],
    )


async def _process(job_id: str, path: Path, algorithm_ids: list[str]) -> None:
    await store.update(job_id, status="processing", progress=0.05, stage="decoding")

    async def progress(p: float, stage: str) -> None:
        await store.update(job_id, progress=p, stage=stage)
        await bus.publish(job_id, {"event": "progress", "progress": p, "stage": stage})

    try:
        out = await run_pipeline(path, algorithm_ids, progress)
        algo_results = _algorithm_results(out["per_algo"], out["quality"], out["median_hr"])
        consensus = _consensus(out["per_algo"])
        await store.update(
            job_id,
            status="done",
            progress=1.0,
            stage="done",
            warnings=out["quality"].warnings,
            result={
                "video_meta": out["video_meta"],
                "timing": out.get("timing"),
                "algorithms": [r.model_dump(by_alias=True) for r in algo_results],
                "consensus": consensus.model_dump(by_alias=True) if consensus else None,
            },
        )
        await bus.publish(job_id, {"event": "done"})
    except Exception as e:  # noqa: BLE001
        log.exception("pipeline failed")
        await store.update(job_id, status="failed", error=str(e))
        await bus.publish(job_id, {"event": "failed", "error": str(e)})
    finally:
        try:
            if settings.keep_captures:
                # Preserve the clip for offline inspection / re-analysis.
                import shutil

                dest = settings.captures_dir / path.name
                shutil.move(str(path), str(dest))
            else:
                path.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass


@router.post("", status_code=202)
async def create_measurement(
    bg: BackgroundTasks,
    video: UploadFile = File(...),
    algorithms: str | None = None,
) -> dict:
    if not video.filename:
        raise HTTPException(400, "video file required")
    data = await video.read()
    if len(data) > settings.max_video_mb * 1024 * 1024:
        raise HTTPException(413, f"video larger than {settings.max_video_mb}MB")
    job = await store.create()
    safe_name = video.filename.replace("/", "_")
    target = settings.tmp_dir / f"{job.id}_{safe_name}"
    target.write_bytes(data)
    ids = (
        [a.strip() for a in algorithms.split(",") if a.strip()]
        if algorithms
        else all_ids()
    )
    unknown = [a for a in ids if a not in set(all_ids())]
    if unknown:
        raise HTTPException(400, f"unknown algorithms: {unknown}")
    bg.add_task(_process, job.id, target, ids)
    return {"jobId": job.id, "status": "queued"}


@router.get(
    "/{job_id}",
    response_model=MeasurementResponse,
    response_model_by_alias=True,
)
async def get_measurement(job_id: str) -> MeasurementResponse:
    j = store.get(job_id)
    if not j:
        raise HTTPException(404, "job not found")
    payload: dict = {
        "job_id": j.id,
        "status": j.status,
        "progress": j.progress,
        "stage": j.stage,
        "warnings": j.warnings,
        "error": j.error,
    }
    if j.result:
        payload["video_meta"] = j.result["video_meta"]
        payload["timing"] = j.result.get("timing")
        payload["algorithms"] = j.result["algorithms"]
        payload["consensus"] = j.result["consensus"]
    return MeasurementResponse.model_validate(payload)


@router.get("/{job_id}/stream")
async def stream_measurement(job_id: str):
    if not store.get(job_id):
        raise HTTPException(404)
    queue = bus.subscribe(job_id)

    async def gen():
        try:
            while True:
                ev = await queue.get()
                yield {"event": ev.get("event", "message"), "data": json.dumps(ev)}
                if ev.get("event") in {"done", "failed"}:
                    break
        finally:
            bus.unsubscribe(job_id, queue)

    return EventSourceResponse(gen())


@router.delete("/{job_id}", status_code=204)
async def delete_measurement(job_id: str) -> None:
    await store.delete(job_id)
