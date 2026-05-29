import numpy as np

from ..base import AlgorithmAdapter


class ChromAdapter(AlgorithmAdapter):
    id = "CHROM"

    def estimate_bvp(self, rgb_signal, frames, fs):
        from unsupervised_methods.methods.CHROME_DEHAAN import CHROME_DEHAAN

        if rgb_signal is None:
            raise ValueError("ChromAdapter requires rgb_signal")
        pseudo = rgb_signal.reshape(-1, 1, 1, 3)
        return CHROME_DEHAAN(pseudo, fs).astype(np.float64)
