"""Adaptive confidence weighting + the v4 camera-robust score."""
from app.pipeline.stress.adaptive import metric_confidences, signal_quality_factor
from app.pipeline.stress.composite import composite_stress, composite_stress_breakdown
from app.pipeline.stress.composite_v4 import NEUTRAL_SCORE, composite_stress_v4


def _v4(snr_db, beats, **inp):
    conf = metric_confidences(beat_count=beats, duration_s=float(beats), snr_db=snr_db)
    return composite_stress_v4(snr_db=snr_db, beat_count=beats, confidences=conf, **inp).score


STRESSED = dict(
    baevsky_si=1200, lf_hf=4.0, rmssd_ms=10, pnn50_pct=1.0,
    sd2_sd1=3.6, hf_nu=18, sample_entropy=0.8, coherence=0.2,
)
RELAXED = dict(
    baevsky_si=70, lf_hf=0.7, rmssd_ms=70, pnn50_pct=30.0,
    sd2_sd1=1.1, hf_nu=62, sample_entropy=1.5, coherence=2.4,
)


def test_signal_quality_factor_monotonic():
    assert signal_quality_factor(-10) < signal_quality_factor(0) < signal_quality_factor(10)
    assert 0.0 < signal_quality_factor(-10) <= signal_quality_factor(10) <= 1.0


def test_short_clip_trusts_short_term_over_lf_and_nonlinear():
    c = metric_confidences(beat_count=25, duration_s=30.0, snr_db=3.0)
    assert c.lf < c.short_time          # LF needs a long record
    assert c.nonlinear_strong < c.short_time  # DFA needs hundreds of beats


def test_confidence_grows_with_record_length():
    short = metric_confidences(25, 30.0, 3.0)
    long = metric_confidences(220, 240.0, 6.0)
    assert long.lf > short.lf
    assert long.nonlinear_strong > short.nonlinear_strong
    assert long.hf >= short.hf


def test_confidences_none_matches_fixed_weights():
    # The default path (no confidences) must equal the legacy fixed-weight score.
    legacy = composite_stress(baevsky_si=300, lf_hf=2.0, rmssd=30)
    explicit = composite_stress_breakdown(300, 2.0, 30, confidences=None).score
    assert abs(legacy - explicit) < 1e-9


def test_v4_in_range():
    s = _v4(6.0, 60, **STRESSED)
    assert 3.0 <= s <= 100.0


def test_v4_separates_stress_from_relaxation_when_trusted():
    assert _v4(8.0, 120, **STRESSED) > _v4(8.0, 120, **RELAXED)


def test_v4_low_trust_shrinks_toward_neutral():
    """A poor measurement should read inconclusive (~neutral), not a confident extreme."""
    stressed_hi = _v4(8.0, 120, **STRESSED)
    stressed_lo = _v4(-6.0, 18, **STRESSED)
    relaxed_hi = _v4(8.0, 120, **RELAXED)
    relaxed_lo = _v4(-6.0, 18, **RELAXED)
    # High-stress reading is pulled down, low-stress reading pulled up — both toward neutral.
    assert stressed_lo < stressed_hi
    assert relaxed_lo > relaxed_hi
    assert min(stressed_lo, relaxed_lo) <= NEUTRAL_SCORE + 12
    assert abs(stressed_lo - relaxed_lo) < abs(stressed_hi - relaxed_hi)
