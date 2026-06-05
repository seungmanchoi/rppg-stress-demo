import numpy as np

from ..base import AlgorithmAdapter


class GreenAdapter(AlgorithmAdapter):
    """GREEN — the original rPPG method: just the green channel detrended.

    Verkruysse, Svaasand & Nelson, "Remote plethysmographic imaging using
    ambient light", Optics Express 2008. Hemoglobin absorbs green light most
    strongly, so the green channel alone carries the strongest pulse signature.
    """

    id = "GREEN"

    def estimate_bvp(self, rgb_signal, frames, fs):
        from unsupervised_methods.methods.GREEN import GREEN

        if rgb_signal is None:
            raise ValueError("GreenAdapter requires rgb_signal")
        pseudo = rgb_signal.reshape(-1, 1, 1, 3)
        return GREEN(pseudo).astype(np.float64)
