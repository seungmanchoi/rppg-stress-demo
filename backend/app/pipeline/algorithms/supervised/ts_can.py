"""TS-CAN adapter — matches UBFC-rPPG pretrained config (img_size=72, frame_depth=20)."""
from __future__ import annotations

import numpy as np

from ..base import AlgorithmAdapter
from . import get_device
from ._base_deep import (
    WeightMissingError,
    diff_normalize_data,
    load_state_dict_clean,
    resize_face_crops,
    round_down_to_multiple,
    standardized_data,
    weight_path,
)

FRAME_DEPTH = 20
IMG_SIZE = 72  # inferred from final_dense_1.weight shape (128, 16384) → 8x8x64x4


class TsCanAdapter(AlgorithmAdapter):
    id = "TS-CAN"

    def estimate_bvp(self, rgb_signal, frames, fs):
        if frames is None or len(frames) < FRAME_DEPTH:
            raise WeightMissingError("TS-CAN requires at least 20 face frames")

        import torch
        from neural_methods.model.TS_CAN import TSCAN

        device = get_device()
        wp = weight_path("UBFC-rPPG_TSCAN.pth")
        model = TSCAN(frame_depth=FRAME_DEPTH, img_size=IMG_SIZE).to(device)
        try:
            model.load_state_dict(load_state_dict_clean(wp, device), strict=True)
        except Exception as e:  # noqa: BLE001
            raise WeightMissingError(f"TS-CAN weight load failed: {e}") from e
        model.eval()

        # Preprocess — rPPG-Toolbox standard: DiffNormalized (motion) + Standardized (raw)
        crops = resize_face_crops(frames, IMG_SIZE)
        motion = diff_normalize_data(crops)        # (T, H, W, 3)
        appearance = standardized_data(crops)      # (T, H, W, 3)
        # Stack: input expects (T, 6, H, W) — first 3 = motion, last 3 = appearance
        x = np.concatenate([motion, appearance], axis=-1)  # (T, H, W, 6)
        x = x.transpose(0, 3, 1, 2).astype(np.float32)     # (T, 6, H, W)

        # Truncate to multiple of FRAME_DEPTH (TSM segment alignment)
        usable = round_down_to_multiple(x.shape[0], FRAME_DEPTH)
        if usable == 0:
            raise WeightMissingError("after alignment, not enough frames")
        x = x[:usable]

        with torch.inference_mode():
            t = torch.from_numpy(x).contiguous().to(device)
            out = model(t).squeeze(-1).cpu().numpy()

        # Pad back to original length with zeros so downstream HRV gets a T-long signal
        bvp = np.zeros(len(frames), dtype=np.float64)
        bvp[:usable] = out.astype(np.float64)
        return bvp
