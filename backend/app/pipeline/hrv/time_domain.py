from dataclasses import dataclass

import numpy as np


@dataclass
class TimeDomainHRV:
    hr_bpm: float
    ibi_mean_ms: float
    sdnn_ms: float
    rmssd_ms: float
    pnn50_pct: float


def time_domain_hrv(ibi_ms: np.ndarray) -> TimeDomainHRV:
    if len(ibi_ms) < 2:
        return TimeDomainHRV(0.0, 0.0, 0.0, 0.0, 0.0)
    diffs = np.diff(ibi_ms)
    mean_ibi = float(np.mean(ibi_ms))
    return TimeDomainHRV(
        hr_bpm=float(60_000 / mean_ibi),
        ibi_mean_ms=mean_ibi,
        sdnn_ms=float(np.std(ibi_ms)),
        rmssd_ms=float(np.sqrt(np.mean(diffs**2))),
        pnn50_pct=float(np.sum(np.abs(diffs) > 50) / len(diffs) * 100),
    )
