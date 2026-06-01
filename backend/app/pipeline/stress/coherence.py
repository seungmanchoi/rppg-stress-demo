"""HeartMath-style Cardiac Coherence score.

Coherence measures how 'tuned' the HRV signal is to a single dominant frequency
in the 0.04~0.26Hz range (resonance frequency, typically ~0.1Hz with slow breathing).
The HeartMath emWave reports 0 (low) ~ 3 (high) using peak/total ratio in this band.

Method: take Lomb-Scargle PSD of IBI series, find peak in resonance band,
compute peak-band power / total power. Score = ratio * 6 (clipped to 0..3).
"""

from dataclasses import dataclass

import numpy as np
from scipy.signal import lombscargle


@dataclass
class CoherenceResult:
    score: float  # 0~3, HeartMath emWave compatible scale
    peak_freq_hz: float  # dominant frequency in 0.04~0.26Hz band


def cardiac_coherence(ibi_ms: np.ndarray) -> CoherenceResult:
    if len(ibi_ms) < 16:
        return CoherenceResult(0.0, 0.0)
    t = np.cumsum(ibi_ms) / 1000.0
    x = ibi_ms - np.mean(ibi_ms)
    freqs = np.linspace(0.01, 0.5, 512)
    psd = lombscargle(t, x, freqs * 2 * np.pi, normalize=True)
    coh_mask = (freqs >= 0.04) & (freqs <= 0.26)
    if not np.any(coh_mask):
        return CoherenceResult(0.0, 0.0)
    peak_idx = int(np.argmax(psd[coh_mask]))
    peak_freq = float(freqs[coh_mask][peak_idx])
    peak_pow = float(psd[coh_mask][peak_idx])
    # Bandwidth ±0.015Hz around the peak (HeartMath's 'peak ± 0.015' definition)
    band_mask = np.abs(freqs - peak_freq) <= 0.015
    band_pow = float(np.trapz(psd[band_mask], freqs[band_mask]))
    total_pow = float(np.trapz(psd, freqs))
    if total_pow <= 1e-12 or peak_pow <= 1e-12:
        return CoherenceResult(0.0, peak_freq)
    ratio = band_pow / total_pow
    score = float(min(3.0, ratio * 6.0))
    return CoherenceResult(score, peak_freq)
