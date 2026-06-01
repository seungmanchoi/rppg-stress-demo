"""Composite stress score v2 — autonomic balance ensemble.

Goal: capture the *full* HRV picture by combining classical ESC/NASPE indices
with Kubios autonomic indices, HeartMath coherence, non-linear complexity,
and respiratory regularity. Reduces single-metric bias of the v1 score.

Weights (sum = 1.00):
  Classical (sum 0.45)
    - Baevsky SI         0.15  [clinical]    autonomic rigidity
    - LF/HF              0.15  [clinical]    sympathovagal balance
    - RMSSD (inv)        0.15  [clinical]    parasympathetic vagal tone
  Kubios autonomic (sum 0.20)
    - SNS Index          0.12  [commercial]  sympathetic activity (+ stress)
    - PNS Index (inv)    0.08  [commercial]  parasympathetic activity (- stress)
  Non-linear complexity (sum 0.15)
    - Sample Entropy dev 0.08  [research]    complexity drift from healthy ~1.5
    - DFA α1 dev         0.07  [research]    short-term scaling drift from ~1.0
  Coherence + respiration (sum 0.20)
    - Coherence (inv)    0.12  [commercial]  high coherence → low stress
    - Respiration dev    0.08  [commercial]  fast/erratic breathing → ↑

Each component is normalized to [0, 1] before weighting. Final score = 100·Σ.
"""
from __future__ import annotations

from app.pipeline.stress.composite import (
    BAEVSKY_CEIL,
    BAEVSKY_FLOOR,
    LF_HF_RELAXED,
    LF_HF_STRESSED,
    MIN_SCORE_WITH_VALID_HRV,
    RMSSD_HIGH_STRESS_MS,
    RMSSD_RELAXED_MS,
    CompositeBreakdown,
    StressComponent,
    _clip,
    composite_level,
)

import math


# v2-specific normalization bounds
SAMPEN_HEALTHY = 1.5
SAMPEN_HALFWIDTH = 1.2
DFA_HEALTHY = 1.0
DFA_HALFWIDTH = 0.5
RESP_HEALTHY_RPM = 15.0
RESP_HALFWIDTH = 10.0


def _norm_baev(si: float) -> float:
    return _clip(
        math.log10(max(si, BAEVSKY_FLOOR) / BAEVSKY_FLOOR)
        / math.log10(BAEVSKY_CEIL / BAEVSKY_FLOOR)
    )


def _norm_lfhf(r: float) -> float:
    return _clip((r - LF_HF_RELAXED) / (LF_HF_STRESSED - LF_HF_RELAXED))


def _norm_rmssd_inv(ms: float) -> float:
    """RMSSD: high = relaxed. Stress contribution rises as RMSSD falls."""
    return _clip((RMSSD_RELAXED_MS - ms) / (RMSSD_RELAXED_MS - RMSSD_HIGH_STRESS_MS))


def _norm_sns(idx: float) -> float:
    """Kubios SNS in [-2, +2]. +2 = strong sympathetic = max stress."""
    return _clip((idx + 2.0) / 4.0)


def _norm_pns_inv(idx: float) -> float:
    """Kubios PNS in [-2, +2]. -2 = parasympathetic suppression = max stress."""
    return _clip((2.0 - idx) / 4.0)


def _norm_dev(value: float, healthy: float, halfwidth: float) -> float:
    """Penalize deviation from a healthy mid-point."""
    return _clip(abs(value - healthy) / halfwidth)


def _norm_coherence_inv(score: float) -> float:
    """HeartMath coherence 0~3. Higher = more relaxed."""
    return _clip((3.0 - score) / 3.0)


def composite_stress_v2(
    baevsky_si: float,
    lf_hf: float,
    rmssd_ms: float,
    sns_index: float,
    pns_index: float,
    sample_entropy: float,
    dfa_alpha1: float,
    coherence: float,
    respiration_rpm: float,
) -> CompositeBreakdown:
    s_baev = _norm_baev(baevsky_si)
    s_lfhf = _norm_lfhf(lf_hf)
    s_rmssd = _norm_rmssd_inv(rmssd_ms)
    s_sns = _norm_sns(sns_index)
    s_pns = _norm_pns_inv(pns_index)
    s_sampen = _norm_dev(sample_entropy, SAMPEN_HEALTHY, SAMPEN_HALFWIDTH)
    s_dfa = _norm_dev(dfa_alpha1, DFA_HEALTHY, DFA_HALFWIDTH)
    s_coh = _norm_coherence_inv(coherence)
    s_resp = _norm_dev(respiration_rpm, RESP_HEALTHY_RPM, RESP_HALFWIDTH)

    weights_norms = [
        ("baevsky_si",      "Baevsky SI",   0.15, baevsky_si,    "점수", s_baev,   "clinical"),
        ("lf_hf",           "LF/HF",        0.15, lf_hf,         "비율", s_lfhf,   "clinical"),
        ("rmssd",           "RMSSD (inv)",  0.15, rmssd_ms,      "ms",   s_rmssd,  "clinical"),
        ("sns_index",       "SNS Index",    0.12, sns_index,     "-2~2", s_sns,    "commercial"),
        ("pns_index_inv",   "PNS (inv)",    0.08, pns_index,     "-2~2", s_pns,    "commercial"),
        ("sample_entropy",  "SampEn dev",   0.08, sample_entropy,"-",    s_sampen, "research"),
        ("dfa_alpha1",      "DFA α1 dev",   0.07, dfa_alpha1,    "-",    s_dfa,    "research"),
        ("coherence_inv",   "Coherence inv",0.12, coherence,     "0~3",  s_coh,    "commercial"),
        ("respiration",     "Resp. dev",    0.08, respiration_rpm,"/min",s_resp,   "commercial"),
    ]
    score = 100.0 * sum(w * n for (_, _, w, _, _, n, _) in weights_norms)
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
        for (name, label, w, raw, unit, n, tier) in weights_norms
    ]
    return CompositeBreakdown(score=score, level=composite_level(score), components=components)
