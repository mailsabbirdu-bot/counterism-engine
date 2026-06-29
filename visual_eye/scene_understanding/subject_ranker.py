import math
from typing import List, Optional
try:
    from ..schema import TrackedObject, SubjectRank
except (ImportError, ValueError):
    try:
        from visual_eye.schema import TrackedObject, SubjectRank
    except ImportError:
        from schema import TrackedObject, SubjectRank

def rank_visual_subjects(tracks: List[TrackedObject], total_frames: int, sampled_frames_count: int,
                        visual_style: Optional[any] = None, narrative_ranks: List[SubjectRank] = []) -> List[SubjectRank]:
    """
    Implements the Phase 3 Cinematic Importance Model.
    Ranks subjects based on size, position, movement, contrast, and narrative relevance.
    """
    try:
        if not tracks or sampled_frames_count == 0:
            return []

        # Map narrative scores for lookup
        n_map = {r.track_id: r.narrative_importance for r in narrative_ranks}

        ranked = []
        for track in tracks:
            # 1. Subject Size (Area coverage)
            avg_area = track.average_bbox.width * track.average_bbox.height
            screen_area = 1920 * 1080
            coverage = avg_area / screen_area
            size_score = min(1.0, coverage / 0.25)

            # 2. Screen Position Score
            cx = track.average_bbox.x + track.average_bbox.width / 2
            cy = track.average_bbox.y + track.average_bbox.height / 2
            dist_center = math.sqrt((cx - 960)**2 + (cy - 540)**2)
            pos_score = max(0, 1.0 - (dist_center / 1100.0))

            # 3. Tracking Stability / Duration
            stability = track.frames_visible / float(sampled_frames_count)

            # 4. Movement Score
            mv_per_frame = track.movement_distance / (track.frames_visible + 1)
            mv_score = max(0, 1.0 - (mv_per_frame / 20.0)) # Stable = better for focus

            # 5. Contrast (Heuristic from detection confidence and style)
            contrast_score = (track.average_confidence * 0.7) + (0.3 if visual_style and visual_style.contrast > 0.5 else 0.1)

            # 6. Narrative Match
            n_score = n_map.get(track.track_id, 0.0)

            # FORMULA: cinematic_score = size * 0.25 + screen_pos * 0.20 + movement * 0.15 + contrast * 0.15 + duration * 0.15 + narrative * 0.10
            c_score = (size_score * 0.25) + \
                      (pos_score * 0.20) + \
                      (mv_score * 0.15) + \
                      (contrast_score * 0.15) + \
                      (stability * 0.15) + \
                      (n_score * 0.10)

            # FORMULA: final_importance = (visual_importance * 0.45) + (tracking_stability * 0.25) + (screen_pos * 0.15) + (duration * 0.15)
            v_imp = (size_score * 0.45) + (stability * 0.25) + (pos_score * 0.15) + (stability * 0.15)

            # HERO RULES
            if track.type == 'person' and coverage > 0.25 and stability > 0.4:
                v_imp = min(1.0, v_imp + 0.3)

            ranked.append(SubjectRank(
                track_id=track.track_id,
                type=track.type,
                confidence=track.average_confidence,
                visual_importance=float(min(1.0, v_imp)),
                narrative_importance=float(n_score),
                tracking_stability=float(stability),
                screen_position_score=float(pos_score),
                duration_visibility=float(stability),
                cinematic_score=float(min(1.0, c_score)),
                final_importance=float(min(1.0, (v_imp * 0.6 + n_score * 0.4)))
            ))

        ranked.sort(key=lambda x: x.final_importance, reverse=True)
        return ranked
    except Exception as e:
        print(f"⚠️ Subject Ranker Error: {e}")
        return []
