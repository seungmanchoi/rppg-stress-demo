from dataclasses import dataclass

import numpy as np


@dataclass
class Poincare:
    sd1: float
    sd2: float


def poincare(ibi_ms: np.ndarray) -> Poincare:
    if len(ibi_ms) < 3:
        return Poincare(0.0, 0.0)
    x1, x2 = ibi_ms[:-1], ibi_ms[1:]
    sd1 = float(np.std(x2 - x1) / np.sqrt(2))
    sd2 = float(np.std(x2 + x1) / np.sqrt(2))
    return Poincare(sd1, sd2)
