from pathlib import Path

import cv2
import numpy as np


def decode_video(path: Path, target_fps: int = 30) -> tuple[np.ndarray, float, tuple[int, int]]:
    """Decode video to RGB frames at target_fps. Returns (frames, effective_fps, (h, w)).

    Computes actual fps from per-frame timestamps because canvas.captureStream
    produces variable-fps webm where the container-level fps is unreliable.
    """
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {path}")

    raw_frames: list[np.ndarray] = []
    last_ts_ms = 0.0
    first_ts_ms: float | None = None
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        ts = cap.get(cv2.CAP_PROP_POS_MSEC)
        if first_ts_ms is None:
            first_ts_ms = ts
        last_ts_ms = ts
        raw_frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    if not raw_frames:
        raise ValueError("No frames decoded")

    duration_s = max(0.001, (last_ts_ms - (first_ts_ms or 0.0)) / 1000.0)
    actual_fps = len(raw_frames) / duration_s if duration_s > 0 else 30.0

    # If source is high-fps (>1.5× target), downsample.
    if actual_fps > target_fps * 1.5:
        stride = max(1, int(round(actual_fps / target_fps)))
        frames = raw_frames[::stride]
        effective_fps = actual_fps / stride
    else:
        frames = raw_frames
        effective_fps = actual_fps

    arr = np.stack(frames, axis=0)
    return arr, float(effective_fps), (arr.shape[1], arr.shape[2])
