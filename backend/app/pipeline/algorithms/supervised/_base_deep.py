"""Shared helpers for supervised deep-learning rPPG adapters.

Pre-processing formulas mirror rPPG-Toolbox's
`BaseLoader.diff_normalize_data` / `BaseLoader.standardized_data` exactly so
pretrained weights see the same input distribution.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.core.config import settings


class WeightMissingError(RuntimeError):
    """Raised when a model weight file is not present or fails to load."""


def weight_path(filename: str) -> Path:
    p = settings.weights_dir / filename
    if not p.exists() or p.stat().st_size < 1_000_000:
        raise WeightMissingError(f"weight missing: {p}")
    return p


def resize_face_crops(frames: np.ndarray, size: int) -> np.ndarray:
    """(T, H, W, 3) uint8 → (T, size, size, 3) float32 in [0, 1]."""
    out = np.empty((len(frames), size, size, 3), dtype=np.float32)
    for i, f in enumerate(frames):
        out[i] = cv2.resize(f, (size, size)).astype(np.float32) / 255.0
    return out


def diff_normalize_data(data: np.ndarray) -> np.ndarray:
    """rPPG-Toolbox BaseLoader.diff_normalize_data formula:
        d[j] = (x[j+1] - x[j]) / (x[j+1] + x[j] + 1e-7)
        d   /= std(d)
        d append one zero frame at tail (preserves T)
    """
    n = data.shape[0]
    if n < 2:
        return np.zeros_like(data)
    out = np.zeros((n - 1, *data.shape[1:]), dtype=np.float32)
    for j in range(n - 1):
        out[j] = (data[j + 1] - data[j]) / (data[j + 1] + data[j] + 1e-7)
    std = float(np.std(out))
    if std > 1e-12:
        out = out / std
    out = np.concatenate([out, np.zeros((1, *data.shape[1:]), dtype=np.float32)], axis=0)
    out[np.isnan(out)] = 0
    return out


def standardized_data(data: np.ndarray) -> np.ndarray:
    """Z-score over the entire tensor (matches rPPG-Toolbox)."""
    mean = float(np.mean(data))
    std = float(np.std(data)) or 1.0
    out = ((data - mean) / std).astype(np.float32)
    out[np.isnan(out)] = 0
    return out


def load_state_dict_clean(weight_p: Path, device) -> dict:
    """Load .pth and strip the 'module.' DDP prefix."""
    import torch

    state = torch.load(weight_p, map_location=device, weights_only=False)
    return {k.replace("module.", ""): v for k, v in state.items()}


def round_down_to_multiple(n: int, m: int) -> int:
    return (n // m) * m
