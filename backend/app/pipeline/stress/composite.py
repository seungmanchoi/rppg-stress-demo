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

from app.pipeline.stress.adaptive import MetricConfidence, confidence_for

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


# A component row: (name, label, weight, raw_value, raw_unit, normalized, tier)
Row = tuple[str, str, float, float, str, float, str]


def assemble_score(
    rows: list[Row],
    confidences: MetricConfidence | None = None,
) -> tuple[float, list["StressComponent"]]:
    """Combine weighted, normalized components into a 0~100 score.

    When ``confidences`` is given, each component weight is scaled by its
    confidence and the surviving weights are renormalized — low-trust indices
    (e.g. LF/HF on a short clip) fade out and the score leans on what the
    measurement can actually support. With ``confidences=None`` this is a plain
    weighted sum identical to the original fixed-weight formula.
    """
    eff = [w * confidence_for(name, confidences) for (name, _, w, _, _, _, _) in rows]
    total = sum(eff)
    if total <= 1e-9:
        contributions = [0.0] * len(rows)
        raw_score = 0.0
    else:
        contributions = [100.0 * (e / total) * n for e, (_, _, _, _, _, n, _) in zip(eff, rows)]
        raw_score = sum(contributions)
    score = max(MIN_SCORE_WITH_VALID_HRV, raw_score)
    components = [
        StressComponent(
            name=name,
            label=label,
            weight=w,
            raw_value=raw,
            raw_unit=unit,
            normalized=n,
            contribution=contrib,
            tier=tier,
        )
        for (name, label, w, raw, unit, n, tier), contrib in zip(rows, contributions)
    ]
    return score, components


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
    confidences: MetricConfidence | None = None,
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
    rows: list[Row] = [
        ("baevsky_si", "Baevsky SI", 0.40, baevsky_si, "점수", s_baev, "clinical"),
        ("lf_hf", "LF/HF", 0.40, lf_hf, "비율", s_lfhf, "clinical"),
        ("rmssd", "RMSSD", 0.20, rmssd, "ms", s_rmssd, "clinical"),
    ]
    score, components = assemble_score(rows, confidences)
    return CompositeBreakdown(score=score, level=composite_level(score), components=components)


def composite_stress(
    baevsky_si: float,
    lf_hf: float,
    rmssd: float,
    confidences: MetricConfidence | None = None,
) -> float:
    """Return composite stress score in [3, 100] when HRV is valid. (back-compat)"""
    return composite_stress_breakdown(baevsky_si, lf_hf, rmssd, confidences).score
