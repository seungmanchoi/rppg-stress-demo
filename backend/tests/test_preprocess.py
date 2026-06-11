"""Preprocess unit tests using synthetic video (no real face)."""
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from app.pipeline.preprocess.frame_decoder import decode_video
from app.pipeline.preprocess.quality_gate import assess


@pytest.fixture
def synthetic_video(tmp_path: Path) -> Path:
    out = tmp_path / "synth.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out), fourcc, 30.0, (160, 120))
    rng = np.random.default_rng(0)
    for _ in range(150):
        frame = (rng.integers(0, 255, (120, 160, 3), dtype=np.uint8))
        writer.write(frame)
    writer.release()
    return out


def test_decode_video_returns_rgb_frames(synthetic_video: Path):
    frames, fps, timestamps_ms, (h, w) = decode_video(synthetic_video, target_fps=30)
    assert frames.ndim == 4 and frames.shape[-1] == 3
    assert frames.dtype == np.uint8
    assert 28 <= fps <= 32
    assert h == 120 and w == 160
    assert len(timestamps_ms) == len(frames)


def test_decode_video_missing_file_raises(tmp_path: Path):
    with pytest.raises(ValueError):
        decode_video(tmp_path / "nope.mp4")


def test_quality_gate_bright_static_synthetic(synthetic_video: Path):
    frames, _, _, _ = decode_video(synthetic_video)
    # 합성 영상 → 얼굴 0개, 노이즈 큼
    q = assess(frames, detected=0)
    assert q.detected_ratio == 0.0
    assert q.mean_brightness > 0
    assert any("얼굴 검출 비율" in w for w in q.warnings)
