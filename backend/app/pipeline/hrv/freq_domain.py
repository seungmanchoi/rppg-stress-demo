from dataclasses import dataclass

import numpy as np
from scipy.signal import lombscargle


@dataclass
class FreqDomainHRV:
    lf_power: float
    hf_power: float
    lf_hf_ratio: float


def freq_domain_hrv(ibi_ms: np.ndarray) -> FreqDomainHRV:
    if len(ibi_ms) < 16:
        return FreqDomainHRV(0.0, 0.0, 0.0)
    t = np.cumsum(ibi_ms) / 1000.0
    x = ibi_ms - np.mean(ibi_ms)
    freqs = np.linspace(0.04, 0.4, 256)
    psd = lombscargle(t, x, freqs * 2 * np.pi, normalize=True)
    lf_mask = (freqs >= 0.04) & (freqs < 0.15)
    hf_mask = (freqs >= 0.15) & (freqs <= 0.40)
    lf = float(np.trapz(psd[lf_mask], freqs[lf_mask]))
    hf = float(np.trapz(psd[hf_mask], freqs[hf_mask]))
    ratio = lf / hf if hf > 1e-12 else 0.0
    return FreqDomainHRV(lf, hf, ratio)
