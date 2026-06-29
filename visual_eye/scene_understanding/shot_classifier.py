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
    Production-grade shot classification.
    Infers camera height and shot type using horizon, distortion, and object context.
    """
    try:
        if not frames:
            return ShotAnalysis()

        all_objs = [obj for f in frames for obj in f.objects]

        # 1. Shot Type (Wide, Medium, Close-up)
        # We look at the largest subject coverage across sampled frames
        max_subject_coverage = 0
        for f in frames:
            if f.objects:
                frame_max = max(o.bbox.width * o.bbox.height for o in f.objects)
                max_subject_coverage = max(max_subject_coverage, frame_max / (1920 * 1080))

        if max_subject_coverage > 0.35: shot_type = "close_up"
        elif max_subject_coverage > 0.1: shot_type = "medium"
        else: shot_type = "wide"

        # 2. Camera Height (Advanced Inference)
        # Based on horizon position and perspective
        if composition.horizon == "lower_third" or "aerial" in scene_type.lower():
            camera_height = "aerial"
        elif composition.horizon == "upper_third":
            # If horizon is high, we are likely looking down from an elevated position
            camera_height = "elevated"
        elif any(o.type == "person" for o in all_objs):
            # Check for distortion if person is very large/close
            if max_subject_coverage > 0.3: camera_height = "low_angle" # common for close-ups
            else: camera_height = "eye_level"
        else:
            camera_height = "eye_level" # safe default

        # 3. Environment
        env_str = str(scene_type).lower()
        if any(kw in env_str for kw in ["city", "urban", "street", "building"]):
            environment = "urban"
        elif any(kw in env_str for kw in ["nature", "forest", "mountain", "river"]):
            environment = "nature"
        elif "interior" in env_str or "office" in env_str:
            environment = "interior"
        else:
            environment = "unknown"

        # 4. Complexity
        avg_obj_count = len(all_objs) / len(frames) if frames else 0
        if composition.busy_score > 0.7 or avg_obj_count > 10:
            complexity = "high"
        elif composition.busy_score < 0.3 and avg_obj_count < 3:
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
        print(f"⚠️ Shot Classifier Error: {e}")
        return ShotAnalysis()
