def tracking_score(detected_frames: int, total_frames: int) -> float:
    return float(detected_frames / total_frames) if total_frames else 0.0
