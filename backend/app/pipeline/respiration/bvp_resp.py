"""BVP-derived respiration rate.

Approach: amplitude modulation of the BVP signal carries respiratory
information (Respiratory Sinus Arrhythmia + baseline wander). We compute the
analytic-signal envelope, band-pass to 0.1~0.5Hz (6~30 breaths/min), then
find the dominant peak via FFT.

Reference: Karlen, W., Raman, S., Ansermino, J.M., Dumont, G.A. (2013).
Multiparameter Respiratory Rate Estimation from the Photoplethysmogram. IEEE TBME.
"""

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, filtfilt, hilbert


@dataclass
class RespirationResult:
    rate_rpm: float  # breaths per minute
    confidence: float  # 0~1, peak-prominence over noise floor


def _bandpass(x: np.ndarray, fs: float, lo: float, hi: float, order: int = 3) -> np.ndarray:
    nyq = 0.5 * fs
    b, a = butter(order, [lo / nyq, hi / nyq], btype="band")
    return filtfilt(b, a, x)


def respiration_from_bvp(bvp: np.ndarray, fs: float) -> RespirationResult:
    """Estimate respiration rate (breaths per minute) from a BVP signal.

    Returns rate=0 when signal is too short (<10s) or no dominant frequency.
    """
    if len(bvp) < int(10 * fs):
        return RespirationResult(0.0, 0.0)
    # Envelope = magnitude of analytic signal of HR-filtered BVP
    try:
        # Pre-filter to heart band so envelope reflects pulse amplitude
        hr_band = _bandpass(bvp, fs, 0.7, 3.5)
        env = np.abs(hilbert(hr_band))
        # De-mean envelope and low-pass to respiratory band 0.1~0.5 Hz (6~30 rpm)
        env = env - np.mean(env)
        resp = _bandpass(env, fs, 0.1, 0.5)
    except Exception:  # noqa: BLE001
        return RespirationResult(0.0, 0.0)
    # FFT to find dominant frequency
    n = len(resp)
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    mag = np.abs(np.fft.rfft(resp))
    band = (freqs >= 0.1) & (freqs <= 0.5)
    if not np.any(band):
        return RespirationResult(0.0, 0.0)
    band_freqs = freqs[band]
    band_mag = mag[band]
    peak_idx = int(np.argmax(band_mag))
    peak_freq = float(band_freqs[peak_idx])
    rpm = peak_freq * 60.0
    if rpm < 6 or rpm > 30:
        return RespirationResult(0.0, 0.0)
    # Confidence: peak vs out-of-band noise floor
    noise = float(np.mean(mag[~band])) + 1e-12
    conf = float(min(1.0, band_mag[peak_idx] / (noise * 6.0)))
    return RespirationResult(rate_rpm=round(rpm, 1), confidence=round(conf, 2))
