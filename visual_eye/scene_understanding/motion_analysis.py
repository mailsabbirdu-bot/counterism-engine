from typing import List
try:
    from ..schema import MotionAnalysis, TrackedObject
except (ImportError, ValueError):
    try:
        from visual_eye.schema import MotionAnalysis, TrackedObject
    except ImportError:
        from schema import MotionAnalysis, TrackedObject

def analyze_motion(tracks: List[TrackedObject], total_frames: int) -> MotionAnalysis:
    """
    Estimate movement amount based on object tracks.
    """
    try:
        if not tracks or total_frames == 0:
            return MotionAnalysis(intensity="low", score=0.0)

        total_movement = sum(t.movement_distance for t in tracks)
        avg_movement_per_frame = total_movement / (total_frames * len(tracks))

        score = min(1.0, avg_movement_per_frame / 5.0)

        if score > 0.6: intensity = "high"
        elif score > 0.2: intensity = "medium"
        else: intensity = "low"

        return MotionAnalysis(
            intensity=intensity,
            score=float(score)
        )

    except Exception as e:
        print(f"⚠️ Motion analysis error: {e}")
        return MotionAnalysis(intensity="low", score=0.0)
