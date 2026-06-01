"""BVP signal quality and pulse-wave morphology metrics.

PQI (Pulse Quality Index) — beat-to-beat consistency, Elgendi 2016.
Spectral entropy — frequency-domain signal cleanliness (low = clean spectrum).
Pulse Rise Time — systolic upstroke duration, related to arterial stiffness.
"""

from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks


@dataclass
class BvpQuality:
    pqi: float  # 0~100, beat-shape consistency
    spectral_entropy: float  # 0~1, lower = cleaner dominant rhythm
    pulse_rise_time_ms: float  # systolic upstroke (ms), 100~250 normal


def _spectral_entropy(x: np.ndarray, fs: float) -> float:
    n = len(x)
    if n < 32:
        return 0.0
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    mag = np.abs(np.fft.rfft(x - np.mean(x)))
    band = (freqs >= 0.5) & (freqs <= 4.0)
    if not np.any(band):
        return 0.0
    p = mag[band]
    s = p.sum()
    if s <= 1e-12:
        return 0.0
    p = p / s
    nz = p[p > 0]
    h = -np.sum(nz * np.log2(nz))
    # Normalize to 0..1 by log2(N)
    h_norm = h / np.log2(len(p))
    return float(h_norm)


def _pqi(bvp: np.ndarray, fs: float) -> tuple[float, float]:
    """Pulse Quality Index via beat-template correlation + rise time.

    Returns (pqi 0..100, mean_rise_time_ms).
    """
    n = len(bvp)
    if n < int(3 * fs):
        return 0.0, 0.0
    # Normalize, find peaks (HR-aware minimum distance: 0.4s = 150 BPM ceiling)
    x = (bvp - np.mean(bvp)) / (np.std(bvp) + 1e-9)
    min_dist = int(0.4 * fs)
    peaks, _ = find_peaks(x, distance=min_dist, prominence=0.3)
    if len(peaks) < 4:
        return 0.0, 0.0
    # Extract beats: 30% before peak, 70% after
    window = int(0.8 * fs)
    pre = int(window * 0.3)
    post = window - pre
    beats = []
    rise_times_samples = []
    for p_idx in peaks:
        if p_idx - pre < 0 or p_idx + post > n:
            continue
        beat = x[p_idx - pre : p_idx + post]
        beats.append(beat)
        # Foot = local minimum in the pre-peak segment
        foot = int(np.argmin(beat[:pre]))
        rise_times_samples.append(pre - foot)
    if len(beats) < 4:
        return 0.0, 0.0
    beats = np.array(beats)
    template = np.mean(beats, axis=0)
    # Mean Pearson correlation of each beat to template
    template_z = (template - template.mean()) / (template.std() + 1e-9)
    corrs = []
    for b in beats:
        bz = (b - b.mean()) / (b.std() + 1e-9)
        corrs.append(float(np.mean(bz * template_z)))
    pqi = float(np.clip(np.mean(corrs), 0, 1) * 100)
    rise_ms = float(np.mean(rise_times_samples) / fs * 1000)
    return pqi, rise_ms


def bvp_quality(bvp: np.ndarray, fs: float) -> BvpQuality:
    if len(bvp) < int(3 * fs):
        return BvpQuality(0.0, 0.0, 0.0)
    pqi, rise = _pqi(bvp, fs)
    se = _spectral_entropy(bvp, fs)
    return BvpQuality(pqi=pqi, spectral_entropy=se, pulse_rise_time_ms=rise)
