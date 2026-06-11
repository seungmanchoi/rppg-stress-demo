"""BVP → IBI extraction (robust to noisy camera signals).

Pipeline:
1. Band-pass to cardiac frequency range (0.7~3.5 Hz)
2. Savitzky-Golay smoothing to suppress noise peaks
3. Estimate dominant HR via FFT (+ 2nd-harmonic mis-lock correction)
4. Detect peaks with HR-aware min-distance + strong prominence
5. Parabolic (sub-sample) peak refinement — recovers timing finer than the
   sampling grid, which is essential at 30 fps where one sample ≈ 33 ms and
   raw integer-index IBIs quantize RMSSD into a staircase
6. Split clean missed-beat gaps (≈ integer multiples of the expected interval)
   back into single beats instead of discarding them
7. Drop IBIs outside ±30% of expected interval
8. MAD outlier cleanup (2·MAD)

The orchestrator hands this function a BVP that has already been resampled onto
a uniform, oversampled time grid (see ``preprocess.resample``), so peak indices
map linearly to real time and ``fs`` is exact.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, filtfilt, find_peaks, savgol_filter


def bandpass(signal: np.ndarray, fs: float, lo: float = 0.7, hi: float = 3.5) -> np.ndarray:
    nyq = fs / 2
    hi = min(hi, nyq * 0.99)
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


def _parabolic_refine(y: np.ndarray, peaks: np.ndarray) -> np.ndarray:
    """Sub-sample peak locations via 3-point parabolic interpolation."""
    refined = peaks.astype(np.float64)
    for i, p in enumerate(peaks):
        if 0 < p < len(y) - 1:
            y0, y1, y2 = float(y[p - 1]), float(y[p]), float(y[p + 1])
            denom = y0 - 2 * y1 + y2
            if denom != 0.0:
                delta = 0.5 * (y0 - y2) / denom
                if -1.0 < delta < 1.0:
                    refined[i] = p + delta
    return refined


def _split_missed_beats(ibi_ms: np.ndarray, expected_ms: float) -> np.ndarray:
    """Split gaps that are clean integer multiples of the expected IBI.

    A single missed detection produces an interval ≈ 2× normal. Discarding it
    breaks the successive-difference chain that RMSSD/SDSD depend on, so when a
    gap divides evenly into beats that each land within ±30% of expected, we
    restore the implied beats instead of dropping the gap.
    """
    out: list[float] = []
    for v in ibi_ms:
        ratio = v / expected_ms if expected_ms > 0 else 1.0
        if ratio >= 1.5:
            k = min(int(round(ratio)), 4)
            if k >= 2 and abs(v / k - expected_ms) <= 0.3 * expected_ms:
                out.extend([v / k] * k)
                continue
        out.append(float(v))
    return np.asarray(out, dtype=np.float64)


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
    # Detect 2nd-harmonic mis-locking: if dominant freq > 2.4 Hz (≈ 144 BPM)
    # but half-frequency band has non-trivial power, halve it.
    if hr_hz > 2.4:
        half_hz = hr_hz / 2
        n = len(filtered)
        spec = np.abs(np.fft.rfft(filtered - filtered.mean()))
        freqs = np.fft.rfftfreq(n, 1 / fs)
        peak_pow = float(spec[(freqs >= hr_hz - 0.05) & (freqs <= hr_hz + 0.05)].sum())
        half_pow = float(spec[(freqs >= half_hz - 0.05) & (freqs <= half_hz + 0.05)].sum())
        if half_hz >= 0.7 and half_pow > peak_pow * 0.25:
            hr_hz = half_hz

    if hr_hz <= 0:
        peaks, _ = find_peaks(filtered, distance=int(0.4 * fs))
    else:
        expected_ibi_s = 1.0 / hr_hz
        min_dist = max(1, int(round(expected_ibi_s * fs * 0.7)))
        prominence = float(np.std(filtered)) * 0.5
        peaks, _ = find_peaks(filtered, distance=min_dist, prominence=prominence)

    if len(peaks) < 3:
        return np.array([])

    # Sub-sample peak timing — critical for HRV at camera frame rates.
    peak_pos = _parabolic_refine(filtered, peaks)
    ibi_ms = np.diff(peak_pos) / fs * 1000.0

    # Restore clean missed beats, then drop intervals that deviate >30%.
    if hr_hz > 0:
        expected_ms = 1000.0 / hr_hz
        ibi_ms = _split_missed_beats(ibi_ms, expected_ms)
        keep = (ibi_ms >= expected_ms * 0.7) & (ibi_ms <= expected_ms * 1.3)
        ibi_ms = ibi_ms[keep]

    # 2·MAD cleanup (tighter than typical 3·MAD). A physiological floor on the
    # cut-off keeps near-constant inputs (and the sub-ms ripple introduced by
    # parabolic refinement) from collapsing genuine beats to a handful.
    if len(ibi_ms) >= 3:
        med = float(np.median(ibi_ms))
        mad = float(np.median(np.abs(ibi_ms - med)))
        cut = max(2.0 * mad, 0.03 * med)
        ibi_ms = ibi_ms[np.abs(ibi_ms - med) <= cut]

    return ibi_ms
