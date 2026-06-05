"""Supervised adapters smoke tests on synthetic pulsing frames.

Each adapter loads its pretrained weight and produces a BVP signal aligned
to the original frame count. Tests are skipped if weights are missing.
"""
from __future__ import annotations

import numpy as np
import pytest

from app.core.config import settings
from app.pipeline.algorithms.supervised.bigsmall import BigSmallAdapter
from app.pipeline.algorithms.supervised.deepphys import DeepPhysAdapter
from app.pipeline.algorithms.supervised.efficientphys import EfficientPhysAdapter
from app.pipeline.algorithms.supervised.physformer import PhysFormerAdapter
from app.pipeline.algorithms.supervised.physnet import PhysNetAdapter
from app.pipeline.algorithms.supervised.rhythmformer import RhythmFormerAdapter
from app.pipeline.algorithms.supervised.ts_can import TsCanAdapter


def _synthetic_pulsing_frames(t_frames: int = 360, hr_hz: float = 1.2) -> np.ndarray:
    rng = np.random.default_rng(0)
    frames = np.zeros((t_frames, 96, 96, 3), dtype=np.uint8)
    for i in range(t_frames):
        base = rng.random((96, 96, 3)) * 30 + 100
        pulse = 15 * np.sin(2 * np.pi * hr_hz * i / 30)
        base[:, :, 1] = np.clip(base[:, :, 1] + pulse, 0, 255)
        frames[i] = base.astype(np.uint8)
    return frames


CASES = [
    ("TS-CAN", TsCanAdapter, "UBFC-rPPG_TSCAN.pth", 200),
    ("EfficientPhys", EfficientPhysAdapter, "UBFC-rPPG_EfficientPhys.pth", 200),
    ("PhysFormer", PhysFormerAdapter, "PURE_PhysFormer_DiffNormalized.pth", 320),
    ("RhythmFormer", RhythmFormerAdapter, "PURE_RhythmFormer.pth", 320),
    ("BigSmall", BigSmallAdapter, "BP4D_BigSmall_Multitask_Fold1.pth", 60),
    ("PhysNet", PhysNetAdapter, "PURE_PhysNet_DiffNormalized.pth", 200),
    ("DeepPhys", DeepPhysAdapter, "UBFC-rPPG_DeepPhys.pth", 200),
]


@pytest.mark.parametrize("name,Cls,weight,min_nonzero", CASES, ids=[c[0] for c in CASES])
def test_supervised_adapter_runs(name, Cls, weight, min_nonzero):
    if not (settings.weights_dir / weight).exists():
        pytest.skip(f"{name} weight not downloaded")
    frames = _synthetic_pulsing_frames(t_frames=360)
    bvp = Cls().estimate_bvp(None, frames, 30)
    assert bvp.shape == (360,)
    non_zero = bvp[bvp != 0]
    assert len(non_zero) >= min_nonzero, f"{name} produced too few samples"
    assert float(np.std(non_zero)) > 0, f"{name} bvp is constant"
