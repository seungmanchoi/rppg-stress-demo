"""Composite stress score (0~100) from HRV indices.

Thresholds tuned so that:
- A relaxed but realistic HRV profile (RMSSD ~70, LF/HF ~0.6, Baevsky ~80) → ~10
- A balanced day-to-day profile                  → ~30~50
- High-stress profile (RMSSD ~15, LF/HF ~4, Baevsky ~900) → ~80

We never want a value to be exactly 0 from valid HRV input; callers should
mark an algorithm as `available=False` if HRV could not be computed, instead
of feeding zero into this function.
"""
from __future__ import annotations

import math
from typing import Literal

Level = Literal["low", "mid", "high", "very_high"]

# Tuneable thresholds — see docstring above.
RMSSD_HIGH_STRESS_MS = 15.0   # very tense ⇒ s_rmssd → 1
RMSSD_RELAXED_MS = 100.0      # very relaxed ⇒ s_rmssd → 0
LF_HF_RELAXED = 0.7           # parasympathetic dominance lower bound
LF_HF_STRESSED = 4.0          # strong sympathetic dominance
BAEVSKY_FLOOR = 40.0          # below this is treated as "very relaxed"
BAEVSKY_CEIL = 1500.0
MIN_SCORE_WITH_VALID_HRV = 3.0  # never report 0 when HRV was computed


def _clip(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def composite_stress(baevsky_si: float, lf_hf: float, rmssd: float) -> float:
    """Return composite stress score in [3, 100] when HRV is valid."""
    # Baevsky: log-scaled between floor and ceiling
    s_baev = _clip(
        math.log10(max(baevsky_si, BAEVSKY_FLOOR) / BAEVSKY_FLOOR)
        / math.log10(BAEVSKY_CEIL / BAEVSKY_FLOOR)
    )
    # LF/HF: smooth ramp from relaxed → stressed
    s_lfhf = _clip((lf_hf - LF_HF_RELAXED) / (LF_HF_STRESSED - LF_HF_RELAXED))
    # RMSSD: lower = more stress
    s_rmssd = _clip(
        (RMSSD_RELAXED_MS - rmssd) / (RMSSD_RELAXED_MS - RMSSD_HIGH_STRESS_MS)
    )
    score = 100 * (0.4 * s_baev + 0.4 * s_lfhf + 0.2 * s_rmssd)
    # Floor for valid HRV — a calmly measured signal should not show 0 / 100 etiquette
    return max(MIN_SCORE_WITH_VALID_HRV, score)


def composite_level(score: float) -> Level:
    if score < 30:
        return "low"
    if score < 60:
        return "mid"
    if score < 80:
        return "high"
    return "very_high"
