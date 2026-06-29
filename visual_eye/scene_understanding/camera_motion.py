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
    Enhanced camera motion estimation (pan, zoom, tilt, forward/backward) using OpenCV.
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened() or len(sampled_frames) < 2:
            return CameraMotion(type="unknown", confidence=0.0)

        motions = []

        # Lucas-Kanade parameters
        lk_params = dict(winSize=(21, 21), maxLevel=3,
                        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))

        # Feature parameters
        feature_params = dict(maxCorners=200, qualityLevel=0.01, minDistance=10, blockSize=7)

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

            # Filter good points
            good_new = p1[st == 1]
            good_old = p0[st == 1]

            if len(good_new) < 15: continue

            # Global vectors
            dx = good_new[:, 0] - good_old[:, 0]
            dy = good_new[:, 1] - good_old[:, 1]

            mdx = np.median(dx)
            mdy = np.median(dy)

            # Center of the frame
            h, w = gray1.shape
            cx, cy = w/2, h/2

            # Radial distance from center
            dist_old = np.sqrt((good_old[:, 0] - cx)**2 + (good_old[:, 1] - cy)**2)
            dist_new = np.sqrt((good_new[:, 0] - cx)**2 + (good_new[:, 1] - cy)**2)

            # Filter points very close to center to avoid noise
            valid_mask = dist_old > 20
            if np.any(valid_mask):
                # Zoom / Forward/Backward detection
                # Average ratio of distances from center
                ratios = dist_new[valid_mask] / dist_old[valid_mask]
                zoom_factor = np.median(ratios)

                # Check for "Forward" vs "Zoom In"
                # Forward (Dolly): Expansion from center, but often accompanied by parallax
                # Zoom In: Uniform scaling
                # For this Phase, we'll treat them similarly but try to distinguish by ratio variance

                if zoom_factor > 1.015:
                    motions.append("forward" if np.std(ratios) > 0.05 else "zoom_in")
                elif zoom_factor < 0.985:
                    motions.append("backward" if np.std(ratios) > 0.05 else "zoom_out")
                elif abs(mdx) > 4:
                    # Pixels move right -> Camera moves left
                    motions.append("pan_left" if mdx > 0 else "pan_right")
                elif abs(mdy) > 4:
                    # Pixels move down -> Camera moves up
                    motions.append("tilt_up" if mdy > 0 else "tilt_down")
                else:
                    motions.append("static")

        cap.release()

        if not motions:
            return CameraMotion(type="unknown", confidence=0.0)

        from collections import Counter
        most_common = Counter(motions).most_common(1)[0]
        confidence = most_common[1] / len(motions)

        # Only return if we have decent confidence (> 50%)
        if confidence > 0.5:
            return CameraMotion(type=most_common[0], confidence=float(confidence))
        else:
            return CameraMotion(type="unknown", confidence=float(confidence))

    except Exception as e:
        print(f"⚠️ Camera motion error: {e}")
        return CameraMotion(type="unknown", confidence=0.0)
