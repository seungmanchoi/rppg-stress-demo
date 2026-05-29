from dataclasses import dataclass, field

import cv2
import numpy as np


@dataclass
class QualityReport:
    detected_ratio: float
    mean_brightness: float
    mean_motion_px: float
    warnings: list[str] = field(default_factory=list)


def assess(frames: np.ndarray, detected: int) -> QualityReport:
    total = len(frames)
    ratio = detected / total if total else 0.0
    brightness = float(frames.mean())

    flow_mags: list[float] = []
    grays = [cv2.cvtColor(frames[i], cv2.COLOR_RGB2GRAY) for i in range(0, total, 5)]
    for a, b in zip(grays, grays[1:]):
        flow = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        flow_mags.append(float(np.linalg.norm(flow, axis=-1).mean()))
    motion = float(np.mean(flow_mags)) if flow_mags else 0.0

    warnings: list[str] = []
    if ratio < 0.7:
        warnings.append(f"얼굴 검출 비율 낮음: {ratio:.0%}")
    if brightness < 50:
        warnings.append("영상이 어두움")
    if motion > 3:
        warnings.append("움직임 큼")

    return QualityReport(ratio, brightness, motion, warnings)
