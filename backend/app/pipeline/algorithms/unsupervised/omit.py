import numpy as np

from ..base import AlgorithmAdapter


class OmitAdapter(AlgorithmAdapter):
    id = "OMIT"

    def estimate_bvp(self, rgb_signal, frames, fs):
        from unsupervised_methods.methods.OMIT import OMIT

        if rgb_signal is None:
            raise ValueError("OmitAdapter requires rgb_signal")
        pseudo = rgb_signal.reshape(-1, 1, 1, 3)
        return OMIT(pseudo).astype(np.float64)
