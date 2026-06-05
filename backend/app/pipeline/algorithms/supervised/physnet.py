"""PhysNet adapter — PURE pretrained (3D-CNN encoder-decoder, CHUNK=128, 72x72, DiffNormalized)."""
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

CHUNK_LENGTH = 128
IMG_SIZE = 72


class PhysNetAdapter(AlgorithmAdapter):
    id = "PhysNet"

    def estimate_bvp(self, rgb_signal, frames, fs):
        if frames is None or len(frames) < CHUNK_LENGTH:
            raise WeightMissingError(f"PhysNet requires ≥ {CHUNK_LENGTH} face frames")

        import torch
        from neural_methods.model.PhysNet import PhysNet_padding_Encoder_Decoder_MAX

        device = get_device()
        wp = weight_path("PURE_PhysNet_DiffNormalized.pth")
        model = PhysNet_padding_Encoder_Decoder_MAX(frames=CHUNK_LENGTH).to(device)
        try:
            model.load_state_dict(load_state_dict_clean(wp, device), strict=True)
        except Exception as e:  # noqa: BLE001
            raise WeightMissingError(f"PhysNet weight load failed: {e}") from e
        model.eval()

        crops = resize_face_crops(frames, IMG_SIZE)         # (T, H, W, 3)
        diff = diff_normalize_data(crops)                   # (T, H, W, 3)

        T = diff.shape[0]
        n_chunks = T // CHUNK_LENGTH
        if n_chunks == 0:
            raise WeightMissingError("after alignment, no full chunks")
        usable = n_chunks * CHUNK_LENGTH
        diff = diff[:usable]
        # PhysNet expects (B, C, T, H, W)
        x = diff.reshape(n_chunks, CHUNK_LENGTH, IMG_SIZE, IMG_SIZE, 3)
        x = x.transpose(0, 4, 1, 2, 3).astype(np.float32)   # (n_chunks, 3, CHUNK, H, W)

        with torch.inference_mode():
            t = torch.from_numpy(np.ascontiguousarray(x)).to(device)
            rppg, *_ = model(t)                  # (n_chunks, CHUNK)
            out = rppg.cpu().numpy().reshape(-1)

        bvp = np.zeros(len(frames), dtype=np.float64)
        bvp[:usable] = out[:usable].astype(np.float64)
        return bvp
