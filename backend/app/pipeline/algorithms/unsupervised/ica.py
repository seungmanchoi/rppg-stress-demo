import numpy as np

from ..base import AlgorithmAdapter


class IcaAdapter(AlgorithmAdapter):
    """ICA (Poh-McDuff-Picard) — independent component analysis on RGB.

    Poh, McDuff & Picard, "Non-contact, automated cardiac pulse measurements
    using video imaging and blind source separation", Optics Express 2010.
    JADE/FastICA separates the 3 RGB channels into independent sources; the
    component whose spectral peak lies in the cardiac band is taken as the BVP.
    """

    id = "ICA"

    def estimate_bvp(self, rgb_signal, frames, fs):
        from unsupervised_methods.methods.ICA_POH import ICA_POH

        if rgb_signal is None:
            raise ValueError("IcaAdapter requires rgb_signal")
        pseudo = rgb_signal.reshape(-1, 1, 1, 3)
        return ICA_POH(pseudo, fs).astype(np.float64)
