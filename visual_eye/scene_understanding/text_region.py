import cv2
import numpy as np
from typing import List
try:
    from ..schema import AnalysisFrame, RecommendedTextRegion, SafeTextRegion
except (ImportError, ValueError):
    try:
        from visual_eye.schema import AnalysisFrame, RecommendedTextRegion, SafeTextRegion
    except ImportError:
        from schema import AnalysisFrame, RecommendedTextRegion, SafeTextRegion

def recommend_text_region(frames: List[AnalysisFrame], video_path: str) -> RecommendedTextRegion:
    """
    Production-grade Organic Safe Zone detection.
    Replaces grid-based logic with an empty-space heatmap and continuous area finding.
    """
    try:
        if not frames:
            return RecommendedTextRegion(x=100, y=100, width=500, height=300, confidence=0.5, stability=0.0)

        # 1. Accumulate an occupancy mask across all sampled frames
        # Use low-res for speed: 480x270 (1/4 of 1080p)
        h_low, w_low = 270, 480
        master_mask = np.zeros((h_low, w_low), dtype=np.float32)

        # Step size for processing images (don't read too many)
        stride = max(1, len(frames) // 5)
        cap = cv2.VideoCapture(video_path)

        for i in range(0, len(frames), stride):
            f_info = frames[i]
            cap.set(cv2.CAP_PROP_POS_FRAMES, f_info.frame_index)
            ret, img = cap.read()
            if not ret: continue

            # Grayscale edge detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            edges_low = cv2.resize(edges, (w_low, h_low), interpolation=cv2.INTER_AREA)

            # Object masks
            obj_mask = np.zeros((h_low, w_low), dtype=np.float32)
            for obj in f_info.objects:
                x1, y1 = int(obj.bbox.x * w_low / 1920), int(obj.bbox.y * h_low / 1080)
                x2, y2 = int((obj.bbox.x + obj.bbox.width) * w_low / 1920), int((obj.bbox.y + obj.bbox.height) * h_low / 1080)
                # Expand object mask slightly for safety buffer
                cv2.rectangle(obj_mask, (x1-10, y1-10), (x2+10, y2+10), 1.0, -1)

            # Combine current frame clutter (edges + objects)
            frame_clutter = (edges_low / 255.0) + obj_mask
            master_mask += frame_clutter

        cap.release()

        # 2. Normalize and invert to find negative space
        # Areas with low master_mask score are stable negative space
        master_mask /= (len(frames) / stride)
        safe_heatmap = 1.0 - np.clip(master_mask, 0, 1)

        # 3. Find largest continuous empty area (using box search)
        # Apply a threshold to safe_heatmap to get binary safe zone
        _, binary_safe = cv2.threshold(safe_heatmap, 0.7, 1.0, cv2.THRESH_BINARY)
        binary_safe = binary_safe.astype(np.uint8)

        # Find components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_safe)

        if num_labels <= 1: # Only background
             return RecommendedTextRegion(x=100, y=100, width=800, height=300, confidence=0.5, stability=0.2)

        # Filter out background component (0) and find largest area
        best_comp = 1
        max_area = 0
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] > max_area:
                max_area = stats[i, cv2.CC_STAT_AREA]
                best_comp = i

        # Get bounding box of best component
        x, y, w, h = stats[best_comp, cv2.CC_STAT_LEFT], stats[best_comp, cv2.CC_STAT_TOP], \
                     stats[best_comp, cv2.CC_STAT_WIDTH], stats[best_comp, cv2.CC_STAT_HEIGHT]

        # Scale back to 1920x1080
        final_x, final_y = x * 1920 / w_low, y * 1080 / h_low
        final_w, final_h = w * 1920 / w_low, h * 1080 / h_low

        # Stability is the average safety score in this region
        stability = np.mean(safe_heatmap[y:y+h, x:x+w])

        return RecommendedTextRegion(
            x=float(final_x + 50), # margin
            y=float(final_y + 50),
            width=float(final_w - 100),
            height=float(final_h - 100),
            confidence=float(stability),
            stability=float(stability),
            avoid_subject=True
        )

    except Exception as e:
        print(f"⚠️ Safe Region Recommendation Error: {e}")
        return RecommendedTextRegion(x=100, y=100, width=500, height=300, confidence=0.5, stability=0.0)
