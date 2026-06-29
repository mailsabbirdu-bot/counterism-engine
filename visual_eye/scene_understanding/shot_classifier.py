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
    Classify shot type and complexity based on detections, composition, and scene metadata.
    """
    try:
        if not frames:
            return ShotAnalysis()

        all_objs = [obj for f in frames for obj in f.objects]

        # 1. Shot Type (Wide, Medium, Close-up)
        if not all_objs:
             shot_type = "wide" # Landscape/empty shot
        else:
            # Measure relative size of dominant objects
            max_area = 0
            for frame in frames:
                if frame.objects:
                    frame_max = max(o.bbox.width * o.bbox.height for o in frame.objects)
                    max_area = max(max_area, frame_max)

            screen_area = 1920 * 1080
            coverage = max_area / screen_area

            if coverage > 0.4: shot_type = "close_up"
            elif coverage > 0.12: shot_type = "medium"
            else: shot_type = "wide"

        # 2. Camera Height
        # Inferred from horizon and scene type
        if "aerial" in scene_type.lower() or composition.horizon == "lower_third":
            camera_height = "aerial"
        elif any(o.type == "person" for o in all_objs):
            camera_height = "eye_level"
        elif composition.horizon == "upper_third":
            camera_height = "low_angle"
        else:
            camera_height = "normal"

        # 3. Environment
        env_str = str(scene_type).lower()
        if "city" in env_str or "highway" in env_str or "industrial" in env_str:
            environment = "urban"
        elif "interior" in env_str or "office" in env_str or "factory" in env_str:
            environment = "interior"
        elif "forest" in env_str or "mountain" in env_str or "nature" in env_str or "coast" in env_str:
            environment = "nature"
        else:
            environment = "unknown"

        # 4. Complexity
        # Combination of object count and composition busy score
        avg_objs = len(all_objs) / len(frames)
        if composition.busy_score > 0.7 or avg_objs > 12:
            complexity = "high"
        elif composition.busy_score < 0.25 and avg_objs < 3:
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
