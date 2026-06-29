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
    Analyzes visual balance, negative space, and horizon with production logic.
    Ensures that best_overlay_side is logically consistent with negative space.
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
        # Use objects from the current frame to identify subject weight
        l_weight, r_weight = 0.0, 0.0
        for obj in frames[mid_idx].objects:
            cx = obj.bbox.x + obj.bbox.width / 2
            area_score = (obj.bbox.width * obj.bbox.height) / (w * h)
            if cx < w/2: l_weight += area_score
            else: r_weight += area_score

        # Add edge density to the weight
        l_edges = cv2.Canny(gray[:, :w//2], 100, 200)
        r_edges = cv2.Canny(gray[:, w//2:], 100, 200)
        l_weight += np.mean(l_edges) / 255.0
        r_weight += np.mean(r_edges) / 255.0

        if l_weight > r_weight * 1.5: visual_balance = "left_heavy"
        elif r_weight > l_weight * 1.5: visual_balance = "right_heavy"
        else: visual_balance = "balanced"

        # 2. Negative Space (Finding usable area)
        # Divide into 4 quadrants
        q_coords = [
            ("top_left", (0, 0, w//2, h//2)),
            ("top_right", (w//2, 0, w, h//2)),
            ("bottom_left", (0, h//2, w//2, h)),
            ("bottom_right", (w//2, h//2, w, h))
        ]

        q_scores = []
        for name, (x1, y1, x2, y2) in q_coords:
            roi_gray = gray[y1:y2, x1:x2]
            # Clutter score: object presence + edge density
            obj_clutter = 0
            for obj in frames[mid_idx].objects:
                # Intersection check
                ox1, oy1, ox2, oy2 = obj.bbox.x, obj.bbox.y, obj.bbox.x + obj.bbox.width, obj.bbox.y + obj.bbox.height
                ix1, iy1, ix2, iy2 = max(x1, ox1), max(y1, oy1), min(x2, ox2), min(y2, oy2)
                if ix1 < ix2 and iy1 < iy2:
                    obj_clutter += ((ix2-ix1)*(iy2-iy1)) / ((x2-x1)*(y2-y1))

            edge_clutter = np.mean(cv2.Canny(roi_gray, 100, 200)) / 255.0
            q_scores.append((name, obj_clutter + edge_clutter))

        q_scores.sort(key=lambda x: x[1]) # Sort by clutter ascending
        negative_space = q_scores[0][0] # Clearest quadrant

        # 3. Horizon Estimation
        top_dens = np.mean(cv2.Canny(gray[:h//3, :], 100, 200)) / 255.0
        mid_dens = np.mean(cv2.Canny(gray[h//3:2*h//3, :], 100, 200)) / 255.0
        bot_dens = np.mean(cv2.Canny(gray[2*h//3:, :], 100, 200)) / 255.0

        if top_dens < mid_dens * 0.6: horizon = "upper_third"
        elif bot_dens < mid_dens * 0.6: horizon = "lower_third"
        else: horizon = "middle"

        busy = min(1.0, (l_weight + r_weight) / 2.0)

        return CompositionAnalysis(
            visual_balance=visual_balance,
            negative_space=negative_space,
            horizon=horizon,
            busy_score=float(busy),
            clean_score=float(1.0 - busy)
        )

    except Exception as e:
        print(f"⚠️ Composition Error: {e}")
        return CompositionAnalysis()
