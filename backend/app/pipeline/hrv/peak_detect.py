"""BVP → IBI extraction (robust to noisy camera signals).

Pipeline:
1. Band-pass to cardiac frequency range (0.7~3.5 Hz)
2. Savitzky-Golay smoothing to suppress noise peaks
3. Estimate dominant HR via FFT
4. Detect peaks with HR-aware min-distance + strong prominence
5. Drop IBIs outside ±25% of expected interval
6. MAD outlier cleanup (2·MAD)
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, filtfilt, find_peaks, savgol_filter


def bandpass(signal: np.ndarray, fs: float, lo: float = 0.7, hi: float = 3.5) -> np.ndarray:
    nyq = fs / 2
    b, a = butter(3, [lo / nyq, hi / nyq], btype="band")
    return filtfilt(b, a, signal)


def estimate_hr_hz(filtered: np.ndarray, fs: float) -> float:
    """Return dominant heart frequency in Hz (0 if undetectable)."""
    n = len(filtered)
    if n < int(fs * 4):
        return 0.0
    spec = np.abs(np.fft.rfft(filtered - filtered.mean()))
    freqs = np.fft.rfftfreq(n, 1 / fs)
    band = (freqs >= 0.7) & (freqs <= 3.5)
    if not band.any():
        return 0.0
    return float(freqs[band][int(np.argmax(spec[band]))])


def bvp_to_ibi(bvp: np.ndarray, fs: float) -> np.ndarray:
    """BVP waveform → IBI series in milliseconds, with strong artefact rejection."""
    if len(bvp) < int(fs * 2):
        return np.array([])
    filtered = bandpass(bvp.astype(float), fs)

    # Smooth to suppress sub-cardiac noise peaks (window ~0.2s)
    win = max(5, int(fs * 0.2))
    if win % 2 == 0:
        win += 1
    if len(filtered) > win:
        filtered = savgol_filter(filtered, window_length=win, polyorder=2)

    hr_hz = estimate_hr_hz(filtered, fs)
    if hr_hz <= 0:
        peaks, _ = find_peaks(filtered, distance=int(0.4 * fs))
    else:
        expected_ibi_s = 1.0 / hr_hz
        min_dist = max(1, int(round(expected_ibi_s * fs * 0.7)))
        prominence = float(np.std(filtered)) * 0.5
        peaks, _ = find_peaks(filtered, distance=min_dist, prominence=prominence)

    if len(peaks) < 3:
        return np.array([])

    ibi_ms = np.diff(peaks) / fs * 1000.0

    # Strict window: drop intervals that deviate more than 25% from expected.
    if hr_hz > 0:
        expected_ms = 1000.0 / hr_hz
        keep = (ibi_ms >= expected_ms * 0.75) & (ibi_ms <= expected_ms * 1.25)
        ibi_ms = ibi_ms[keep]

    # 2·MAD cleanup (tighter than typical 3·MAD).
    if len(ibi_ms) >= 3:
        med = float(np.median(ibi_ms))
        mad = float(np.median(np.abs(ibi_ms - med))) or 1.0
        ibi_ms = ibi_ms[np.abs(ibi_ms - med) < 2 * mad]

    return ibi_ms
