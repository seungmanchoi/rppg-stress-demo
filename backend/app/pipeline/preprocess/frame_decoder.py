from pathlib import Path

import cv2
import numpy as np


def decode_video(path: Path, target_fps: int = 30) -> tuple[np.ndarray, float, tuple[int, int]]:
    """Decode video to RGB frames at target_fps. Returns (frames, effective_fps, (h, w))."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {path}")
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    stride = max(1, int(round(src_fps / target_fps)))
    frames: list[np.ndarray] = []
    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % stride == 0:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        idx += 1
    cap.release()
    if not frames:
        raise ValueError("No frames decoded")
    arr = np.stack(frames, axis=0)
    fps = src_fps / stride
    return arr, float(fps), (arr.shape[1], arr.shape[2])
