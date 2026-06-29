import cv2
import numpy as np
from typing import List, Optional
try:
    from ..schema import CameraMotion
except (ImportError, ValueError):
    try:
        from visual_eye.schema import CameraMotion
    except ImportError:
        from schema import CameraMotion

def estimate_camera_motion(video_path: str, sampled_frames: List[int]) -> CameraMotion:
    """
    Estimate camera motion (pan, zoom, static) using Lucas-Kanade optical flow on sampled frames.
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return CameraMotion(type="unknown", confidence=0.0)

        motions = []

        # Parameters for lucas kanade optical flow
        lk_params = dict(winSize=(15, 15), maxLevel=2,
                        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

        # Parameters for ShiTomasi corner detection
        feature_params = dict(maxCorners=100, qualityLevel=0.3, minDistance=7, blockSize=7)

        # Iterate through pairs of sampled frames
        for i in range(len(sampled_frames) - 1):
            idx1 = sampled_frames[i]
            idx2 = sampled_frames[i+1]

            cap.set(cv2.CAP_PROP_POS_FRAMES, idx1)
            ret1, frame1 = cap.read()
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx2)
            ret2, frame2 = cap.read()

            if not ret1 or not ret2: continue

            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

            p0 = cv2.goodFeaturesToTrack(gray1, mask=None, **feature_params)
            if p0 is None: continue

            p1, st, err = cv2.calcOpticalFlowPyrLK(gray1, gray2, p0, None, **lk_params)

            if p1 is None: continue

            # Select good points
            good_new = p1[st == 1]
            good_old = p0[st == 1]

            if len(good_new) < 10: continue

            # Calculate movement vectors
            dx = good_new[:, 0] - good_old[:, 0]
            dy = good_new[:, 1] - good_old[:, 1]

            # Median movement
            mdx = np.median(dx)
            mdy = np.median(dy)

            # Detect zoom
            # Zoom in: points move away from center
            # Zoom out: points move towards center
            h, w = gray1.shape
            cx, cy = w/2, h/2

            dist_old = np.sqrt((good_old[:, 0] - cx)**2 + (good_old[:, 1] - cy)**2)
            dist_new = np.sqrt((good_new[:, 0] - cx)**2 + (good_new[:, 1] - cy)**2)

            # Use ratio to detect zoom
            zoom_ratios = dist_new / dist_old
            valid_ratios = zoom_ratios[dist_old > 10] # Avoid division by small numbers near center
            zoom_factor = np.median(valid_ratios) if len(valid_ratios) > 0 else 1.0

            if zoom_factor > 1.01: motions.append("zoom_in")
            elif zoom_factor < 0.99: motions.append("zoom_out")
            elif abs(mdx) > 3:
                # Pixels move right (mdx > 0) -> Camera panned left
                if mdx > 0: motions.append("pan_left")
                else: motions.append("pan_right")
            elif abs(mdy) > 3:
                # Pixels move down (mdy > 0) -> Camera tilted up
                if mdy > 0: motions.append("tilt_up")
                else: motions.append("tilt_down")
            else:
                motions.append("static")

        cap.release()

        if not motions:
            return CameraMotion(type="unknown", confidence=0.0)

        from collections import Counter
        most_common = Counter(motions).most_common(1)[0]

        return CameraMotion(
            type=most_common[0],
            confidence=most_common[1] / len(motions)
        )

    except Exception as e:
        print(f"⚠️ Camera motion error: {e}")
        return CameraMotion(type="unknown", confidence=0.0)
