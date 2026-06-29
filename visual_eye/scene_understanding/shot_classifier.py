try:
    from ..schema import ShotAnalysis, AnalysisFrame, CompositionAnalysis, DetectedObject
except (ImportError, ValueError):
    try:
        from visual_eye.schema import ShotAnalysis, AnalysisFrame, CompositionAnalysis, DetectedObject
    except ImportError:
        from schema import ShotAnalysis, AnalysisFrame, CompositionAnalysis, DetectedObject

from typing import List

def classify_shot(frames: List[AnalysisFrame], composition: CompositionAnalysis, scene_type: str) -> ShotAnalysis:
    """
    Classify shot type and complexity based on detections and composition.
    """
    try:
        if not frames:
            return ShotAnalysis()

        # 1. Shot Type (Wide, Medium, Close-up)
        # Based on average object size relative to frame
        all_objs = [obj for f in frames for obj in f.objects]
        if not all_objs:
             shot_type = "wide" # Default for empty scenes
        else:
            avg_area = sum(o.bbox.width * o.bbox.height for o in all_objs) / len(all_objs)
            screen_area = 1920 * 1080
            if avg_area > screen_area * 0.3: shot_type = "close_up"
            elif avg_area > screen_area * 0.1: shot_type = "medium"
            else: shot_type = "wide"

        # 2. Camera Height
        if "aerial" in scene_type.lower() or "top_down" in scene_type.lower():
            camera_height = "aerial"
        elif any(o.type == "person" for o in all_objs):
            camera_height = "eye_level"
        else:
            camera_height = "unknown"

        # 3. Environment
        environment = "urban" if "city" in scene_type.lower() or "building" in scene_type.lower() else "nature"
        if "interior" in scene_type.lower(): environment = "interior"

        # 4. Complexity
        if composition.busy_score > 0.6 or len(all_objs) > 10:
            complexity = "high"
        elif composition.busy_score < 0.3 and len(all_objs) < 3:
            complexity = "low"
        else:
            complexity = "medium"

        return ShotAnalysis(
            shot_type=shot_type,
            camera_height=camera_height,
            environment=environment,
            complexity=complexity
        )

    except Exception as e:
        print(f"⚠️ Shot classification error: {e}")
        return ShotAnalysis()
