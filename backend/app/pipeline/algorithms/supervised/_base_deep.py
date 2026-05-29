"""Shared utilities for supervised deep-learning rPPG adapters.

These adapters wrap rPPG-Toolbox models. They share preprocessing patterns:
- standardized appearance stream
- diff-normalized motion stream
- (T, 6, H, W) concatenated tensor where applicable
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.core.config import settings


class WeightMissingError(RuntimeError):
    """Raised when a model weight file is not present locally."""


def weight_path(filename: str) -> Path:
    p = settings.weights_dir / filename
    if not p.exists() or p.stat().st_size < 1_000_000:
        raise WeightMissingError(f"weight missing: {p}")
    return p


def resize_crops(frames: np.ndarray, size: int) -> np.ndarray:
    """frames: (T, H, W, 3) uint8 → (T, size, size, 3) float32 normalized 0~1."""
    out = np.empty((len(frames), size, size, 3), dtype=np.float32)
    for i, f in enumerate(frames):
        out[i] = cv2.resize(f, (size, size)).astype(np.float32) / 255.0
    return out


def diff_normalized(frames: np.ndarray) -> np.ndarray:
    """DiffNormalized motion stream."""
    diff = np.zeros_like(frames)
    diff[1:] = (frames[1:] - frames[:-1]) / (frames[1:] + frames[:-1] + 1e-7)
    diff = (diff - diff.mean()) / (diff.std() + 1e-7)
    return diff


def standardized(frames: np.ndarray) -> np.ndarray:
    """Z-score standardized appearance stream."""
    return (frames - frames.mean()) / (frames.std() + 1e-7)


def load_state_dict_clean(weight_p: Path, device) -> dict:
    """Load .pth and strip the 'module.' DDP prefix."""
    import torch

    state = torch.load(weight_p, map_location=device, weights_only=False)
    return {k.replace("module.", ""): v for k, v in state.items()}
