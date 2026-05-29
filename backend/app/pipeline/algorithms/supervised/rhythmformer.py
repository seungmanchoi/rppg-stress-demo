from __future__ import annotations

from ..base import AlgorithmAdapter
from ._base_deep import WeightMissingError


class RhythmFormerAdapter(AlgorithmAdapter):
    id = "RhythmFormer"

    def estimate_bvp(self, rgb_signal, frames, fs):
        raise WeightMissingError(
            "RhythmFormer adapter inference is pending implementation "
            "(weight present, dataset-specific preprocessor required)."
        )
