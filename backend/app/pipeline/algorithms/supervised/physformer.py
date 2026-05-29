"""PhysFormer adapter — PURE pretrained (CHUNK_LENGTH=160, 128x128, DiffNormalized).

Hyperparams from configs/infer_configs/PURE_UBFC-rPPG_PHYSFORMER_BASIC.yaml:
    PATCH_SIZE=4, DIM=96, FF_DIM=144, NUM_HEADS=4, NUM_LAYERS=12, THETA=0.7
Trainer inference uses gra_sharp=2.0.
"""
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
GRA_SHARP = 2.0
DIM = 96
FF_DIM = 144
NUM_HEADS = 4
NUM_LAYERS = 12
THETA = 0.7
PATCH_SIZE = 4
DROPOUT = 0.1


class PhysFormerAdapter(AlgorithmAdapter):
    id = "PhysFormer"

    def estimate_bvp(self, rgb_signal, frames, fs):
        if frames is None or len(frames) < CHUNK_LENGTH:
            raise WeightMissingError(
                f"PhysFormer requires ≥ {CHUNK_LENGTH} face frames"
            )

        import torch
        from neural_methods.model.PhysFormer import ViT_ST_ST_Compact3_TDC_gra_sharp

        device = get_device()
        wp = weight_path("PURE_PhysFormer_DiffNormalized.pth")
        model = ViT_ST_ST_Compact3_TDC_gra_sharp(
            image_size=(CHUNK_LENGTH, IMG_SIZE, IMG_SIZE),
            patches=(PATCH_SIZE,) * 3,
            dim=DIM,
            ff_dim=FF_DIM,
            num_heads=NUM_HEADS,
            num_layers=NUM_LAYERS,
            dropout_rate=DROPOUT,
            theta=THETA,
        ).to(device)
        try:
            model.load_state_dict(load_state_dict_clean(wp, device), strict=True)
        except Exception as e:  # noqa: BLE001
            raise WeightMissingError(f"PhysFormer weight load failed: {e}") from e
        model.eval()

        # Preprocess: DiffNormalized at the original resolution, then resize
        crops = resize_face_crops(frames, IMG_SIZE)         # (T, H, W, 3)
        diff = diff_normalize_data(crops)                   # (T, H, W, 3)
        x = diff.transpose(0, 3, 1, 2).astype(np.float32)   # (T, 3, H, W)

        T = x.shape[0]
        n_chunks = T // CHUNK_LENGTH
        if n_chunks == 0:
            raise WeightMissingError("after alignment, no full chunks")
        x = x[: n_chunks * CHUNK_LENGTH]
        # Reshape to (B, 3, CHUNK_LENGTH, H, W)
        x = x.reshape(n_chunks, CHUNK_LENGTH, 3, IMG_SIZE, IMG_SIZE).transpose(0, 2, 1, 3, 4)

        with torch.inference_mode():
            t = torch.from_numpy(x).contiguous().to(device)
            rppg, _, _, _ = model(t, GRA_SHARP)
            rppg = rppg.cpu().numpy()  # (B, CHUNK_LENGTH)

        bvp = np.zeros(len(frames), dtype=np.float64)
        bvp[: n_chunks * CHUNK_LENGTH] = rppg.reshape(-1).astype(np.float64)
        return bvp
