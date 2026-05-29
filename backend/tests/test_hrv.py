import numpy as np

from app.pipeline.hrv.freq_domain import freq_domain_hrv
from app.pipeline.hrv.nonlinear import poincare
from app.pipeline.hrv.peak_detect import bvp_to_ibi
from app.pipeline.hrv.time_domain import time_domain_hrv


def test_peak_detect_synthetic_60bpm():
    fs = 30
    t = np.arange(0, 30, 1 / fs)
    bvp = np.sin(2 * np.pi * 1.0 * t)
    ibi_ms = bvp_to_ibi(bvp, fs=fs)
    assert 950 < np.mean(ibi_ms) < 1050
    assert len(ibi_ms) >= 25


def test_peak_detect_short_signal_returns_empty():
    assert len(bvp_to_ibi(np.zeros(10), fs=30)) == 0


def test_time_domain_known_series():
    ibi_ms = np.array([900.0, 920, 880, 910, 905, 895, 915, 890])
    m = time_domain_hrv(ibi_ms)
    assert abs(m.sdnn_ms - float(np.std(ibi_ms))) < 0.5
    assert m.rmssd_ms > 0
    assert 0 <= m.pnn50_pct <= 100
    expected_hr = 60_000 / float(np.mean(ibi_ms))
    assert abs(m.hr_bpm - expected_hr) < 0.1


def test_freq_domain_hf_dominant():
    n = 240
    base = np.full(n, 1000.0) + 30 * np.sin(2 * np.pi * 0.25 * np.arange(n))
    ibi = base
    m = freq_domain_hrv(ibi)
    assert m.hf_power > m.lf_power
    assert m.lf_hf_ratio < 1.0


def test_poincare_basic():
    rng = np.random.default_rng(42)
    ibi = 900 + rng.normal(0, 25, 200)
    p = poincare(ibi)
    assert p.sd1 > 0
    assert p.sd2 > 0
