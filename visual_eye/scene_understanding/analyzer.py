import os
from typing import List, Dict, Any, Optional

try:
    from ..schema import SceneAnalysis, SceneSummary, SubjectRank
    from .tracker import track_objects
    from .subject_ranker import rank_visual_subjects
    from .narrative_ranker import rank_narrative_subjects
    from .camera_motion import estimate_camera_motion
    from .composition import analyze_composition
    from .shot_classifier import classify_shot
    from .text_region import recommend_text_region
    from .color_analysis import analyze_colors
    from .motion_analysis import analyze_motion
except (ImportError, ValueError):
    try:
        from visual_eye.schema import SceneAnalysis, SceneSummary, SubjectRank
        from visual_eye.scene_understanding.tracker import track_objects
        from visual_eye.scene_understanding.subject_ranker import rank_visual_subjects
        from visual_eye.scene_understanding.narrative_ranker import rank_narrative_subjects
        from visual_eye.scene_understanding.camera_motion import estimate_camera_motion
        from visual_eye.scene_understanding.composition import analyze_composition
        from visual_eye.scene_understanding.shot_classifier import classify_shot
        from visual_eye.scene_understanding.text_region import recommend_text_region
        from visual_eye.scene_understanding.color_analysis import analyze_colors
        from visual_eye.scene_understanding.motion_analysis import analyze_motion
    except ImportError:
        from schema import SceneAnalysis, SceneSummary, SubjectRank
        from tracker import track_objects
        from subject_ranker import rank_visual_subjects
        from narrative_ranker import rank_narrative_subjects
        from camera_motion import estimate_camera_motion
        from composition import analyze_composition
        from shot_classifier import classify_shot
        from text_region import recommend_text_region
        from color_analysis import analyze_colors
        from motion_analysis import analyze_motion

def perform_scene_understanding(analysis: SceneAnalysis, video_path: str, context: Optional[Dict[str, Any]] = None) -> SceneAnalysis:
    """
    Main entry point for the Scene Understanding Layer.
    Orchestrates modules and populates the SceneAnalysis object.
    """
    frames = analysis.frames
    total_frames = analysis.total_frames
    sampled_indices = [f.frame_index for f in frames]

    # 1. Object Tracking
    try:
        analysis.tracked_objects = track_objects(frames)
    except Exception as e: print(f"⚠️ Track Fail: {e}")

    # 2. Camera Motion
    try:
        analysis.camera_motion = estimate_camera_motion(video_path, sampled_indices)
    except Exception as e: print(f"⚠️ Camera Fail: {e}")

    # 3. Composition
    try:
        analysis.composition = analyze_composition(frames, video_path)
    except Exception as e: print(f"⚠️ Composition Fail: {e}")

    # 4. Subject Ranking (Visual)
    try:
        analysis.visual_subjects = rank_visual_subjects(analysis.tracked_objects, total_frames, len(frames))
    except Exception as e: print(f"⚠️ Visual Rank Fail: {e}")

    # 5. Subject Ranking (Narrative)
    try:
        analysis.narrative_subjects = rank_narrative_subjects(analysis.tracked_objects, context)
    except Exception as e: print(f"⚠️ Narrative Rank Fail: {e}")

    # 6. Final Combined Ranking
    try:
        analysis.main_subjects = combine_rankings(analysis.visual_subjects, analysis.narrative_subjects)
    except Exception as e: print(f"⚠️ Combined Rank Fail: {e}")

    # 7. Shot classification
    try:
        analysis.shot_analysis = classify_shot(frames, analysis.composition, analysis.scene_type)
    except Exception as e: print(f"⚠️ Shot Fail: {e}")

    # 8. Text region
    try:
        analysis.recommended_text_region = recommend_text_region(frames)
    except Exception as e: print(f"⚠️ Text Region Fail: {e}")

    # 9. Style
    try:
        analysis.visual_style = analyze_colors(frames, video_path)
    except Exception as e: print(f"⚠️ Style Fail: {e}")

    # 10. Motion
    try:
        analysis.motion = analyze_motion(analysis.tracked_objects, analysis.camera_motion, total_frames)
    except Exception as e: print(f"⚠️ Motion Fail: {e}")

    # 11. Summary
    try:
        analysis.scene_summary = generate_summary(analysis)
    except Exception as e: print(f"⚠️ Summary Fail: {e}")

    return analysis

def combine_rankings(visual: List[SubjectRank], narrative: List[SubjectRank], v_weight: float = 0.5, n_weight: float = 0.5) -> List[SubjectRank]:
    combined = {}
    for v in visual:
        combined[v.track_id] = {'type': v.type, 'v': v.visual_importance, 'n': 0.0}
    for n in narrative:
        if n.track_id in combined: combined[n.track_id]['n'] = n.narrative_importance
        else: combined[n.track_id] = {'type': n.type, 'v': 0.0, 'n': n.narrative_importance}

    results = []
    for tid, info in combined.items():
        final = (info['v'] * v_weight) + (info['n'] * n_weight)
        results.append(SubjectRank(track_id=tid, type=info['type'], visual_importance=info['v'], narrative_importance=info['n'], final_importance=float(final)))
    results.sort(key=lambda x: x.final_importance, reverse=True)
    return results

def generate_summary(analysis: SceneAnalysis) -> SceneSummary:
    main_subject = "unknown"
    reason = "No distinct subject identified"

    if analysis.main_subjects:
        best = analysis.main_subjects[0]
        main_subject = best.type
        if best.narrative_importance > 0.7: reason = f"Mentioned in script with strong {best.type} presence"
        else: reason = f"Visually dominant {best.type}"

    side = "center"
    ns = analysis.composition.negative_space
    if "left" in ns: side = "left"
    elif "right" in ns: side = "right"

    anim = "fade_in"
    if analysis.camera_motion.type == "zoom_in" or analysis.camera_motion.type == "forward": anim = "zoom_in"
    elif analysis.motion.intensity == "high": anim = "slide_up"

    return SceneSummary(
        main_subject=main_subject,
        selection_reason=reason,
        camera_motion=analysis.camera_motion.type,
        best_overlay_side=side,
        recommended_animation=anim
    )
