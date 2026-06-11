"""Measurement-aware reliability weighting for HRV-derived stress scores.

Not every HRV index is trustworthy from a 30-second webcam clip. Successive-
difference metrics (RMSSD, SD1, pNN50) stabilise within ~20 beats, but:

- LF / LF-HF need several slow cycles — the LF band bottoms out at 0.04 Hz
  (a 25-second period), so a short record barely contains one cycle.
- DFA α1, Sample/Approximate Entropy and Higuchi FD are defined over hundreds
  of beats; on 30–60 of them they are essentially noise.

Rather than hard-cutting these, we attenuate each component by a confidence in
[0, 1] derived from beat count, record duration and signal SNR, then renormalize
the surviving weights. A score therefore leans on whichever indices the actual
measurement can support — the formula's identity is unchanged, only the trust
placed in each term adapts. ``confidences=None`` reproduces the fixed-weight
behaviour exactly.
"""
from __future__ import annotations

from dataclasses import dataclass


def _ramp(x: float, lo: float, hi: float) -> float:
    """0 below ``lo``, 1 above ``hi``, linear in between."""
    if hi <= lo:
        return 1.0
    return max(0.0, min(1.0, (x - lo) / (hi - lo)))


def signal_quality_factor(snr_db: float) -> float:
    """Global multiplier from BVP SNR: ~0.55 at very low SNR, 1.0 when clean."""
    return 0.55 + 0.45 * _ramp(snr_db, -3.0, 6.0)


@dataclass
class MetricConfidence:
    """Confidence (0~1) per metric category for one measurement."""

    short_time: float
    distribution: float
    hf: float
    lf: float
    nonlinear_strong: float
    nonlinear_soft: float
    coherence: float
    sns: float
    pns: float
    quality: float

    def get(self, category: str) -> float:
        return float(getattr(self, category, 1.0))


# Map each stress component `name` (shared across v1/v2/v3/v4) to a category.
NAME_TO_CATEGORY = {
    "baevsky_si": "distribution",
    "lf_hf": "lf",
    "rmssd": "short_time",
    "sdnn": "distribution",
    "pnn50": "short_time",
    "pnn20": "short_time",
    "sd2_sd1": "distribution",
    "sd1": "short_time",
    "hf_nu": "hf",
    "sample_entropy": "nonlinear_soft",
    "dfa_alpha1": "nonlinear_strong",
    "higuchi_fd": "nonlinear_soft",
    "sns_index": "sns",
    "pns_index_inv": "pns",
    "coherence_inv": "coherence",
    "respiration": "hf",
    "hr_elevation": "short_time",
}


def metric_confidences(
    beat_count: int, duration_s: float, snr_db: float
) -> MetricConfidence:
    b = float(beat_count)
    d = float(duration_s)
    q = signal_quality_factor(snr_db)
    short_time = 0.62 + 0.38 * _ramp(b, 16, 60)
    distribution = 0.40 + 0.60 * _ramp(b, 18, 55)
    hf = 0.40 + 0.60 * _ramp(d, 25, 110)
    lf = 0.12 + 0.88 * _ramp(d, 45, 200)
    nonlinear_strong = 0.08 + 0.92 * _ramp(b, 45, 220)
    nonlinear_soft = 0.22 + 0.78 * _ramp(b, 32, 150)
    coherence = 0.45 + 0.55 * _ramp(d, 25, 120)
    return MetricConfidence(
        short_time=short_time * q,
        distribution=distribution * q,
        hf=hf * q,
        lf=lf * q,
        nonlinear_strong=nonlinear_strong * q,
        nonlinear_soft=nonlinear_soft * q,
        coherence=coherence * q,
        sns=(0.5 * distribution + 0.5 * lf) * q,
        pns=(0.5 * short_time + 0.5 * hf) * q,
        quality=q,
    )


def confidence_for(name: str, conf: MetricConfidence | None) -> float:
    if conf is None:
        return 1.0
    category = NAME_TO_CATEGORY.get(name)
    if category is None:
        return 1.0
    return conf.get(category)
