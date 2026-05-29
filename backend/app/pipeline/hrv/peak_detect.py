import numpy as np
from scipy.signal import butter, filtfilt, find_peaks


def bandpass(signal: np.ndarray, fs: float, lo: float = 0.7, hi: float = 3.5) -> np.ndarray:
    nyq = fs / 2
    b, a = butter(3, [lo / nyq, hi / nyq], btype="band")
    return filtfilt(b, a, signal)


def bvp_to_ibi(bvp: np.ndarray, fs: float) -> np.ndarray:
    """BVP waveform → IBI series in milliseconds. Removes outliers via median ± 3·MAD."""
    if len(bvp) < int(fs * 2):
        return np.array([])
    filtered = bandpass(bvp.astype(float), fs)
    peaks, _ = find_peaks(filtered, distance=int(0.4 * fs))
    if len(peaks) < 2:
        return np.array([])
    ibi_ms = np.diff(peaks) / fs * 1000.0

    if len(ibi_ms) >= 3:
        med = np.median(ibi_ms)
        mad = np.median(np.abs(ibi_ms - med)) or 1.0
        ibi_ms = ibi_ms[np.abs(ibi_ms - med) < 3 * mad]
    return ibi_ms
