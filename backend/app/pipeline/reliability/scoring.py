from typing import Literal

Grade = Literal["low", "medium", "high"]

# SNR floor gate: below this, the pulse is buried in noise and the IBI series
# (hence RMSSD/Baevsky/stress) is untrustworthy *regardless* of how good face
# tracking or stillness was. Cap reliability below the consensus inclusion
# threshold (30) so such a card can't drag the aggregate — it stays visible as
# a low-reliability card (HR may still be informative) but is excluded from the
# reliability-weighted consensus.
SNR_FLOOR_DB = -3.0
SNR_FLOOR_CAP = 25.0


def _clip(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def reliability_score(snr_db: float, tracking: float, motion_px: float, hr_dev: float) -> float:
    snr = _clip((snr_db + 5) / 15)
    track = _clip(tracking)
    motion = _clip(1 - motion_px / 5)
    consensus = _clip(1 - abs(hr_dev) / 10)
    score = 100 * (0.30 * snr + 0.25 * track + 0.20 * motion + 0.25 * consensus)
    if snr_db < SNR_FLOOR_DB:
        score = min(score, SNR_FLOOR_CAP)
    return score


def reliability_grade(score: float) -> Grade:
    if score >= 75:
        return "high"
    if score >= 45:
        return "medium"
    return "low"
