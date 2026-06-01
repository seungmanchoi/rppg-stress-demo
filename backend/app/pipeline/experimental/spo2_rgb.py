"""RGB-only SpO2 estimation (experimental, RGB CAMERA ONLY).

Approach: ratio-of-ratios from Red vs Blue channels (Blue absorbs more
deoxy-Hb than Green, so R/B has similar shape to R/IR used in real pulse
oximeters when only RGB is available). Calibrated to typical healthy
adult range (96~99%).

References:
- Verkruysse et al. 2008 — first rPPG demonstration with green channel.
- Tarassenko et al. 2014 — non-contact SpO2 feasibility from RGB.
- Bal U. 2015, Tian et al. 2020 — RGB SpO2 with R/B ratio-of-ratios.

⚠ ACCURACY: This estimate is NOT clinically validated. Real pulse
oximeters use red (660nm) + infrared (940nm). RGB cameras lack IR, so
the result is best read as a relative trend, not an absolute SpO2 value.
Expected error vs. medical pulse oximeter: ±3~5% under good conditions,
much larger under poor lighting or motion.
"""

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, filtfilt


@dataclass
class Spo2Estimate:
    spo2_pct: float  # estimated SpO2, 80~100 typical
    confidence: float  # 0~1


def _bandpass(x: np.ndarray, fs: float, lo: float, hi: float) -> np.ndarray:
    nyq = 0.5 * fs
    b, a = butter(3, [lo / nyq, hi / nyq], btype="band")
    return filtfilt(b, a, x)


def _ac_dc(channel: np.ndarray, fs: float) -> tuple[float, float]:
    """Compute pulsatile (AC) RMS amplitude and baseline (DC) mean."""
    dc = float(np.mean(channel))
    if dc <= 1e-9:
        return 0.0, 0.0
    try:
        ac = _bandpass(channel, fs, 0.7, 3.5)
        ac_rms = float(np.sqrt(np.mean(ac**2)))
    except Exception:  # noqa: BLE001
        ac_rms = 0.0
    return ac_rms, dc


def estimate_spo2_rgb(rgb_signal: np.ndarray, fs: float) -> Spo2Estimate:
    """rgb_signal: shape (T, 3) — per-frame R, G, B means from face ROI."""
    if rgb_signal is None or len(rgb_signal) < int(5 * fs):
        return Spo2Estimate(0.0, 0.0)
    r = rgb_signal[:, 0].astype(float)
    b = rgb_signal[:, 2].astype(float)
    r_ac, r_dc = _ac_dc(r, fs)
    b_ac, b_dc = _ac_dc(b, fs)
    if r_dc <= 1e-9 or b_dc <= 1e-9 or b_ac <= 1e-12:
        return Spo2Estimate(0.0, 0.0)
    # Ratio-of-ratios; smaller value → higher SpO2
    rr = (r_ac / r_dc) / (b_ac / b_dc)
    # Linear approximation: SpO2 ≈ 110 − 25·rr (calibrated to clamp 90~100 for typical face)
    spo2 = 110.0 - 25.0 * rr
    spo2 = float(np.clip(spo2, 85.0, 100.0))
    # Confidence drops when AC is small (noisy signal)
    snr_proxy = min(r_ac / (r_dc + 1e-9), b_ac / (b_dc + 1e-9))
    conf = float(min(1.0, snr_proxy * 250))
    return Spo2Estimate(spo2_pct=round(spo2, 1), confidence=round(conf, 2))
