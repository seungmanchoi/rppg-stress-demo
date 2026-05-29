import numpy as np
import pytest

from app.pipeline.algorithms.unsupervised.chrom import ChromAdapter
from app.pipeline.algorithms.unsupervised.omit import OmitAdapter
from app.pipeline.algorithms.unsupervised.pos import PosAdapter


def _synth_signal(seconds: int = 30, fs: int = 30, hr_hz: float = 1.2):
    rng = np.random.default_rng(0)
    t = np.arange(0, seconds, 1 / fs)
    pulse = 4 * np.sin(2 * np.pi * hr_hz * t)
    base_rgb = np.array([120, 100, 90])
    weight = np.array([1.0, 1.3, 0.7])
    signal = base_rgb + pulse[:, None] * weight + rng.normal(0, 1, (len(t), 3))
    return signal.astype(np.float64), fs


@pytest.mark.parametrize("adapter_cls", [PosAdapter, ChromAdapter, OmitAdapter])
def test_unsup_adapter_returns_bvp(adapter_cls):
    sig, fs = _synth_signal()
    bvp = adapter_cls().estimate_bvp(sig, None, fs)
    assert bvp.ndim == 1
    assert len(bvp) > 0
    assert float(np.std(bvp)) > 0
