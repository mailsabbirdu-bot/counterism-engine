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
    Extract dominant colors, brightness, and contrast by sampling frames and using K-means.
    """
    try:
        if not frames:
            return ColorAnalysis()

        # Sample up to 3 frames (start, middle, end) for a better average
        indices = [0, len(frames)//2, len(frames)-1]
        indices = sorted(list(set([i for i in indices if i < len(frames)])))

        all_centers = []
        all_brightness = []
        all_contrast = []

        cap = cv2.VideoCapture(video_path)

        for idx in indices:
            frame_idx = frames[idx].frame_index
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, img = cap.read()
            if not ret: continue

            # 1. K-Means for dominant colors
            small = cv2.resize(img, (80, 80), interpolation=cv2.INTER_AREA)
            data = small.reshape((-1, 3)).astype(np.float32)

            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, labels, centers = cv2.kmeans(data, 3, None, criteria, 5, cv2.KMEANS_RANDOM_CENTERS)
            all_centers.extend(centers)

            # 2. Stats
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            all_brightness.append(np.mean(gray) / 255.0)
            all_contrast.append(np.std(gray) / 128.0)

        cap.release()

        if not all_centers:
            return ColorAnalysis()

        # Consolidate centers for final top colors
        final_data = np.array(all_centers).astype(np.float32)
        _, _, top_centers = cv2.kmeans(final_data, 3, None, criteria, 5, cv2.KMEANS_RANDOM_CENTERS)

        dominant_hex = []
        for center in top_centers:
            b, g, r = center.astype(int)
            dominant_hex.append(f"#{r:02x}{g:02x}{b:02x}")

        return ColorAnalysis(
            dominant_colors=dominant_hex,
            brightness=float(np.mean(all_brightness)),
            contrast=float(min(1.0, np.mean(all_contrast)))
        )

    except Exception as e:
        print(f"⚠️ Color analysis error: {e}")
        return ColorAnalysis()
