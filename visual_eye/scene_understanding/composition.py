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
    Analyze visual balance, negative space, and horizon using edge/texture density and object distribution.
    """
    try:
        if not frames:
            return CompositionAnalysis()

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

        # 1. Visual Balance (Density of objects and edges)
        left_side = gray[:, :w//2]
        right_side = gray[:, w//2:]

        left_edges = cv2.Canny(left_side, 100, 200)
        right_edges = cv2.Canny(right_side, 100, 200)

        l_density = np.mean(left_edges)
        r_density = np.mean(right_edges)

        # Factor in objects
        l_obj_area = 0
        r_obj_area = 0
        for obj in frames[mid_idx].objects:
            cx = obj.bbox.x + obj.bbox.width / 2
            area = obj.bbox.width * obj.bbox.height
            if cx < w/2: l_obj_area += area
            else: r_obj_area += area

        # Weighted score for balance
        l_score = l_density + (l_obj_area / (w*h/2)) * 100
        r_score = r_density + (r_obj_area / (w*h/2)) * 100

        if l_score > r_score * 1.4: visual_balance = "left_heavy"
        elif r_score > l_score * 1.4: visual_balance = "right_heavy"
        else: visual_balance = "balanced"

        # 2. Negative Space (Finding the 'clearest' region)
        # Check 4 sectors
        q1 = gray[:h//2, :w//2] # top-left
        q2 = gray[:h//2, w//2:] # top-right
        q3 = gray[h//2:, :w//2] # bottom-left
        q4 = gray[h//2:, w//2:] # bottom-right

        densities = [
            ("top_left", np.mean(cv2.Canny(q1, 100, 200))),
            ("top_right", np.mean(cv2.Canny(q2, 100, 200))),
            ("bottom_left", np.mean(cv2.Canny(q3, 100, 200))),
            ("bottom_right", np.mean(cv2.Canny(q4, 100, 200)))
        ]
        densities.sort(key=lambda x: x[1])
        negative_space = densities[0][0]

        # 3. Horizon Estimation (Looking for gradient changes or lines)
        # Simple heuristic: density gradient
        top_h = np.mean(cv2.Canny(gray[:h//3, :], 100, 200))
        mid_h = np.mean(cv2.Canny(gray[h//3:2*h//3, :], 100, 200))
        bot_h = np.mean(cv2.Canny(gray[2*h//3:, :], 100, 200))

        if top_h < mid_h * 0.7: horizon = "upper_third" # Sky is usually clear
        elif bot_h < mid_h * 0.7: horizon = "lower_third" # Ground is usually more textured, unless it's water
        else: horizon = "middle"

        # 4. Busy vs Clean Scores
        busy = min(1.0, np.mean(cv2.Canny(gray, 100, 200)) / 40.0) # 40.0 is a heuristic max density
        clean = float(1.0 - busy)

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
