from typing import Literal

Grade = Literal["low", "medium", "high"]


def _clip(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def reliability_score(snr_db: float, tracking: float, motion_px: float, hr_dev: float) -> float:
    snr = _clip((snr_db + 5) / 15)
    track = _clip(tracking)
    motion = _clip(1 - motion_px / 5)
    consensus = _clip(1 - abs(hr_dev) / 10)
    return 100 * (0.30 * snr + 0.25 * track + 0.20 * motion + 0.25 * consensus)


def reliability_grade(score: float) -> Grade:
    if score >= 75:
        return "high"
    if score >= 45:
        return "medium"
    return "low"
