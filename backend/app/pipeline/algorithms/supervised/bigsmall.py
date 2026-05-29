from __future__ import annotations

from ..base import AlgorithmAdapter
from ._base_deep import WeightMissingError


class BigSmallAdapter(AlgorithmAdapter):
    id = "BigSmall"

    def estimate_bvp(self, rgb_signal, frames, fs):
        raise WeightMissingError(
            "BigSmall adapter inference is pending implementation "
            "(weight present, multitask preprocessor required)."
        )
