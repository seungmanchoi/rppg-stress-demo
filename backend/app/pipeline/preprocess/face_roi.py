import numpy as np

FOREHEAD = [10, 67, 297, 332, 338]
LEFT_CHEEK = [50, 101, 118, 117, 123]
RIGHT_CHEEK = [280, 330, 347, 346, 352]
LANDMARKS = FOREHEAD + LEFT_CHEEK + RIGHT_CHEEK


def _get_face_mesh():
    """Lazy-init MediaPipe FaceMesh (avoids global state at import time)."""
    import mediapipe as mp

    return mp.solutions.face_mesh.FaceMesh(
        static_image_mode=False,
        refine_landmarks=False,
        max_num_faces=1,
        min_detection_confidence=0.5,
    )


def extract_roi_signal(
    frames: np.ndarray,
    roi_crops: bool = False,
) -> tuple[np.ndarray, int, np.ndarray | None]:
    """
    frames: (T, H, W, 3) uint8 RGB
    returns: (mean RGB signal (T, 3), detected_count, optional aligned face crops (T, 72, 72, 3))
    """
    import cv2

    mesh = _get_face_mesh()
    T, H, W, _ = frames.shape
    signal = np.zeros((T, 3))
    crops = np.zeros((T, 72, 72, 3), dtype=np.uint8) if roi_crops else None
    detected = 0
    last_box: tuple[int, int, int, int] | None = None
    try:
        for i in range(T):
            res = mesh.process(frames[i])
            if not res.multi_face_landmarks:
                if i > 0:
                    signal[i] = signal[i - 1]
                if crops is not None and last_box:
                    x0, y0, x1, y1 = last_box
                    crops[i] = cv2.resize(frames[i, y0:y1, x0:x1], (72, 72))
                continue
            lms = res.multi_face_landmarks[0].landmark
            pts = np.array(
                [(int(lms[j].x * W), int(lms[j].y * H)) for j in LANDMARKS]
            )
            x0 = max(0, int(pts[:, 0].min()))
            y0 = max(0, int(pts[:, 1].min()))
            x1 = min(W, int(pts[:, 0].max()))
            y1 = min(H, int(pts[:, 1].max()))
            roi = frames[i, y0:y1, x0:x1]
            if roi.size:
                signal[i] = roi.reshape(-1, 3).mean(0)
                detected += 1
                last_box = (x0, y0, x1, y1)
                if crops is not None:
                    fx0 = max(0, x0 - (x1 - x0) // 2)
                    fy0 = max(0, y0 - (y1 - y0))
                    fx1 = min(W, x1 + (x1 - x0) // 2)
                    fy1 = min(H, y1 + (y1 - y0) // 2)
                    face_crop = frames[i, fy0:fy1, fx0:fx1]
                    if face_crop.size:
                        crops[i] = cv2.resize(face_crop, (72, 72))
    finally:
        mesh.close()
    return signal, detected, crops
