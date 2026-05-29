import numpy as np

from app.pipeline.stress.baevsky import baevsky_si
from app.pipeline.stress.composite import composite_level, composite_stress


def test_baevsky_low_for_relaxed():
    ibi_ms = 900 + 30 * np.sin(np.linspace(0, 6 * np.pi, 200))
    out = baevsky_si(ibi_ms)
    assert 30 < out.si < 800
    assert out.level in {"normal", "mild", "moderate"}


def test_baevsky_high_for_rigid():
    rng = np.random.default_rng(0)
    ibi_ms = np.full(200, 700.0) + rng.normal(0, 1, 200)
    out = baevsky_si(ibi_ms)
    assert out.si > 500
    assert out.level in {"moderate", "high"}


def test_composite_in_range():
    score = composite_stress(baevsky_si=300, lf_hf=2.0, rmssd=30)
    assert 0 <= score <= 100
    assert composite_level(score) in {"low", "mid", "high", "very_high"}


def test_composite_high_input():
    score = composite_stress(baevsky_si=1200, lf_hf=4.0, rmssd=10)
    assert score > 60


def test_composite_low_input():
    score = composite_stress(baevsky_si=80, lf_hf=0.8, rmssd=55)
    assert score < 30
