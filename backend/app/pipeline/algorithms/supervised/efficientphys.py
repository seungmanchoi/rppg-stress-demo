"""EfficientPhys adapter — UBFC-rPPG pretrained (img_size=72, frame_depth=20)."""
from __future__ import annotations

import numpy as np

from ..base import AlgorithmAdapter
from . import get_device
from ._base_deep import (
    WeightMissingError,
    load_state_dict_clean,
    resize_face_crops,
    round_down_to_multiple,
    standardized_data,
    weight_path,
)

FRAME_DEPTH = 20
IMG_SIZE = 72


class EfficientPhysAdapter(AlgorithmAdapter):
    id = "EfficientPhys"

    def estimate_bvp(self, rgb_signal, frames, fs):
        if frames is None or len(frames) < FRAME_DEPTH + 1:
            raise WeightMissingError("EfficientPhys requires at least 21 face frames")

        import torch
        from neural_methods.model.EfficientPhys import EfficientPhys

        device = get_device()
        wp = weight_path("UBFC-rPPG_EfficientPhys.pth")
        model = EfficientPhys(frame_depth=FRAME_DEPTH, img_size=IMG_SIZE).to(device)
        try:
            model.load_state_dict(load_state_dict_clean(wp, device), strict=True)
        except Exception as e:  # noqa: BLE001
            raise WeightMissingError(f"EfficientPhys weight load failed: {e}") from e
        model.eval()

        # EfficientPhys does `torch.diff(dim=0)` + BatchNorm internally
        # So input is standardized raw frames (T, 3, H, W)
        crops = resize_face_crops(frames, IMG_SIZE)
        std_crops = standardized_data(crops)                    # (T, H, W, 3)
        x = std_crops.transpose(0, 3, 1, 2).astype(np.float32)  # (T, 3, H, W)

        # Truncate to multiple of FRAME_DEPTH; need one extra frame because of internal diff
        usable = round_down_to_multiple(x.shape[0] - 1, FRAME_DEPTH)
        if usable == 0:
            raise WeightMissingError("after alignment, not enough frames")
        x = x[: usable + 1]  # diff will yield `usable` outputs

        with torch.inference_mode():
            t = torch.from_numpy(x).contiguous().to(device)
            out = model(t).squeeze(-1).cpu().numpy()

        bvp = np.zeros(len(frames), dtype=np.float64)
        bvp[:usable] = out[:usable].astype(np.float64)
        return bvp
