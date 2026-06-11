"""End-to-end wiring: a real adapter's BVP through the full v1–v4 path.

Mirrors the orchestrator's per-algorithm transform on a synthetic pulsatile
RGB signal (no video file / face detection needed), confirming every stage
chains correctly and recovers a sane heart rate and four stress scores.
"""
import cv2
import numpy as np

from app.pipeline.algorithms.unsupervised.green import GreenAdapter
from app.pipeline.orchestrator import run_pipeline
from app.pipeline.hrv.freq_domain import freq_domain_hrv
from app.pipeline.hrv.nonlinear import nonlinear_hrv, poincare
from app.pipeline.hrv.peak_detect import bvp_to_ibi
from app.pipeline.hrv.time_domain import time_domain_hrv
from app.pipeline.preprocess.resample import resample_uniform
from app.pipeline.reliability.snr import bvp_snr_db
from app.pipeline.stress.adaptive import metric_confidences
from app.pipeline.stress.baevsky import baevsky_si
from app.pipeline.stress.coherence import cardiac_coherence
from app.pipeline.stress.composite import composite_stress_breakdown
from app.pipeline.stress.composite_v2 import composite_stress_v2
from app.pipeline.stress.composite_v3 import composite_stress_v3
from app.pipeline.stress.composite_v4 import composite_stress_v4
from app.pipeline.stress.kubios import kubios_indices


def _pulsatile_rgb(duration_s=40.0, fs=30.0, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(0, duration_s, 1.0 / fs)
    # ~66 BPM carrier with respiratory-sinus-arrhythmia frequency wobble
    inst_hr_hz = 1.1 + 0.05 * np.sin(2 * np.pi * 0.25 * t)
    phase = 2 * np.pi * np.cumsum(inst_hr_hz) / fs
    pulse = np.sin(phase)
    rgb = np.empty((len(t), 3))
    rgb[:, 0] = 120.0 + 0.5 * pulse + rng.normal(0, 0.2, len(t))
    rgb[:, 1] = 128.0 + 3.0 * pulse + rng.normal(0, 0.2, len(t))  # green carries pulse
    rgb[:, 2] = 110.0 + 0.3 * pulse + rng.normal(0, 0.2, len(t))
    return rgb, fs, duration_s


def test_green_adapter_through_v1_to_v4():
    rgb, fs, duration = _pulsatile_rgb()
    bvp = GreenAdapter().estimate_bvp(rgb, None, fs)

    # orchestrator resamples the frame-indexed BVP onto a uniform ×4 grid
    ts_ms = np.arange(len(bvp)) / fs * 1000.0
    bvp_u, fs_u = resample_uniform(bvp, ts_ms, fs, oversample=4)
    ibi = bvp_to_ibi(bvp_u, fs_u)
    assert len(ibi) >= 16

    td = time_domain_hrv(ibi)
    fd = freq_domain_hrv(ibi)
    pc = poincare(ibi)
    nl = nonlinear_hrv(ibi)
    bv = baevsky_si(ibi)
    snr = bvp_snr_db(bvp_u, fs_u)
    coh = cardiac_coherence(ibi)
    kub = kubios_indices(td.ibi_mean_ms, td.rmssd_ms, fd.hf_nu, td.hr_bpm, bv.si, fd.lf_nu)
    conf = metric_confidences(beat_count=len(ibi), duration_s=duration, snr_db=snr)

    # HR recovered near the 66 BPM carrier
    assert 55 <= td.hr_bpm <= 78

    v1 = composite_stress_breakdown(bv.si, fd.lf_hf_ratio, td.rmssd_ms, confidences=conf)
    v2 = composite_stress_v2(
        baevsky_si=bv.si, lf_hf=fd.lf_hf_ratio, rmssd_ms=td.rmssd_ms,
        sns_index=kub.sns_index, pns_index=kub.pns_index,
        sample_entropy=nl.sample_entropy, dfa_alpha1=nl.dfa_alpha1,
        coherence=coh.score, respiration_rpm=15.0, confidences=conf,
    )
    v3 = composite_stress_v3(
        baevsky_si=bv.si, lf_hf=fd.lf_hf_ratio, rmssd_ms=td.rmssd_ms,
        sdnn_ms=td.sdnn_ms, pnn50_pct=td.pnn50_pct, sd2_sd1=pc.sd_ratio,
        sample_entropy=nl.sample_entropy, dfa_alpha1=nl.dfa_alpha1,
        higuchi_fd=nl.higuchi_fd, sns_index=kub.sns_index,
        pns_index=kub.pns_index, coherence=coh.score, confidences=conf,
    )
    v4 = composite_stress_v4(
        baevsky_si=bv.si, lf_hf=fd.lf_hf_ratio, rmssd_ms=td.rmssd_ms,
        pnn50_pct=td.pnn50_pct, sd2_sd1=pc.sd_ratio, hf_nu=fd.hf_nu,
        sample_entropy=nl.sample_entropy, coherence=coh.score,
        snr_db=snr, beat_count=len(ibi), confidences=conf,
    )
    for v in (v1, v2, v3, v4):
        assert 3.0 <= v.score <= 100.0
        assert v.level in {"low", "mid", "high", "very_high"}
        assert len(v.components) >= 3


async def test_run_pipeline_smoke_no_face(tmp_path):
    """Full orchestrator on a faceless noise clip: must finish without crashing.

    Guards the decode 4-tuple unpacking and the resample NaN-sanitization path
    (POS emits 0/0 → NaN BVP when RGB is degenerate). No face → all dropped.
    """
    path = tmp_path / "synth.mp4"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 30.0, (160, 120))
    rng = np.random.default_rng(0)
    for _ in range(120):
        writer.write(rng.integers(0, 255, (120, 160, 3), dtype=np.uint8))
    writer.release()

    out = await run_pipeline(path, ["GREEN", "POS"], None)
    assert {"per_algo", "video_meta", "timing", "median_hr", "quality"} <= set(out)
    assert all(not a["available"] for a in out["per_algo"])
