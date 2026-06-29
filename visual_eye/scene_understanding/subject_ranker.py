import math
from typing import List
try:
    from ..schema import TrackedObject, SubjectRank
except (ImportError, ValueError):
    try:
        from visual_eye.schema import TrackedObject, SubjectRank
    except ImportError:
        from schema import TrackedObject, SubjectRank

def rank_visual_subjects(tracks: List[TrackedObject], total_frames: int, sampled_frames_count: int) -> List[SubjectRank]:
    """
    Rank objects by visual importance based on size, duration, confidence, and position.
    """
    try:
        ranked = []
        if not tracks or sampled_frames_count == 0:
            return []

        for track in tracks:
            # 1. Size score (average screen coverage)
            # Area relative to 1920x1080
            avg_area = track.average_bbox.width * track.average_bbox.height
            size_score = min(1.0, avg_area / (1920 * 1080 * 0.15)) # 15% coverage is high importance

            # 2. Duration/Persistence score
            # Frames visible relative to total sampled frames
            persistence_score = track.frames_visible / float(sampled_frames_count)

            # 3. Position score (Rule of Thirds / Centrality)
            cx = track.average_bbox.x + track.average_bbox.width / 2
            cy = track.average_bbox.y + track.average_bbox.height / 2

            # Centeredness: distance from center
            dist_from_center = math.sqrt((cx - 960)**2 + (cy - 540)**2)
            # Normalizing distance (max distance to corner is ~1100)
            center_score = max(0, 1.0 - (dist_from_center / 1100.0))

            # 4. Movement consistency
            # High movement might mean secondary object, steady position might mean subject
            # (or vice-versa, but usually subjects are tracked steadily)
            # For now, we prioritize confidence and duration.

            # Combined Visual Importance
            # Weights: Persistence (30%), Size (30%), Confidence (25%), Position (15%)
            v_imp = (persistence_score * 0.35) + (size_score * 0.25) + (track.average_confidence * 0.25) + (center_score * 0.15)
            v_imp = float(min(1.0, v_imp))

            ranked.append(SubjectRank(
                track_id=track.track_id,
                type=track.type,
                visual_importance=v_imp
            ))

        ranked.sort(key=lambda x: x.visual_importance, reverse=True)
        return ranked
    except Exception as e:
        print(f"⚠️ Visual subject ranking error: {e}")
        return []
