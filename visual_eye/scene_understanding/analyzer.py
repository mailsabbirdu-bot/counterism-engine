import os
from typing import List, Dict, Any, Optional

try:
    from ..schema import SceneAnalysis, SceneSummary, SubjectRank, CinematicDecision, RecommendedTextRegion
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
        from visual_eye.schema import SceneAnalysis, SceneSummary, SubjectRank, CinematicDecision, RecommendedTextRegion
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
        from schema import SceneAnalysis, SceneSummary, SubjectRank, CinematicDecision, RecommendedTextRegion
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
    Main Orchestrator for Phase 3 Cinematic Intelligence.
    """
    frames = analysis.frames
    total_frames = analysis.total_frames
    indices = [f.frame_index for f in frames]

    # 1. Perception Layer
    try: analysis.tracked_objects = track_objects(frames)
    except: pass

    try: analysis.visual_style = analyze_colors(frames, video_path)
    except: pass

    try: analysis.composition = analyze_composition(frames, video_path)
    except: pass

    try: analysis.camera_motion = estimate_camera_motion(video_path, indices)
    except: pass

    # 2. Ranking Layer (Refined ordering for dependencies)
    try:
        # Get narrative scores first
        analysis.narrative_subjects = rank_narrative_subjects(analysis.tracked_objects, context)
        # Use them in cinematic model
        analysis.main_subjects = rank_visual_subjects(
            analysis.tracked_objects, total_frames, len(frames),
            analysis.visual_style, analysis.narrative_subjects
        )
        # Sync visual_subjects for schema compatibility
        analysis.visual_subjects = analysis.main_subjects
    except: pass

    # Hero selection
    if analysis.main_subjects:
        best = analysis.main_subjects[0]
        analysis.main_subject = {
            "track_id": best.track_id, "type": best.type,
            "confidence": best.confidence, "importance_score": best.final_importance
        }

    # 3. Decision Layer
    try: analysis.shot_analysis = classify_shot(frames, analysis.composition, analysis.scene_type)
    except: pass

    try: analysis.recommended_text_region = recommend_text_region(frames, video_path)
    except: pass

    try: analysis.motion = analyze_motion(analysis.tracked_objects, analysis.camera_motion, total_frames)
    except: pass

    try: analysis.scene_summary = generate_cinematic_summary(analysis)
    except: pass

    return analysis

def generate_cinematic_summary(analysis: SceneAnalysis) -> SceneSummary:
    hero = analysis.main_subject
    secondaries = []
    if len(analysis.main_subjects) > 1:
        for s in analysis.main_subjects[1:4]:
            secondaries.append({"track_id": s.track_id, "type": s.type, "importance": s.final_importance})

    tx_conf = analysis.recommended_text_region.confidence
    tx_decision = "center"
    fallback = False

    if tx_conf < 0.6:
        ns = analysis.composition.negative_space
        tx_decision = f"place_text_{ns}"
        fallback = True
    else:
        rx, ry = analysis.recommended_text_region.x, analysis.recommended_text_region.y
        pos = "center"
        if rx < 640: pos = "left"
        elif rx > 1280: pos = "right"
        if ry < 360: pos = f"top_{pos}"
        elif ry > 720: pos = f"bottom_{pos}"
        tx_decision = f"place_text_{pos}"

    anim_style = "slow_fade"
    if analysis.motion.intensity == "high": anim_style = "dynamic_slide"
    elif analysis.camera_motion.type == "zoom_in": anim_style = "parallax_reveal"

    main_type = hero['type'] if hero else "environment"
    strategy = f"The primary {main_type} subject occupies the {analysis.composition.visual_balance.replace('_heavy', ' side')} of the frame "
    strategy += f"while the {analysis.composition.negative_space.replace('_', ' ')} contains negative space suitable for documentary typography."

    return SceneSummary(
        hero_subject=hero,
        secondary_subjects=secondaries,
        text_position=CinematicDecision(decision=tx_decision, confidence=float(tx_conf), fallback_used=fallback),
        camera_behavior=CinematicDecision(decision=analysis.camera_motion.type, confidence=analysis.camera_motion.confidence),
        animation_style=CinematicDecision(decision=anim_style, confidence=0.8),
        overlay_strategy=strategy,
        main_subject=main_type,
        selection_reason=strategy,
        camera_motion=analysis.camera_motion.type,
        best_overlay_side=analysis.composition.negative_space,
        recommended_animation=anim_style
    )
