import cv2
import numpy as np
from typing import List, Dict, Any
try:
    from ..schema import CompositionAnalysis, AnalysisFrame, DetectedObject
except (ImportError, ValueError):
    try:
        from visual_eye.schema import CompositionAnalysis, AnalysisFrame, DetectedObject
    except ImportError:
        from schema import CompositionAnalysis, AnalysisFrame, DetectedObject

def analyze_composition(frames: List[AnalysisFrame], video_path: str) -> CompositionAnalysis:
    """
    Analyze visual balance, negative space, and busy/clean scores.
    """
    try:
        if not frames:
            return CompositionAnalysis()

        # Use a middle frame for detailed image-based analysis
        mid_idx = len(frames) // 2
        frame_idx = frames[mid_idx].frame_index

        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, img = cap.read()
        cap.release()

        if not ret:
            return CompositionAnalysis()

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 1. Visual Balance (Left vs Right occupancy)
        # Use objects from the selected frame
        left_occ = 0
        right_occ = 0
        for obj in frames[mid_idx].objects:
            cx = obj.bbox.x + obj.bbox.width / 2
            area = obj.bbox.width * obj.bbox.height
            if cx < w/2: left_occ += area
            else: right_occ += area

        if left_occ > right_occ * 1.5: visual_balance = "left_heavy"
        elif right_occ > left_occ * 1.5: visual_balance = "right_heavy"
        else: visual_balance = "balanced"

        # 2. Negative Space
        # Divide into 3 vertical strips
        left_strip = clutter_score(gray[:, :w//3])
        mid_strip = clutter_score(gray[:, w//3:2*w//3])
        right_strip = clutter_score(gray[:, 2*w//3:])

        strips = [("left", left_strip), ("center", mid_strip), ("right", right_strip)]
        strips.sort(key=lambda x: x[1]) # Sort by clutter ascending
        negative_space = strips[0][0] # Strip with least clutter

        # 3. Horizon Estimation
        # Check edge density in horizontal strips
        top_h = clutter_score(gray[:h//3, :])
        mid_h = clutter_score(gray[h//3:2*h//3, :])
        bot_h = clutter_score(gray[2*h//3:, :])

        if top_h < mid_h and top_h < bot_h: horizon = "upper_third"
        elif bot_h < mid_h and bot_h < top_h: horizon = "lower_third"
        else: horizon = "middle"

        # 4. Busy vs Clean Scores
        busy = clutter_score(gray)
        clean = 1.0 - busy

        return CompositionAnalysis(
            visual_balance=visual_balance,
            negative_space=negative_space,
            horizon=horizon,
            busy_score=float(busy),
            clean_score=float(clean)
        )

    except Exception as e:
        print(f"⚠️ Composition analysis error: {e}")
        return CompositionAnalysis()

def clutter_score(img_gray: np.ndarray) -> float:
    """
    Calculate a clutter score based on edge density.
    """
    edges = cv2.Canny(img_gray, 100, 200)
    density = np.mean(edges) / 255.0
    # Normalize to a reasonable range
    score = min(1.0, density * 5.0)
    return score
