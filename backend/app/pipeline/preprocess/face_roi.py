"""Face ROI extraction using OpenCV Haar cascade.

Returns mean RGB signal averaged over forehead + cheek strips.
For supervised models we also return 72x72 face crops aligned per frame.
"""
from __future__ import annotations

import cv2
import numpy as np

_CASCADE: cv2.CascadeClassifier | None = None


def _cascade() -> cv2.CascadeClassifier:
    global _CASCADE
    if _CASCADE is None:
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _CASCADE = cv2.CascadeClassifier(path)
    return _CASCADE


def _strip_mean(frame: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
    """Return mean RGB over forehead band + two cheek bands inside face box."""
    forehead = frame[y : y + h // 3, x + w // 4 : x + 3 * w // 4]
    left_cheek = frame[y + h // 3 : y + 2 * h // 3, x : x + w // 3]
    right_cheek = frame[y + h // 3 : y + 2 * h // 3, x + 2 * w // 3 : x + w]
    pieces = [p.reshape(-1, 3) for p in (forehead, left_cheek, right_cheek) if p.size]
    if not pieces:
        return np.zeros(3)
    return np.concatenate(pieces, axis=0).mean(axis=0)


def extract_roi_signal(
    frames: np.ndarray,
    roi_crops: bool = False,
) -> tuple[np.ndarray, int, np.ndarray | None]:
    """
    frames: (T, H, W, 3) uint8 RGB
    returns: (signal (T, 3), detected_count, optional (T, 72, 72, 3) face crops)
    """
    T = len(frames)
    signal = np.zeros((T, 3), dtype=np.float64)
    crops = np.zeros((T, 72, 72, 3), dtype=np.uint8) if roi_crops else None
    cascade = _cascade()
    detected = 0
    last_box: tuple[int, int, int, int] | None = None

    for i in range(T):
        gray = cv2.cvtColor(frames[i], cv2.COLOR_RGB2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=4, minSize=(40, 40))
        if len(faces) > 0:
            # pick largest face
            x, y, w, h = max(faces, key=lambda b: b[2] * b[3])
            signal[i] = _strip_mean(frames[i], x, y, w, h)
            detected += 1
            last_box = (x, y, w, h)
            if crops is not None:
                face = frames[i, y : y + h, x : x + w]
                if face.size:
                    crops[i] = cv2.resize(face, (72, 72))
        else:
            if last_box and i > 0:
                signal[i] = signal[i - 1]
                if crops is not None:
                    x, y, w, h = last_box
                    H, W = frames.shape[1], frames.shape[2]
                    yy0, yy1 = max(0, y), min(H, y + h)
                    xx0, xx1 = max(0, x), min(W, x + w)
                    face = frames[i, yy0:yy1, xx0:xx1]
                    if face.size:
                        crops[i] = cv2.resize(face, (72, 72))

    return signal, detected, crops
