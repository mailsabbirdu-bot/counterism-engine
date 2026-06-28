import numpy as np
from typing import List
from .schema import SafeTextRegion, DetectedObject

def detect_safe_text_regions(frame: np.ndarray, objects: List[DetectedObject]) -> List[SafeTextRegion]:
    """
    Identifies areas where text can appear.
    Phase 1 Heuristic: Divide frame into 9 sectors (3x3 grid) and return
    the one with the least object occupancy/complexity.
    """
    try:
        height, width = frame.shape[:2]
        sectors = []

        # Define a 3x3 grid
        for row in range(3):
            for col in range(3):
                sect_x = col * (width // 3)
                sect_y = row * (height // 3)
                sect_w = width // 3
                sect_h = height // 3

                # Check for object overlap
                overlap_score = 0
                for obj in objects:
                    # Simple AABB overlap check
                    if not (obj.bbox.x > sect_x + sect_w or
                            obj.bbox.x + obj.bbox.width < sect_x or
                            obj.bbox.y > sect_y + sect_h or
                            obj.bbox.y + obj.bbox.height < sect_y):
                        overlap_score += obj.confidence

                sectors.append({
                    "region": SafeTextRegion(
                        x=sect_x + 50, # Margin
                        y=sect_y + 50,
                        width=sect_w - 100,
                        height=sect_h - 100,
                        confidence=1.0 - min(overlap_score, 1.0)
                    ),
                    "score": overlap_score
                })

        # Sort by overlap score (ascending) and return regions
        sectors.sort(key=lambda s: s["score"])
        return [s["region"] for s in sectors if s["region"].confidence > 0.5]

    except Exception as e:
        print(f"Safe zone detection error: {e}")
        return [SafeTextRegion(x=100, y=100, width=500, height=300, confidence=0.85)]
