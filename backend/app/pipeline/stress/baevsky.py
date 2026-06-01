from dataclasses import dataclass
from typing import Literal

import numpy as np

Level = Literal["normal", "mild", "moderate", "high"]


@dataclass
class BaevskyResult:
    si: float
    level: Level
    mo_s: float
    amo_pct: float
    mxdmn_s: float


def baevsky_level(si: float) -> Level:
    if si < 150:
        return "normal"
    if si < 500:
        return "mild"
    if si < 900:
        return "moderate"
    return "high"


def baevsky_si(ibi_ms: np.ndarray) -> BaevskyResult:
    if len(ibi_ms) < 16:
        return BaevskyResult(0.0, "normal", 0.0, 0.0, 0.0)
    ibi_s = ibi_ms / 1000.0
    bin_width = 0.05
    bins = np.arange(ibi_s.min(), ibi_s.max() + bin_width, bin_width)
    if len(bins) < 2:
        return BaevskyResult(0.0, "normal", 0.0, 0.0, 0.0)
    counts, edges = np.histogram(ibi_s, bins=bins)
    if counts.sum() == 0:
        return BaevskyResult(0.0, "normal", 0.0, 0.0, 0.0)
    mode_idx = int(np.argmax(counts))
    mo = float((edges[mode_idx] + edges[mode_idx + 1]) / 2)
    amo = float(counts[mode_idx] / counts.sum() * 100)
    mxdmn = float(ibi_s.max() - ibi_s.min()) or 1e-6
    si = amo / (2 * mo * mxdmn)
    return BaevskyResult(
        si=si,
        level=baevsky_level(si),
        mo_s=mo,
        amo_pct=amo,
        mxdmn_s=mxdmn,
    )
