"""BigSmall adapter — BP4D pretrained (n_segment=3, BIG=144x144 Std, SMALL=9x9 DiffN).

Multi-task model: outputs BVP, Respiration, AU. We expose BVP and tuck respiration
into `extras` (rate computation done downstream if non-zero).
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
    round_down_to_multiple,
    standardized_data,
    weight_path,
)

N_SEGMENT = 3
BIG_SIZE = 144
SMALL_SIZE = 9


class BigSmallAdapter(AlgorithmAdapter):
    id = "BigSmall"

    def estimate_bvp(self, rgb_signal, frames, fs):
        if frames is None or len(frames) < N_SEGMENT:
            raise WeightMissingError("BigSmall requires ≥ 3 face frames")

        import torch
        from neural_methods.model.BigSmall import BigSmall

        device = get_device()
        wp = weight_path("BP4D_BigSmall_Multitask_Fold1.pth")
        model = BigSmall(n_segment=N_SEGMENT).to(device)
        try:
            model.load_state_dict(load_state_dict_clean(wp, device), strict=True)
        except Exception as e:  # noqa: BLE001
            raise WeightMissingError(f"BigSmall weight load failed: {e}") from e
        model.eval()

        big = resize_face_crops(frames, BIG_SIZE)          # (T, 144, 144, 3)
        small = resize_face_crops(frames, SMALL_SIZE)      # (T, 9, 9, 3)
        big = standardized_data(big)
        small = diff_normalize_data(small)

        big_t = big.transpose(0, 3, 1, 2).astype(np.float32)      # (T, 3, 144, 144)
        small_t = small.transpose(0, 3, 1, 2).astype(np.float32)  # (T, 3, 9, 9)

        usable = round_down_to_multiple(big_t.shape[0], N_SEGMENT)
        if usable == 0:
            raise WeightMissingError("after alignment, not enough frames")
        big_t = big_t[:usable]
        small_t = small_t[:usable]

        with torch.inference_mode():
            tb = torch.from_numpy(big_t).contiguous().to(device)
            ts = torch.from_numpy(small_t).contiguous().to(device)
            # BigSmall.forward returns (au_out, bvp_out, resp_out)
            _au, bvp_out, _resp = model([tb, ts])
            bvp_arr = bvp_out.squeeze(-1).cpu().numpy()

        bvp = np.zeros(len(frames), dtype=np.float64)
        bvp[:usable] = bvp_arr[:usable].astype(np.float64)
        return bvp
