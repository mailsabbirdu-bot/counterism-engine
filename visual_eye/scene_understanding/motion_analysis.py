from typing import List
try:
    from ..schema import MotionAnalysis, TrackedObject, CameraMotion
except (ImportError, ValueError):
    try:
        from visual_eye.schema import MotionAnalysis, TrackedObject, CameraMotion
    except ImportError:
        from schema import MotionAnalysis, TrackedObject, CameraMotion

def analyze_motion(tracks: List[TrackedObject], camera_motion: CameraMotion, total_frames: int) -> MotionAnalysis:
    """
    Estimate overall motion intensity by combining object movement and camera dynamics.
    """
    try:
        if total_frames == 0:
            return MotionAnalysis(intensity="low", score=0.0)

        # 1. Object movement score
        obj_score = 0.0
        if tracks:
            total_movement = sum(t.movement_distance for t in tracks)
            # Movement distance per frame per object
            avg_mv = total_movement / (total_frames * len(tracks))
            obj_score = min(1.0, avg_mv / 8.0) # 8px/frame is high object motion

        # 2. Camera movement score
        cam_scores = {
            "static": 0.1,
            "pan_left": 0.4, "pan_right": 0.4,
            "tilt_up": 0.4, "tilt_down": 0.4,
            "zoom_in": 0.6, "zoom_out": 0.6,
            "forward": 0.8, "backward": 0.8,
            "unknown": 0.2
        }
        cam_score = cam_scores.get(camera_motion.type, 0.2) * (0.5 + camera_motion.confidence / 2)

        # Combined score (Weighted: Camera usually defines the "feel" of motion more)
        final_score = (cam_score * 0.6) + (obj_score * 0.4)

        if final_score > 0.65: intensity = "high"
        elif final_score > 0.3: intensity = "medium"
        else: intensity = "low"

        return MotionAnalysis(
            intensity=intensity,
            score=float(min(1.0, final_score))
        )

    except Exception as e:
        print(f"⚠️ Motion analysis error: {e}")
        return MotionAnalysis(intensity="low", score=0.0)
