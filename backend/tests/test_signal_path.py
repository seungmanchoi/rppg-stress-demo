"""Timestamp-aware resampling + sub-sample peak timing.

The payoff of the resampling path is *reproducibility*: variable-frame-rate
capture must not inject phantom beat-to-beat variability into the IBI series.
These tests pin that — the resampled path's RMSSD is invariant to frame jitter,
whereas the naive average-fps path inflates with it.
"""
import numpy as np
from scipy.interpolate import CubicSpline

from app.pipeline.hrv.peak_detect import bvp_to_ibi
from app.pipeline.hrv.time_domain import time_domain_hrv
from app.pipeline.preprocess.resample import resample_uniform, timestamps_usable


def _synth_bvp(ibi_ms, fs, jitter, rng):
    """Synthesize a PPG-like wave from an IBI series sampled at a jittered fps."""
    beat_t = np.concatenate([[0.0], np.cumsum(ibi_ms) / 1000.0])
    duration = beat_t[-1]
    phase_spl = CubicSpline(beat_t, 2 * np.pi * np.arange(len(beat_t)))
    n = int(duration * fs)
    dt = (1.0 / fs) * (1.0 + jitter * rng.standard_normal(n))
    dt = np.clip(dt, 1e-3, None)
    t = np.cumsum(dt)
    t -= t[0]
    t = t[t <= duration]
    bvp = -np.cos(phase_spl(t)) + 0.3 * np.cos(2 * phase_spl(t))
    return bvp, t * 1000.0, len(t) / duration


def _rmssd(ibi):
    return float(np.sqrt(np.mean(np.diff(ibi) ** 2)))


def _ibi_fixture():
    rng = np.random.default_rng(0)
    return 800.0 + 22 * np.sin(2 * np.pi * 0.25 * np.arange(60)) + rng.normal(0, 16, 60)


def test_resampled_rmssd_invariant_to_frame_jitter():
    ibi_true = _ibi_fixture()
    rmssd_vals = []
    for jitter in (0.0, 0.25):
        bvp, ts_ms, fps = _synth_bvp(ibi_true, 30.0, jitter, np.random.default_rng(1))
        bvp_u, fs_u = resample_uniform(bvp, ts_ms, fps, oversample=4)
        rmssd_vals.append(time_domain_hrv(bvp_to_ibi(bvp_u, fs_u)).rmssd_ms)
    assert abs(rmssd_vals[0] - rmssd_vals[1]) < 3.0


def test_naive_average_fps_path_inflates_with_jitter():
    """Contrast: ignoring per-frame timing lets jitter masquerade as HRV."""
    ibi_true = _ibi_fixture()
    bvp_lo, _, fps_lo = _synth_bvp(ibi_true, 30.0, 0.0, np.random.default_rng(1))
    bvp_hi, _, fps_hi = _synth_bvp(ibi_true, 30.0, 0.25, np.random.default_rng(1))
    rmssd_lo = time_domain_hrv(bvp_to_ibi(bvp_lo, fps_lo)).rmssd_ms
    rmssd_hi = time_domain_hrv(bvp_to_ibi(bvp_hi, fps_hi)).rmssd_ms
    assert rmssd_hi - rmssd_lo > 5.0


def test_timestamps_usable_guards():
    assert timestamps_usable(np.arange(10) * 33.0, 10)
    assert not timestamps_usable(None, 10)
    assert not timestamps_usable(np.zeros(10), 10)          # all-zero ticks
    assert not timestamps_usable(np.arange(9) * 33.0, 10)   # length mismatch


def test_resample_falls_back_when_timestamps_bad():
    """Bad timestamps → uniform-grid fallback, still oversampled, never crashes."""
    rng = np.random.default_rng(3)
    bvp = np.sin(2 * np.pi * 1.2 * np.arange(300) / 30.0) + 0.1 * rng.standard_normal(300)
    out, new_fs = resample_uniform(bvp, np.zeros(300), 30.0, oversample=4)
    assert new_fs == 120.0
    assert len(out) > len(bvp)
