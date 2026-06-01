"""Kubios-style autonomic balance indices.

Reference: Kubios HRV Standard / Premium manual.
PNS Index ≈ z-mean of: MeanRR (+), RMSSD (+), HF nu (+) — relative to baseline
SNS Index ≈ z-mean of: HR (+), Baevsky SI (+), LF nu (+)
"""

from dataclasses import dataclass


@dataclass
class KubiosIndices:
    pns_index: float  # -2 (very low) ~ +2 (very high parasympathetic)
    sns_index: float  # -2 (very low) ~ +2 (very high sympathetic)


def _z(x: float, mean: float, sd: float) -> float:
    if sd <= 1e-9:
        return 0.0
    z = (x - mean) / sd
    return max(-3.0, min(3.0, z))


def kubios_indices(
    mean_rr_ms: float,
    rmssd_ms: float,
    hf_nu: float,
    hr_bpm: float,
    baevsky_si: float,
    lf_nu: float,
) -> KubiosIndices:
    # Healthy-adult resting baselines (approximate, Kubios documentation + Task Force 1996)
    PNS_BASELINE = {
        "mean_rr": (920.0, 130.0),
        "rmssd": (42.0, 22.0),
        "hf_nu": (55.0, 18.0),
    }
    SNS_BASELINE = {
        "hr": (65.0, 12.0),
        "baev": (80.0, 70.0),
        "lf_nu": (45.0, 18.0),
    }
    pns_z = (
        _z(mean_rr_ms, *PNS_BASELINE["mean_rr"])
        + _z(rmssd_ms, *PNS_BASELINE["rmssd"])
        + _z(hf_nu, *PNS_BASELINE["hf_nu"])
    ) / 3.0
    sns_z = (
        _z(hr_bpm, *SNS_BASELINE["hr"])
        + _z(baevsky_si, *SNS_BASELINE["baev"])
        + _z(lf_nu, *SNS_BASELINE["lf_nu"])
    ) / 3.0
    # Scale to Kubios's -2..+2 reporting range
    return KubiosIndices(
        pns_index=round(max(-2.0, min(2.0, pns_z * 1.2)), 2),
        sns_index=round(max(-2.0, min(2.0, sns_z * 1.2)), 2),
    )
