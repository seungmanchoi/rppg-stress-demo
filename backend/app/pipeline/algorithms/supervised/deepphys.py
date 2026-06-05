"""DeepPhys adapter — UBFC-rPPG pretrained (motion+appearance dual-stream CNN, 72x72).

Chen & McDuff, "DeepPhys: Video-Based Physiological Measurement Using
Convolutional Attention Networks", ECCV 2018. The ancestor of TS-CAN: a
motion branch (frame differences) gated by an appearance branch's attention.
Unlike TS-CAN it has no Temporal Shift Module, so no frame_depth alignment.
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
    standardized_data,
    weight_path,
)

IMG_SIZE = 72  # UBFC-rPPG_DeepPhys.pth final_dense_1 = Linear(16384, 128) → 72


class DeepPhysAdapter(AlgorithmAdapter):
    id = "DeepPhys"

    def estimate_bvp(self, rgb_signal, frames, fs):
        if frames is None or len(frames) < 2:
            raise WeightMissingError("DeepPhys requires ≥ 2 face frames")

        import torch
        from neural_methods.model.DeepPhys import DeepPhys

        device = get_device()
        wp = weight_path("UBFC-rPPG_DeepPhys.pth")
        model = DeepPhys(img_size=IMG_SIZE).to(device)
        try:
            model.load_state_dict(load_state_dict_clean(wp, device), strict=True)
        except Exception as e:  # noqa: BLE001
            raise WeightMissingError(f"DeepPhys weight load failed: {e}") from e
        model.eval()

        # Same preprocessing as TS-CAN: DiffNormalized motion + Standardized appearance
        crops = resize_face_crops(frames, IMG_SIZE)
        motion = diff_normalize_data(crops)        # (T, H, W, 3)
        appearance = standardized_data(crops)      # (T, H, W, 3)
        x = np.concatenate([motion, appearance], axis=-1)  # (T, H, W, 6)
        x = x.transpose(0, 3, 1, 2).astype(np.float32)     # (T, 6, H, W)

        with torch.inference_mode():
            t = torch.from_numpy(x).contiguous().to(device)
            out = model(t).squeeze(-1).cpu().numpy()       # (T,)

        bvp = np.zeros(len(frames), dtype=np.float64)
        n = min(len(out), len(frames))
        bvp[:n] = out[:n].astype(np.float64)
        return bvp
