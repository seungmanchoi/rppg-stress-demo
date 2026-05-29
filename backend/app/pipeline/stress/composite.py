import math
from typing import Literal

Level = Literal["low", "mid", "high", "very_high"]


def _clip(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def composite_stress(baevsky_si: float, lf_hf: float, rmssd: float) -> float:
    s_baev = _clip(math.log10(max(baevsky_si, 1.0) / 50) / math.log10(1500 / 50))
    s_lfhf = _clip((lf_hf - 0.5) / 4.0)
    s_rmssd = _clip(1 - rmssd / 60)
    return 100 * (0.4 * s_baev + 0.4 * s_lfhf + 0.2 * s_rmssd)


def composite_level(score: float) -> Level:
    if score < 30:
        return "low"
    if score < 60:
        return "mid"
    if score < 80:
        return "high"
    return "very_high"
