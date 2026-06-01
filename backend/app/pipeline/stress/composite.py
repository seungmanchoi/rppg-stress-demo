"""Composite stress score (0~100) from HRV indices.

v1 (classic, ESC/NASPE 1996 + Russian Baevsky):
    score = 100 * (0.4·Baev + 0.4·LF/HF + 0.2·RMSSD)

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
from dataclasses import dataclass, field
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


@dataclass
class StressComponent:
    name: str
    label: str
    weight: float            # 0~1
    raw_value: float
    raw_unit: str
    normalized: float        # 0~1 contribution before weighting
    contribution: float      # weighted points contributed to score (0~100·weight)
    tier: str                # clinical / commercial / research / experimental


@dataclass
class CompositeBreakdown:
    score: float
    level: Level
    components: list[StressComponent] = field(default_factory=list)


def _clip(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def composite_level(score: float) -> Level:
    if score < 30:
        return "low"
    if score < 60:
        return "mid"
    if score < 80:
        return "high"
    return "very_high"


def composite_stress_breakdown(
    baevsky_si: float,
    lf_hf: float,
    rmssd: float,
) -> CompositeBreakdown:
    """Return v1 composite (3 components: Baevsky 40% + LF/HF 40% + RMSSD 20%)."""
    s_baev = _clip(
        math.log10(max(baevsky_si, BAEVSKY_FLOOR) / BAEVSKY_FLOOR)
        / math.log10(BAEVSKY_CEIL / BAEVSKY_FLOOR)
    )
    s_lfhf = _clip((lf_hf - LF_HF_RELAXED) / (LF_HF_STRESSED - LF_HF_RELAXED))
    s_rmssd = _clip(
        (RMSSD_RELAXED_MS - rmssd) / (RMSSD_RELAXED_MS - RMSSD_HIGH_STRESS_MS)
    )
    score = 100 * (0.4 * s_baev + 0.4 * s_lfhf + 0.2 * s_rmssd)
    score = max(MIN_SCORE_WITH_VALID_HRV, score)
    components = [
        StressComponent(
            name="baevsky_si",
            label="Baevsky SI",
            weight=0.40,
            raw_value=baevsky_si,
            raw_unit="점수",
            normalized=s_baev,
            contribution=100 * 0.40 * s_baev,
            tier="clinical",
        ),
        StressComponent(
            name="lf_hf",
            label="LF/HF",
            weight=0.40,
            raw_value=lf_hf,
            raw_unit="비율",
            normalized=s_lfhf,
            contribution=100 * 0.40 * s_lfhf,
            tier="clinical",
        ),
        StressComponent(
            name="rmssd",
            label="RMSSD",
            weight=0.20,
            raw_value=rmssd,
            raw_unit="ms",
            normalized=s_rmssd,
            contribution=100 * 0.20 * s_rmssd,
            tier="clinical",
        ),
    ]
    return CompositeBreakdown(score=score, level=composite_level(score), components=components)


def composite_stress(baevsky_si: float, lf_hf: float, rmssd: float) -> float:
    """Return composite stress score in [3, 100] when HRV is valid. (back-compat)"""
    return composite_stress_breakdown(baevsky_si, lf_hf, rmssd).score
