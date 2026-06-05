"""Composite stress score v3 — full HRV panel ensemble (12 metrics).

Extends v2 by adding 6 more standard HRV indices (SDNN, pNN50, SD2/SD1,
Higuchi FD) so the score reflects the *whole* panel shown on each card,
not just the autonomic-balance subset. The widest, most redundant of the
three formulas — single-metric noise is heavily averaged out.

Weights (sum = 1.00):
  Clinical — time + geometry (sum 0.58)
    - Baevsky SI      0.12  [clinical]    autonomic rigidity
    - LF/HF           0.12  [clinical]    sympathovagal balance
    - RMSSD (inv)     0.10  [clinical]    parasympathetic vagal tone
    - SDNN (inv)      0.08  [clinical]    overall HRV magnitude
    - pNN50 (inv)     0.08  [clinical]    short-term parasympathetic
    - SD2/SD1         0.08  [clinical]    Poincaré sympathovagal ratio
  Non-linear complexity (sum 0.17)
    - SampEn dev      0.06  [research]    complexity drift from healthy ~1.5
    - DFA α1 dev      0.06  [research]    short-term scaling drift from ~1.0
    - Higuchi (inv)   0.05  [research]    fractal complexity loss under stress
  Commercial autonomic (sum 0.25)
    - SNS Index       0.10  [commercial]  sympathetic activity (+ stress)
    - PNS (inv)       0.08  [commercial]  parasympathetic activity (- stress)
    - Coherence (inv) 0.07  [commercial]  high coherence → low stress

Each component is normalized to [0, 1] before weighting. Final score = 100·Σ.
"""
from __future__ import annotations

from app.pipeline.stress.composite import (
    MIN_SCORE_WITH_VALID_HRV,
    CompositeBreakdown,
    StressComponent,
    _clip,
    composite_level,
)
from app.pipeline.stress.composite_v2 import (
    DFA_HALFWIDTH,
    DFA_HEALTHY,
    SAMPEN_HALFWIDTH,
    SAMPEN_HEALTHY,
    _norm_baev,
    _norm_coherence_inv,
    _norm_dev,
    _norm_lfhf,
    _norm_pns_inv,
    _norm_rmssd_inv,
    _norm_sns,
)

# v3-specific normalization bounds
SDNN_RELAXED_MS = 120.0
SDNN_STRESSED_MS = 20.0
PNN50_RELAXED_PCT = 30.0
SD2SD1_RELAXED = 1.0
SD2SD1_STRESSED = 4.0
HIGUCHI_HEALTHY = 1.9
HIGUCHI_HALFWIDTH = 0.6


def _norm_sdnn_inv(ms: float) -> float:
    """SDNN: high = healthy variability. Stress rises as it falls."""
    return _clip((SDNN_RELAXED_MS - ms) / (SDNN_RELAXED_MS - SDNN_STRESSED_MS))


def _norm_pnn50_inv(pct: float) -> float:
    """pNN50: high = parasympathetic activity. Stress rises as it falls."""
    return _clip((PNN50_RELAXED_PCT - pct) / PNN50_RELAXED_PCT)


def _norm_sd2sd1(ratio: float) -> float:
    """Poincaré SD2/SD1: higher = sympathetic dominance = more stress."""
    return _clip((ratio - SD2SD1_RELAXED) / (SD2SD1_STRESSED - SD2SD1_RELAXED))


def _norm_higuchi_inv(fd: float) -> float:
    """Higuchi fractal dimension: complexity drops under stress → lower FD = more stress."""
    return _clip((HIGUCHI_HEALTHY - fd) / HIGUCHI_HALFWIDTH)


def composite_stress_v3(
    baevsky_si: float,
    lf_hf: float,
    rmssd_ms: float,
    sdnn_ms: float,
    pnn50_pct: float,
    sd2_sd1: float,
    sample_entropy: float,
    dfa_alpha1: float,
    higuchi_fd: float,
    sns_index: float,
    pns_index: float,
    coherence: float,
) -> CompositeBreakdown:
    rows = [
        ("baevsky_si",     "Baevsky SI",    0.12, baevsky_si,     "점수", _norm_baev(baevsky_si),                                      "clinical"),
        ("lf_hf",          "LF/HF",         0.12, lf_hf,          "비율", _norm_lfhf(lf_hf),                                           "clinical"),
        ("rmssd",          "RMSSD (inv)",   0.10, rmssd_ms,       "ms",   _norm_rmssd_inv(rmssd_ms),                                   "clinical"),
        ("sdnn",           "SDNN (inv)",    0.08, sdnn_ms,        "ms",   _norm_sdnn_inv(sdnn_ms),                                     "clinical"),
        ("pnn50",          "pNN50 (inv)",   0.08, pnn50_pct,      "%",    _norm_pnn50_inv(pnn50_pct),                                  "clinical"),
        ("sd2_sd1",        "SD2/SD1",       0.08, sd2_sd1,        "비율", _norm_sd2sd1(sd2_sd1),                                       "clinical"),
        ("sample_entropy", "SampEn dev",    0.06, sample_entropy, "-",    _norm_dev(sample_entropy, SAMPEN_HEALTHY, SAMPEN_HALFWIDTH), "research"),
        ("dfa_alpha1",     "DFA α1 dev",    0.06, dfa_alpha1,     "-",    _norm_dev(dfa_alpha1, DFA_HEALTHY, DFA_HALFWIDTH),           "research"),
        ("higuchi_fd",     "Higuchi (inv)", 0.05, higuchi_fd,     "-",    _norm_higuchi_inv(higuchi_fd),                               "research"),
        ("sns_index",      "SNS Index",     0.10, sns_index,      "-2~2", _norm_sns(sns_index),                                        "commercial"),
        ("pns_index_inv",  "PNS (inv)",     0.08, pns_index,      "-2~2", _norm_pns_inv(pns_index),                                    "commercial"),
        ("coherence_inv",  "Coherence inv", 0.07, coherence,      "0~3",  _norm_coherence_inv(coherence),                              "commercial"),
    ]
    score = 100.0 * sum(w * n for (_, _, w, _, _, n, _) in rows)
    score = max(MIN_SCORE_WITH_VALID_HRV, score)
    components = [
        StressComponent(
            name=name,
            label=label,
            weight=w,
            raw_value=raw,
            raw_unit=unit,
            normalized=n,
            contribution=100.0 * w * n,
            tier=tier,
        )
        for (name, label, w, raw, unit, n, tier) in rows
    ]
    return CompositeBreakdown(score=score, level=composite_level(score), components=components)
