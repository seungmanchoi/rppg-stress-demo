from __future__ import annotations

from ..base import AlgorithmAdapter
from ._base_deep import WeightMissingError


class EfficientPhysAdapter(AlgorithmAdapter):
    id = "EfficientPhys"

    def estimate_bvp(self, rgb_signal, frames, fs):
        raise WeightMissingError(
            "EfficientPhys adapter inference is pending — "
            "frame_depth-aware reshape required per UBFC-rPPG training."
        )
