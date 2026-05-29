from abc import ABC, abstractmethod

import numpy as np


class AlgorithmAdapter(ABC):
    """Adapter for an rPPG algorithm. Outputs a 1-D BVP waveform sampled at fs."""

    id: str

    @abstractmethod
    def estimate_bvp(
        self,
        rgb_signal: np.ndarray | None,
        frames: np.ndarray | None,
        fs: float,
    ) -> np.ndarray:
        """
        rgb_signal: (T, 3) mean RGB over ROI per frame (unsupervised input)
        frames:     (T, H, W, 3) face crops 0~255 uint8 (supervised input)
        fs:         frames per second
        returns:    (T,) BVP waveform (or empty if unable)
        """
        raise NotImplementedError
