"""RhythmFormer adapter — PURE pretrained (CHUNK_LENGTH=160, 128x128)."""
from __future__ import annotations

import numpy as np

from ..base import AlgorithmAdapter
from . import get_device
from ._base_deep import (
    WeightMissingError,
    diff_normalize_data,
    load_state_dict_clean,
    resize_face_crops,
    weight_path,
)

CHUNK_LENGTH = 160
IMG_SIZE = 128


class RhythmFormerAdapter(AlgorithmAdapter):
    id = "RhythmFormer"

    def estimate_bvp(self, rgb_signal, frames, fs):
        if frames is None or len(frames) < CHUNK_LENGTH:
            raise WeightMissingError(
                f"RhythmFormer requires ≥ {CHUNK_LENGTH} face frames"
            )

        import torch
        from neural_methods.model.RhythmFormer import RhythmFormer

        device = get_device()
        wp = weight_path("PURE_RhythmFormer.pth")
        model = RhythmFormer().to(device)
        try:
            model.load_state_dict(load_state_dict_clean(wp, device), strict=True)
        except Exception as e:  # noqa: BLE001
            raise WeightMissingError(f"RhythmFormer weight load failed: {e}") from e
        model.eval()

        crops = resize_face_crops(frames, IMG_SIZE)         # (T, H, W, 3)
        diff = diff_normalize_data(crops)                   # (T, H, W, 3)
        x = diff.transpose(0, 3, 1, 2).astype(np.float32)   # (T, 3, H, W)

        T = x.shape[0]
        n_chunks = T // CHUNK_LENGTH
        if n_chunks == 0:
            raise WeightMissingError("after alignment, no full chunks")
        x = x[: n_chunks * CHUNK_LENGTH]
        # RhythmFormer expects (N, D, C, H, W)
        x = x.reshape(n_chunks, CHUNK_LENGTH, 3, IMG_SIZE, IMG_SIZE)

        with torch.inference_mode():
            t = torch.from_numpy(x).contiguous().to(device)
            out = model(t).cpu().numpy()  # (N, D) or (N, 1, D)
        out = out.reshape(n_chunks, -1)

        bvp = np.zeros(len(frames), dtype=np.float64)
        flat = out.reshape(-1)[: n_chunks * CHUNK_LENGTH]
        bvp[: len(flat)] = flat.astype(np.float64)
        return bvp
