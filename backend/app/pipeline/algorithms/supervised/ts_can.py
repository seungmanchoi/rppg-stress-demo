from __future__ import annotations

from ..base import AlgorithmAdapter
from ._base_deep import WeightMissingError


class TsCanAdapter(AlgorithmAdapter):
    id = "TS-CAN"

    def estimate_bvp(self, rgb_signal, frames, fs):
        raise WeightMissingError(
            "TS-CAN adapter inference is pending — UBFC-rPPG preprocessor "
            "chunking (frame_depth=20, 36x36 crops) must match training config."
        )
