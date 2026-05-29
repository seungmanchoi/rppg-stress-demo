from __future__ import annotations

from ..base import AlgorithmAdapter
from ._base_deep import WeightMissingError


class PhysFormerAdapter(AlgorithmAdapter):
    id = "PhysFormer"

    def estimate_bvp(self, rgb_signal, frames, fs):
        raise WeightMissingError(
            "PhysFormer adapter inference is pending implementation "
            "(weight present, dataset-specific preprocessor required)."
        )
