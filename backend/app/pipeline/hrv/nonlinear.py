from dataclasses import dataclass

import numpy as np


@dataclass
class Poincare:
    sd1: float
    sd2: float
    sd_ratio: float  # SD2/SD1
    ellipse_area: float  # π · SD1 · SD2


@dataclass
class NonlinearHRV:
    sample_entropy: float
    approximate_entropy: float
    shannon_entropy: float
    dfa_alpha1: float
    higuchi_fd: float


def poincare(ibi_ms: np.ndarray) -> Poincare:
    if len(ibi_ms) < 3:
        return Poincare(0.0, 0.0, 0.0, 0.0)
    x1, x2 = ibi_ms[:-1], ibi_ms[1:]
    sd1 = float(np.std(x2 - x1) / np.sqrt(2))
    sd2 = float(np.std(x2 + x1) / np.sqrt(2))
    ratio = float(sd2 / sd1) if sd1 > 1e-9 else 0.0
    area = float(np.pi * sd1 * sd2)
    return Poincare(sd1, sd2, ratio, area)


def _sample_entropy(x: np.ndarray, m: int = 2, r: float | None = None) -> float:
    """Richman-Moorman Sample Entropy. m=2 is HRV standard."""
    n = len(x)
    if n < m + 2:
        return 0.0
    if r is None:
        r = 0.2 * float(np.std(x))
    if r <= 0:
        return 0.0

    def _phi(mm: int) -> float:
        # Number of vector pairs within tolerance (Chebyshev distance)
        templates = np.array([x[i : i + mm] for i in range(n - mm)])
        count = 0
        for i in range(len(templates)):
            d = np.max(np.abs(templates[i + 1 :] - templates[i]), axis=1)
            count += int(np.sum(d <= r))
        return float(count)

    b = _phi(m)
    a = _phi(m + 1)
    if a == 0 or b == 0:
        return 0.0
    return float(-np.log(a / b))


def _approximate_entropy(x: np.ndarray, m: int = 2, r: float | None = None) -> float:
    n = len(x)
    if n < m + 2:
        return 0.0
    if r is None:
        r = 0.2 * float(np.std(x))
    if r <= 0:
        return 0.0

    def _phi(mm: int) -> float:
        templates = np.array([x[i : i + mm] for i in range(n - mm + 1)])
        c = np.zeros(len(templates))
        for i in range(len(templates)):
            d = np.max(np.abs(templates - templates[i]), axis=1)
            c[i] = float(np.sum(d <= r)) / len(templates)
        c = c[c > 0]
        return float(np.mean(np.log(c))) if len(c) else 0.0

    return float(_phi(m) - _phi(m + 1))


def _shannon_entropy(x: np.ndarray, bins: int = 16) -> float:
    if len(x) < 2:
        return 0.0
    hist, _ = np.histogram(x, bins=bins, density=False)
    p = hist[hist > 0] / hist.sum()
    return float(-np.sum(p * np.log2(p)))


def _dfa_alpha1(x: np.ndarray, scales: tuple[int, ...] = (4, 6, 8, 10, 12, 16)) -> float:
    """Detrended Fluctuation Analysis, short-term scaling exponent α1.
    Standard short-term range: 4~16 beats (HRV)."""
    n = len(x)
    valid_scales = [s for s in scales if s <= n // 2]
    if len(valid_scales) < 2:
        return 0.0
    y = np.cumsum(x - np.mean(x))
    f = []
    for s in valid_scales:
        nb = n // s
        if nb < 2:
            continue
        segs = y[: nb * s].reshape(nb, s)
        # Detrend each segment with linear fit
        t = np.arange(s)
        fluctuations = []
        for seg in segs:
            coef = np.polyfit(t, seg, 1)
            detrended = seg - np.polyval(coef, t)
            fluctuations.append(np.mean(detrended**2))
        f.append(np.sqrt(np.mean(fluctuations)))
    if len(f) < 2:
        return 0.0
    log_s = np.log(valid_scales[: len(f)])
    log_f = np.log(np.array(f) + 1e-12)
    slope, _ = np.polyfit(log_s, log_f, 1)
    return float(slope)


def _higuchi_fd(x: np.ndarray, k_max: int = 8) -> float:
    """Higuchi Fractal Dimension. 1.0 (smooth) ~ 2.0 (random)."""
    n = len(x)
    if n < k_max * 2:
        return 0.0
    lk = []
    for k in range(1, k_max + 1):
        lm = []
        for m in range(k):
            idx = np.arange(m, n, k)
            if len(idx) < 2:
                continue
            sub = x[idx]
            length = np.sum(np.abs(np.diff(sub))) * (n - 1) / (len(idx) * k) / k
            lm.append(length)
        if lm:
            lk.append(np.mean(lm))
    if len(lk) < 2:
        return 0.0
    ln_k = np.log(1.0 / np.arange(1, len(lk) + 1))
    ln_lk = np.log(np.array(lk) + 1e-12)
    slope, _ = np.polyfit(ln_k, ln_lk, 1)
    return float(slope)


def nonlinear_hrv(ibi_ms: np.ndarray) -> NonlinearHRV:
    if len(ibi_ms) < 8:
        return NonlinearHRV(0.0, 0.0, 0.0, 0.0, 0.0)
    x = ibi_ms.astype(float)
    return NonlinearHRV(
        sample_entropy=_sample_entropy(x),
        approximate_entropy=_approximate_entropy(x),
        shannon_entropy=_shannon_entropy(x),
        dfa_alpha1=_dfa_alpha1(x),
        higuchi_fd=_higuchi_fd(x),
    )
