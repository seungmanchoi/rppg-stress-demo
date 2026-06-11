"""Composite stress score v4 — camera-adaptive robust score.

v1–v3 differ by how *many* HRV indices they pour into a fixed-weight formula.
That is the wrong axis to optimise for a real 30-second webcam measurement,
where the long-record indices (LF/HF, DFA, Higuchi) are the least trustworthy
and yet carry real weight. v4 is built the other way around:

1. Lead with the indices that converge fastest and survive camera noise —
   RMSSD, HF power, Baevsky SI, Poincaré geometry and cardiac coherence.
   LF/HF and Sample Entropy are kept only at low base weight.
2. Apply the same per-metric confidence attenuation as v1–v3 (see
   ``adaptive.metric_confidences``) so a term that the record cannot support
   fades out and the weight redistributes to what it can.
3. Apply an *absolute* trust shrink: when SNR is poor or too few beats were
   detected, pull the score toward a neutral baseline instead of emitting a
   confident extreme. A bad measurement should read "inconclusive ≈ normal",
   not "very high stress".

The result is the score to trust most when the input is a phone/webcam clip
rather than a clinical ECG strip.
"""
from __future__ import annotations

from app.pipeline.stress.adaptive import (
    MetricConfidence,
    _ramp,
    signal_quality_factor,
)
from app.pipeline.stress.composite import (
    MIN_SCORE_WITH_VALID_HRV,
    CompositeBreakdown,
    Row,
    assemble_score,
    composite_level,
    _clip,
)
from app.pipeline.stress.composite_v2 import (
    SAMPEN_HALFWIDTH,
    SAMPEN_HEALTHY,
    _norm_baev,
    _norm_coherence_inv,
    _norm_dev,
    _norm_lfhf,
    _norm_rmssd_inv,
)
from app.pipeline.stress.composite_v3 import (
    _norm_pnn50_inv,
    _norm_sd2sd1,
)

# HF in normalized units: high = parasympathetic (relaxed), low = stressed.
HFNU_RELAXED = 60.0
HFNU_STRESSED = 20.0

# Where a low-trust measurement is pulled toward (a mild, everyday baseline).
NEUTRAL_SCORE = 38.0


def _norm_hfnu_inv(hf_nu: float) -> float:
    return _clip((HFNU_RELAXED - hf_nu) / (HFNU_RELAXED - HFNU_STRESSED))


def composite_stress_v4(
    baevsky_si: float,
    lf_hf: float,
    rmssd_ms: float,
    pnn50_pct: float,
    sd2_sd1: float,
    hf_nu: float,
    sample_entropy: float,
    coherence: float,
    snr_db: float,
    beat_count: int,
    confidences: MetricConfidence | None = None,
) -> CompositeBreakdown:
    rows: list[Row] = [
        ("rmssd",          "RMSSD (inv)",   0.26, rmssd_ms,       "ms",   _norm_rmssd_inv(rmssd_ms),                                   "clinical"),
        ("baevsky_si",     "Baevsky SI",    0.18, baevsky_si,     "점수", _norm_baev(baevsky_si),                                      "clinical"),
        ("hf_nu",          "HF n.u. (inv)", 0.14, hf_nu,          "n.u.", _norm_hfnu_inv(hf_nu),                                       "clinical"),
        ("sd2_sd1",        "SD2/SD1",       0.12, sd2_sd1,        "비율", _norm_sd2sd1(sd2_sd1),                                       "clinical"),
        ("coherence_inv",  "Coherence inv", 0.10, coherence,      "0~3",  _norm_coherence_inv(coherence),                              "commercial"),
        ("pnn50",          "pNN50 (inv)",   0.08, pnn50_pct,      "%",    _norm_pnn50_inv(pnn50_pct),                                  "clinical"),
        ("sample_entropy", "SampEn dev",    0.06, sample_entropy, "-",    _norm_dev(sample_entropy, SAMPEN_HEALTHY, SAMPEN_HALFWIDTH), "research"),
        ("lf_hf",          "LF/HF",         0.06, lf_hf,          "비율", _norm_lfhf(lf_hf),                                           "clinical"),
    ]
    score, components = assemble_score(rows, confidences)

    # Absolute trust: shrink toward neutral when SNR is poor or beats are few.
    trust = signal_quality_factor(snr_db) * (0.5 + 0.5 * _ramp(beat_count, 16, 45))
    score = trust * score + (1.0 - trust) * NEUTRAL_SCORE
    score = max(MIN_SCORE_WITH_VALID_HRV, score)
    return CompositeBreakdown(score=score, level=composite_level(score), components=components)
