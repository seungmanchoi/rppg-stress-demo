from dataclasses import dataclass

import numpy as np
from scipy.signal import lombscargle


@dataclass
class FreqDomainHRV:
    vlf_power: float
    lf_power: float
    hf_power: float
    total_power: float
    lf_hf_ratio: float
    lf_nu: float
    hf_nu: float


def freq_domain_hrv(ibi_ms: np.ndarray) -> FreqDomainHRV:
    if len(ibi_ms) < 16:
        return FreqDomainHRV(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    t = np.cumsum(ibi_ms) / 1000.0
    x = ibi_ms - np.mean(ibi_ms)
    # Frequency grid (0.003~0.4Hz) — covers VLF/LF/HF
    freqs = np.linspace(0.003, 0.4, 384)
    psd = lombscargle(t, x, freqs * 2 * np.pi, normalize=True)
    vlf_mask = (freqs >= 0.003) & (freqs < 0.04)
    lf_mask = (freqs >= 0.04) & (freqs < 0.15)
    hf_mask = (freqs >= 0.15) & (freqs <= 0.40)
    vlf = float(np.trapz(psd[vlf_mask], freqs[vlf_mask]))
    lf = float(np.trapz(psd[lf_mask], freqs[lf_mask]))
    hf = float(np.trapz(psd[hf_mask], freqs[hf_mask]))
    total = vlf + lf + hf
    ratio = lf / hf if hf > 1e-12 else 0.0
    # Normalized units exclude VLF per Task Force 1996
    denom = lf + hf
    lf_nu = float(lf / denom * 100) if denom > 1e-12 else 0.0
    hf_nu = float(hf / denom * 100) if denom > 1e-12 else 0.0
    return FreqDomainHRV(vlf, lf, hf, total, ratio, lf_nu, hf_nu)
