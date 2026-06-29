import math
from typing import List
try:
    from ..schema import TrackedObject, SubjectRank
except (ImportError, ValueError):
    try:
        from visual_eye.schema import TrackedObject, SubjectRank
    except ImportError:
        from schema import TrackedObject, SubjectRank

def rank_visual_subjects(tracks: List[TrackedObject], total_frames: int) -> List[SubjectRank]:
    """
    Rank objects by visual importance based on size, duration, and confidence.
    """
    ranked = []

    if not tracks or total_frames == 0:
        return []

    for track in tracks:
        # 1. Size score (coverage of the 1920x1080 screen)
        area = track.average_bbox.width * track.average_bbox.height
        size_score = min(1.0, area / (1920 * 1080 * 0.2)) # Normalized to 20% screen coverage

        # 2. Duration score
        duration_score = track.frames_visible / 10.0 # Heuristic relative to typical sampling

        # 3. Position score (Rule of Thirds / Centeredness)
        cx = track.average_bbox.x + track.average_bbox.width / 2
        cy = track.average_bbox.y + track.average_bbox.height / 2
        dist_from_center = math.sqrt((cx - 960)**2 + (cy - 540)**2)
        pos_score = max(0, 1.0 - (dist_from_center / 1100)) # 1.0 at center, 0.0 at corners

        # Combined Visual Importance
        visual_importance = (size_score * 0.4) + (pos_score * 0.3) + (track.average_confidence * 0.3)
        visual_importance = min(1.0, visual_importance)

        ranked.append(SubjectRank(
            track_id=track.track_id,
            type=track.type,
            visual_importance=visual_importance
        ))

    # Sort by importance descending
    ranked.sort(key=lambda x: x.visual_importance, reverse=True)
    return ranked
