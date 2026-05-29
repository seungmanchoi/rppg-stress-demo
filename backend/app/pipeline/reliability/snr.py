import numpy as np
from scipy.signal import welch


def bvp_snr_db(bvp: np.ndarray, fs: float) -> float:
    """SNR in dB: power in cardiac band (0.7~3 Hz) vs out-of-band."""
    if len(bvp) < int(fs * 4):
        return 0.0
    nperseg = min(len(bvp), int(fs * 8))
    f, psd = welch(bvp.astype(float), fs=fs, nperseg=nperseg)
    sig_mask = (f >= 0.7) & (f <= 3.0)
    sig_power = float(np.trapz(psd[sig_mask], f[sig_mask]))
    noise_power = float(np.trapz(psd[~sig_mask], f[~sig_mask])) or 1e-12
    return 10 * float(np.log10(sig_power / noise_power))
