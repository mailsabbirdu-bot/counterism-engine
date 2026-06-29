import cv2
import numpy as np
from typing import List
try:
    from ..schema import ColorAnalysis, AnalysisFrame
except (ImportError, ValueError):
    try:
        from visual_eye.schema import ColorAnalysis, AnalysisFrame
    except ImportError:
        from schema import ColorAnalysis, AnalysisFrame

def analyze_colors(frames: List[AnalysisFrame], video_path: str) -> ColorAnalysis:
    """
    Extract dominant colors, brightness, and contrast using OpenCV.
    """
    try:
        if not frames:
            return ColorAnalysis()

        mid_idx = len(frames) // 2
        frame_idx = frames[mid_idx].frame_index

        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, img = cap.read()
        cap.release()

        if not ret:
            return ColorAnalysis()

        small = cv2.resize(img, (100, 100), interpolation=cv2.INTER_AREA)
        data = small.reshape((-1, 3)).astype(np.float32)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        K = 3
        _, labels, centers = cv2.kmeans(data, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        dominant_hex = []
        for center in centers:
            b, g, r = center.astype(int)
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            dominant_hex.append(hex_color)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray) / 255.0
        contrast = np.std(gray) / 128.0
        contrast = min(1.0, contrast)

        return ColorAnalysis(
            dominant_colors=dominant_hex,
            brightness=float(brightness),
            contrast=float(contrast)
        )

    except Exception as e:
        print(f"⚠️ Color analysis error: {e}")
        return ColorAnalysis()
