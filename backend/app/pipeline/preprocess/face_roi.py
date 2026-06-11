"""Face ROI extraction using OpenCV Haar cascade.

Returns mean RGB signal averaged over forehead + cheek strips.
For supervised models we also return 72x72 face crops aligned per frame.

Three robustness measures matter for camera rPPG:
- The detection box is smoothed over time (EMA). Per-frame Haar boxes jitter by
  several pixels; an unsmoothed ROI samples slightly different skin each frame,
  injecting motion artefacts straight into the colour signal.
- Frames where no face is found are left as NaN and linearly interpolated
  afterwards, instead of copying the previous sample. Copy-hold creates flat
  plateaus that masquerade as low-frequency (LF) power and corrupt LF/HF.
- Within the ROI we keep only skin-like, well-exposed pixels (drop shadow,
  eyebrows/hair and specular highlights) before averaging.
"""
from __future__ import annotations

import cv2
import numpy as np

_CASCADE: cv2.CascadeClassifier | None = None
_BOX_EMA = 0.35  # weight of the newest detection in the smoothed box


def _cascade() -> cv2.CascadeClassifier:
    global _CASCADE
    if _CASCADE is None:
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _CASCADE = cv2.CascadeClassifier(path)
    return _CASCADE


def _skin_mean(region: np.ndarray) -> np.ndarray | None:
    """Mean RGB over skin-like, well-exposed pixels of a face region."""
    if region.size == 0:
        return None
    pix = region.reshape(-1, 3).astype(np.float64)
    r, g, b = pix[:, 0], pix[:, 1], pix[:, 2]
    bright = pix.mean(axis=1)
    # Exposure gate: drop near-black (shadow/hair/brows) and near-saturated pixels,
    # plus the per-region brightness extremes.
    lo, hi = np.percentile(bright, [12.0, 96.0])
    exposed = (bright > 30.0) & (bright < 245.0) & (bright >= lo) & (bright <= hi)
    # Loose skin-tone rule (illumination-tolerant): warm channel ordering R≥G≥B.
    skin = (r >= g) & (g >= b * 0.85) & (r > 50.0)
    sel = exposed & skin
    if sel.sum() < 0.2 * len(pix):
        sel = exposed  # skin rule too strict for this lighting → fall back
    if sel.sum() == 0:
        return pix.mean(axis=0)
    return pix[sel].mean(axis=0)


def _strip_mean(frame: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
    """Return mean RGB over forehead band + two cheek bands inside face box."""
    H, W = frame.shape[0], frame.shape[1]
    x0, x1 = max(0, x), min(W, x + w)
    y0, y1 = max(0, y), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return np.zeros(3)
    box = frame[y0:y1, x0:x1]
    bh, bw = box.shape[0], box.shape[1]
    forehead = box[0 : bh // 3, bw // 4 : 3 * bw // 4]
    left_cheek = box[bh // 3 : 2 * bh // 3, 0 : bw // 3]
    right_cheek = box[bh // 3 : 2 * bh // 3, 2 * bw // 3 : bw]
    means = [m for m in (_skin_mean(p) for p in (forehead, left_cheek, right_cheek)) if m is not None]
    if not means:
        return np.zeros(3)
    return np.mean(means, axis=0)


def _interp_nan_rows(signal: np.ndarray) -> np.ndarray:
    """Linearly interpolate frames flagged NaN (no detection) per channel."""
    T = len(signal)
    idx = np.arange(T)
    for c in range(signal.shape[1]):
        col = signal[:, c]
        nan = np.isnan(col)
        if nan.all():
            col[:] = 0.0
        elif nan.any():
            col[nan] = np.interp(idx[nan], idx[~nan], col[~nan])
        signal[:, c] = col
    return signal


def extract_roi_signal(
    frames: np.ndarray,
    roi_crops: bool = False,
) -> tuple[np.ndarray, int, np.ndarray | None]:
    """
    frames: (T, H, W, 3) uint8 RGB
    returns: (signal (T, 3), detected_count, optional (T, 72, 72, 3) face crops)
    """
    T = len(frames)
    signal = np.full((T, 3), np.nan, dtype=np.float64)
    crops = np.zeros((T, 72, 72, 3), dtype=np.uint8) if roi_crops else None
    cascade = _cascade()
    detected = 0
    smooth_box: np.ndarray | None = None  # (x, y, w, h) float, EMA-smoothed

    for i in range(T):
        gray = cv2.cvtColor(frames[i], cv2.COLOR_RGB2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=4, minSize=(40, 40))
        if len(faces) > 0:
            x, y, w, h = max(faces, key=lambda b: b[2] * b[3])
            new_box = np.array([x, y, w, h], dtype=np.float64)
            smooth_box = (
                new_box if smooth_box is None
                else _BOX_EMA * new_box + (1 - _BOX_EMA) * smooth_box
            )
            detected += 1
            sx, sy, sw, sh = (int(round(v)) for v in smooth_box)
            signal[i] = _strip_mean(frames[i], sx, sy, sw, sh)
            if crops is not None:
                H, W = frames.shape[1], frames.shape[2]
                face = frames[i, max(0, sy) : min(H, sy + sh), max(0, sx) : min(W, sx + sw)]
                if face.size:
                    crops[i] = cv2.resize(face, (72, 72))
        elif smooth_box is not None and crops is not None:
            sx, sy, sw, sh = (int(round(v)) for v in smooth_box)
            H, W = frames.shape[1], frames.shape[2]
            face = frames[i, max(0, sy) : min(H, sy + sh), max(0, sx) : min(W, sx + sw)]
            if face.size:
                crops[i] = cv2.resize(face, (72, 72))
        # frames with no detection keep NaN in `signal` and are interpolated below

    signal = _interp_nan_rows(signal)
    return signal, detected, crops
