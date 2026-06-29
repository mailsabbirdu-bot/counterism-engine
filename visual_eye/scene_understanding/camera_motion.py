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
    Precision camera motion estimation.
    Uses optical flow background displacement while ignoring foreground object noise.
    Returns results only if confidence > 0.75.
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened() or len(sampled_frames) < 2:
            return CameraMotion(type="static_or_unknown", confidence=0.0)

        lk_params = dict(winSize=(21, 21), maxLevel=3,
                        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))
        feature_params = dict(maxCorners=200, qualityLevel=0.01, minDistance=10, blockSize=7)

        motion_votes = []

        for i in range(len(sampled_frames) - 1):
            idx1, idx2 = sampled_frames[i], sampled_frames[i+1]
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx1)
            ret1, frame1 = cap.read()
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx2)
            ret2, frame2 = cap.read()
            if not ret1 or not ret2: continue

            g1, g2 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY), cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            p0 = cv2.goodFeaturesToTrack(g1, mask=None, **feature_params)
            if p0 is None: continue

            p1, st, err = cv2.calcOpticalFlowPyrLK(g1, g2, p0, None, **lk_params)
            if p1 is None: continue

            good_new = p1[st == 1]
            good_old = p0[st == 1]
            if len(good_new) < 20: continue

            dx = good_new[:, 0] - good_old[:, 0]
            dy = good_new[:, 1] - good_old[:, 1]

            # Robust median to ignore object outliers
            mdx, mdy = np.median(dx), np.median(dy)

            # Radial analysis for Zoom / Forward-Backward
            h, w = g1.shape
            cx, cy = w/2, h/2
            dist_old = np.sqrt((good_old[:, 0] - cx)**2 + (good_old[:, 1] - cy)**2)
            dist_new = np.sqrt((good_new[:, 0] - cx)**2 + (good_new[:, 1] - cy)**2)

            valid = dist_old > 30
            if np.any(valid):
                ratios = dist_new[valid] / dist_old[valid]
                zoom_factor = np.median(ratios)

                if zoom_factor > 1.015:
                    motion_votes.append("forward" if np.std(ratios) > 0.04 else "zoom_in")
                elif zoom_factor < 0.985:
                    motion_votes.append("backward" if np.std(ratios) > 0.04 else "zoom_out")
                elif abs(mdx) > 5:
                    motion_votes.append("pan_left" if mdx > 0 else "pan_right")
                elif abs(mdy) > 5:
                    motion_votes.append("tilt_up" if mdy > 0 else "tilt_down")
                else:
                    motion_votes.append("static")

        cap.release()

        if not motion_votes:
            return CameraMotion(type="static_or_unknown", confidence=0.0)

        from collections import Counter
        most_common = Counter(motion_votes).most_common(1)[0]
        conf = most_common[1] / len(motion_votes)

        # PRODUCTION GATE: Require 0.75 confidence
        if conf >= 0.75:
            return CameraMotion(type=most_common[0], confidence=float(conf))
        else:
            return CameraMotion(type="static_or_unknown", confidence=float(conf))

    except Exception as e:
        print(f"⚠️ Camera Motion Error: {e}")
        return CameraMotion(type="static_or_unknown", confidence=0.0)
