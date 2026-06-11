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

    def _level(s: float) -> str:
        return (
            "low" if s < 30
            else "mid" if s < 60
            else "high" if s < 80
            else "very_high"
        )

    score_v1 = wmed(lambda a: a["composite_v1"].score)
    score_v2 = wmed(lambda a: a["composite_v2"].score)
    score_v3 = wmed(lambda a: a["composite_v3"].score)
    score_v4 = wmed(lambda a: a["composite_v4"].score)

    rel_vals = [a["reliability"] for a, w in zip(available, weights) if w > 0]
    ws = [w for w in weights if w > 0]
    consensus_rel = float(np.average(rel_vals, weights=ws)) if rel_vals else 0.0
    rel_grade = "high" if consensus_rel >= 75 else "medium" if consensus_rel >= 45 else "low"

    return {
        "stress_score": score_v1,
        "stress_level": _level(score_v1),
        "stress_score_v2": score_v2,
        "stress_level_v2": _level(score_v2),
        "stress_score_v3": score_v3,
        "stress_level_v3": _level(score_v3),
        "stress_score_v4": score_v4,
        "stress_level_v4": _level(score_v4),
        # Consensus value for every metric any version uses, so the dashboard
        # can show "the metrics this version actually uses" per v1/v2/v3/v4.
        "hr_bpm": wmed(lambda a: a["hrv"].hr_bpm),
        "rmssd_ms": wmed(lambda a: a["hrv"].rmssd_ms),
        "sdnn_ms": wmed(lambda a: a["hrv"].sdnn_ms),
        "pnn50_pct": wmed(lambda a: a["hrv"].pnn50_pct),
        "lf_hf_ratio": wmed(lambda a: a["freq"].lf_hf_ratio),
        "hf_nu": wmed(lambda a: a["freq"].hf_nu),
        "baevsky_si": wmed(lambda a: a["baevsky"].si),
        "sd2_sd1": wmed(lambda a: a["poincare"].sd_ratio),
        "sample_entropy": wmed(lambda a: a["nonlinear"].sample_entropy),
        "dfa_alpha1": wmed(lambda a: a["nonlinear"].dfa_alpha1),
        "higuchi_fd": wmed(lambda a: a["nonlinear"].higuchi_fd),
        "sns_index": wmed(lambda a: a["kubios"].sns_index),
        "pns_index": wmed(lambda a: a["kubios"].pns_index),
        "coherence_score": wmed(lambda a: a["coherence"].score),
        "respiration_rpm": wmed(lambda a: a["respiration"].rate_rpm),
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
