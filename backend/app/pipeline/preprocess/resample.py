"""Resample a frame-indexed signal onto a uniform time grid.

Webcam capture via ``canvas.captureStream`` is variable-frame-rate: the gap
between consecutive frames drifts (28→32 fps and back). Every rPPG algorithm
emits one BVP sample per frame, so if we later convert peak *indices* to time
using a single average fps, the per-frame timing error leaks directly into the
inter-beat-interval (IBI) series and corrupts every HRV metric — RMSSD and
SDNN most of all.

The fix is to treat each BVP sample as living at its true capture timestamp and
interpolate onto an evenly spaced grid. We also upsample (``oversample`` > 1) so
that downstream integer-index peak picking has a finer time resolution than the
~33 ms native to 30 fps capture; combined with parabolic peak refinement this
brings IBI quantization down from tens of ms to well under a millisecond.

We use PCHIP (shape-preserving monotone cubic) interpolation: it follows the
pulse waveform more faithfully than linear interpolation without the overshoot
that ordinary cubic splines introduce near sharp systolic peaks.
"""
from __future__ import annotations

import numpy as np
from scipy.interpolate import PchipInterpolator


def timestamps_usable(timestamps_ms: np.ndarray | None, n_samples: int) -> bool:
    """True when per-frame timestamps are present, aligned, and strictly rising.

    OpenCV occasionally reports all-zero or non-monotonic ``CAP_PROP_POS_MSEC``
    for some containers; in that case we fall back to assuming uniform spacing.
    """
    if timestamps_ms is None:
        return False
    ts = np.asarray(timestamps_ms, dtype=np.float64)
    if ts.size != n_samples or ts.size < 2:
        return False
    if not np.all(np.isfinite(ts)):
        return False
    span = ts[-1] - ts[0]
    if span <= 0:
        return False
    # Require predominantly increasing timestamps (allow a few equal/back ticks).
    diffs = np.diff(ts)
    if np.median(diffs) <= 0:
        return False
    return float(np.mean(diffs > 0)) >= 0.9


def resample_uniform(
    signal: np.ndarray,
    timestamps_ms: np.ndarray | None,
    fs: float,
    oversample: int = 4,
) -> tuple[np.ndarray, float]:
    """Resample ``signal`` (sampled at the given timestamps) to a uniform grid.

    Parameters
    ----------
    signal:        1-D BVP (or other per-frame) waveform, length T.
    timestamps_ms: per-frame capture times in ms, length T. If unusable, the
                   signal is treated as already-uniform at ``fs`` and only the
                   oversampling step is applied.
    fs:            nominal frames-per-second of ``signal``.
    oversample:    output grid is ``oversample × fs`` Hz (≥1).

    Returns
    -------
    (resampled_signal, new_fs)
    """
    x = np.asarray(signal, dtype=np.float64)
    n = len(x)
    oversample = max(1, int(oversample))
    new_fs = float(fs) * oversample

    if n < 2 or fs <= 0:
        return x, float(fs)

    # Degenerate BVP (e.g. POS's 0/0 when a face is missing) can carry NaN/inf;
    # PCHIP rejects non-finite inputs, so sanitize before interpolating. A
    # zeroed signal yields no peaks downstream and the algorithm is dropped.
    if not np.all(np.isfinite(x)):
        x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)

    if timestamps_usable(timestamps_ms, n):
        t = np.asarray(timestamps_ms, dtype=np.float64) / 1000.0
        t = t - t[0]
        # Guard against any residual non-monotonic ticks before PCHIP.
        keep = np.concatenate(([True], np.diff(t) > 0))
        t, xs = t[keep], x[keep]
        if len(t) < 2:
            return x, float(fs)
        duration = t[-1]
    else:
        duration = (n - 1) / float(fs)
        t = np.linspace(0.0, duration, n)
        xs = x

    n_out = max(2, int(round(duration * new_fs)) + 1)
    grid = np.linspace(0.0, duration, n_out)
    interp = PchipInterpolator(t, xs, extrapolate=True)
    return interp(grid).astype(np.float64), new_fs
