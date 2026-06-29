import cv2
import numpy as np
from typing import List
try:
    from .schema import SafeTextRegion, DetectedObject
except ImportError:
    from schema import SafeTextRegion, DetectedObject

def detect_safe_text_regions(frame: np.ndarray, objects: List[DetectedObject]) -> List[SafeTextRegion]:
    """
    Identifies safe areas for text using edge density and object occupancy.
    Replaces the simple 3x3 grid with a multi-signal clutter analysis.
    """
    try:
        height, width = frame.shape[:2]

        # 1. Edge density map (Visual Clutter)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)

        # 2. Object occupancy map
        occupancy = np.zeros((height, width), dtype=np.float32)
        for obj in objects:
            x = int(obj.bbox.x)
            y = int(obj.bbox.y)
            w = int(obj.bbox.width)
            h = int(obj.bbox.height)
            # Add confidence weight to the occupancy map
            occupancy[max(0, y):min(height, y+h), max(0, x):min(width, x+w)] += obj.confidence

        # 3. Combine signals: Higher edges/occupancy = less safe
        # Normalize edges to 0-1
        edge_density = edges.astype(np.float32) / 255.0
        clutter_map = edge_density + occupancy

        # 4. Evaluate candidate regions
        # We still use a grid-based sampling for candidates, but with higher resolution
        # and more intelligent scoring.
        candidates = []
        rows, cols = 4, 4
        sect_w, sect_h = width // cols, height // rows

        for r in range(rows):
            for c in range(cols):
                x_start, y_start = c * sect_w, r * sect_h

                # ROI for the current sector
                roi_clutter = clutter_map[y_start:y_start+sect_h, x_start:x_start+sect_w]

                # Score is inverse of mean clutter
                mean_clutter = np.mean(roi_clutter)
                # Confidence starts at 1.0 and drops based on clutter
                confidence = max(0.0, 1.0 - (mean_clutter * 2.0))

                # Also consider brightness/contrast for legibility (optional enhancement)
                roi_gray = gray[y_start:y_start+sect_h, x_start:x_start+sect_w]
                std_dev = np.std(roi_gray)
                if std_dev < 10: # Very uniform region (good for text)
                    confidence = min(1.0, confidence + 0.1)

                candidates.append(SafeTextRegion(
                    x=float(x_start + 20),
                    y=float(y_start + 20),
                    width=float(sect_w - 40),
                    height=float(sect_h - 40),
                    confidence=float(confidence)
                ))

        # Sort by confidence descending
        candidates.sort(key=lambda x: x.confidence, reverse=True)

        # Return regions with at least some confidence
        return [c for c in candidates if c.confidence > 0.3]

    except Exception as e:
        print(f"⚠️ Safe zone detection error: {e}")
        # Robust fallback
        return [SafeTextRegion(x=width*0.1, y=height*0.1, width=width*0.8, height=height*0.2, confidence=0.5)]
