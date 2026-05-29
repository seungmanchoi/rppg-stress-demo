import numpy as np

from ..base import AlgorithmAdapter


class PosAdapter(AlgorithmAdapter):
    id = "POS"

    def estimate_bvp(self, rgb_signal, frames, fs):
        from unsupervised_methods.methods.POS_WANG import POS_WANG

        # POS_WANG averages frames internally; pass mean-RGB as (T, 1, 1, 3) pseudo-frames
        if rgb_signal is None:
            raise ValueError("PosAdapter requires rgb_signal")
        pseudo = rgb_signal.reshape(-1, 1, 1, 3)
        return POS_WANG(pseudo, fs).astype(np.float64)
