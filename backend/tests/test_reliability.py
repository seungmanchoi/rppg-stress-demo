import numpy as np

from app.pipeline.reliability.scoring import reliability_grade, reliability_score
from app.pipeline.reliability.snr import bvp_snr_db
from app.pipeline.reliability.tracking import tracking_score


def test_snr_clean_signal_beats_noisy():
    fs = 30
    t = np.arange(0, 30, 1 / fs)
    clean = np.sin(2 * np.pi * 1.2 * t)
    noisy = clean + np.random.default_rng(0).normal(0, 0.5, len(t))
    assert bvp_snr_db(clean, fs) > bvp_snr_db(noisy, fs)


def test_tracking_ratio():
    assert tracking_score(90, 100) == 0.9
    assert tracking_score(0, 0) == 0.0


def test_reliability_high_inputs():
    s = reliability_score(snr_db=10, tracking=0.95, motion_px=1, hr_dev=2)
    assert s > 75
    assert reliability_grade(s) == "high"


def test_reliability_low_inputs():
    s = reliability_score(snr_db=-3, tracking=0.5, motion_px=8, hr_dev=12)
    assert s < 45
    assert reliability_grade(s) == "low"


def test_reliability_medium_inputs():
    s = reliability_score(snr_db=3, tracking=0.75, motion_px=3, hr_dev=5)
    assert 45 <= s < 75
    assert reliability_grade(s) == "medium"
