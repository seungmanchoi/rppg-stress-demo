"""Reliability-weighted consensus across available algorithm results."""
from __future__ import annotations

import numpy as np


def _weighted_median(values: list[float], weights: list[float]) -> float:
    if not values:
        return 0.0
    pairs = sorted(zip(values, weights), key=lambda p: p[0])
    cum = 0.0
    half = sum(weights) / 2 if sum(weights) > 0 else 0
    for v, w in pairs:
        cum += w
        if cum >= half:
            return float(v)
    return float(pairs[-1][0])


def build_consensus(per_algo: list[dict]) -> dict | None:
    """Return None if no reliable algorithms produced output."""
    available = [a for a in per_algo if a.get("available")]
    if not available:
        return None
    weights = [max(a.get("reliability", 0) - 30, 0) for a in available]
    if sum(weights) <= 0:
        return None
    contributing = sum(1 for w in weights if w > 0)

    def wmed(get):
        vals = [float(get(a)) for a, w in zip(available, weights) if w > 0]
        ws = [w for w in weights if w > 0]
        return _weighted_median(vals, ws)

    score = wmed(lambda a: a["composite"])
    level = (
        "low" if score < 30
        else "mid" if score < 60
        else "high" if score < 80
        else "very_high"
    )

    rel_vals = [a["reliability"] for a, w in zip(available, weights) if w > 0]
    ws = [w for w in weights if w > 0]
    consensus_rel = float(np.average(rel_vals, weights=ws)) if rel_vals else 0.0
    rel_grade = "high" if consensus_rel >= 75 else "medium" if consensus_rel >= 45 else "low"

    return {
        "stress_score": score,
        "stress_level": level,
        "hr_bpm": wmed(lambda a: a["hrv"].hr_bpm),
        "rmssd_ms": wmed(lambda a: a["hrv"].rmssd_ms),
        "lf_hf_ratio": wmed(lambda a: a["freq"].lf_hf_ratio),
        "baevsky_si": wmed(lambda a: a["baevsky"].si),
        "reliability": {
            "score": consensus_rel,
            "grade": rel_grade,
            "components": {
                "snr_db": 0.0,
                "face_tracking_pct": 0.0,
                "deviation_from_consensus": 0.0,
                "motion_penalty": 0.0,
            },
        },
        "contributing_algorithms": contributing,
    }
