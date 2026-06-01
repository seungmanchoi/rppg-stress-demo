from dataclasses import dataclass

import numpy as np


@dataclass
class TimeDomainHRV:
    hr_bpm: float
    ibi_mean_ms: float
    sdnn_ms: float
    rmssd_ms: float
    pnn50_pct: float
    pnn20_pct: float
    sdsd_ms: float
    cvnn_pct: float
    hrv_triangular_index: float


def time_domain_hrv(ibi_ms: np.ndarray) -> TimeDomainHRV:
    if len(ibi_ms) < 2:
        return TimeDomainHRV(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    diffs = np.diff(ibi_ms)
    mean_ibi = float(np.mean(ibi_ms))
    sdnn = float(np.std(ibi_ms))
    # HRV Triangular Index: total NN count / height of NN histogram (7.8125ms bins per Task Force 1996)
    bin_width = 7.8125
    bins = np.arange(ibi_ms.min(), ibi_ms.max() + bin_width, bin_width)
    if len(bins) >= 2:
        counts, _ = np.histogram(ibi_ms, bins=bins)
        peak = counts.max() if counts.size else 0
        hrvti = float(len(ibi_ms) / peak) if peak > 0 else 0.0
    else:
        hrvti = 0.0
    return TimeDomainHRV(
        hr_bpm=float(60_000 / mean_ibi),
        ibi_mean_ms=mean_ibi,
        sdnn_ms=sdnn,
        rmssd_ms=float(np.sqrt(np.mean(diffs**2))),
        pnn50_pct=float(np.sum(np.abs(diffs) > 50) / len(diffs) * 100),
        pnn20_pct=float(np.sum(np.abs(diffs) > 20) / len(diffs) * 100),
        sdsd_ms=float(np.std(diffs)),
        cvnn_pct=float(sdnn / mean_ibi * 100) if mean_ibi > 0 else 0.0,
        hrv_triangular_index=hrvti,
    )
