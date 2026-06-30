import os
from typing import List, Dict, Any, Optional

try:
    from ..schema import (
        SceneAnalysis, SceneSummary, SubjectRank, CinematicDecision,
        RecommendedTextRegion, AISummary, AIHeroSubject, AIShotSummary,
        AICompositionSummary, AISemanticContext
    )
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
        from visual_eye.schema import (
            SceneAnalysis, SceneSummary, SubjectRank, CinematicDecision,
            RecommendedTextRegion, AISummary, AIHeroSubject, AIShotSummary,
            AICompositionSummary, AISemanticContext
        )
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
        from schema import (
            SceneAnalysis, SceneSummary, SubjectRank, CinematicDecision,
            RecommendedTextRegion, AISummary, AIHeroSubject, AIShotSummary,
            AICompositionSummary, AISemanticContext
        )
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
    Main Orchestrator for Phase 3.1 AI-Ready Scene Understanding.
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

    # 2. Ranking Layer
    try:
        analysis.narrative_subjects = rank_narrative_subjects(analysis.tracked_objects, context)
        analysis.main_subjects = rank_visual_subjects(
            analysis.tracked_objects, total_frames, len(frames),
            analysis.visual_style, analysis.narrative_subjects
        )
        analysis.visual_subjects = analysis.main_subjects
    except: pass

    # Hero selection logic
    hero = None
    if analysis.main_subjects:
        best = analysis.main_subjects[0]
        # Environment Dominance Check
        scene_type = str(analysis.scene_type).lower()
        script = str(context.get('script', '')).lower() if context else ""

        # Determine if environment should be hero
        env_hero_type = None
        if "highway" in scene_type: env_hero_type = "traffic_scene"
        elif "aerial" in scene_type or "skyline" in scene_type: env_hero_type = "urban_density"
        elif any(kw in scene_type for kw in ["forest", "mountain", "nature", "landscape"]): env_hero_type = "landscape"
        elif "crowd" in scene_type or "pedestrian" in scene_type: env_hero_type = "human_activity"

        # If env hero detected AND (no visual hero is strong OR narrative focus is on env)
        if env_hero_type and (best.final_importance < 0.6 or env_hero_type in script):
            analysis.main_subject = {
                "track_id": "environment",
                "type": env_hero_type,
                "confidence": 1.0,
                "importance_score": 0.9
            }
        else:
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

    # Prepare Tracks for Remotion (Phase 3.2 Hardening)
    try:
        from ..schema import TrackData
        analysis.tracks = [
            TrackData(track_id=t.track_id, type=t.type, frames=t.history)
            for t in analysis.tracked_objects if t.frames_visible > 5
        ]
    except: pass

    try: analysis.scene_summary = generate_cinematic_summary(analysis)
    except: pass

    # 4. AI Summary Generation
    try: analysis.ai_summary = generate_ai_summary(analysis, context)
    except Exception as e:
        print(f"⚠️ AI Summary Generation Error: {e}")

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

def generate_ai_summary(analysis: SceneAnalysis, context: Optional[Dict[str, Any]] = None) -> AISummary:
    types = [t.type for t in analysis.tracked_objects]
    avg_area = sum(t.average_bbox.width * t.average_bbox.height for t in analysis.tracked_objects) / (1920*1080) if analysis.tracked_objects else 0
    has_water = any(kw in analysis.scene_type.lower() for kw in ['river', 'ocean', 'coast', 'water']) or 'boat' in types
    is_night = analysis.visual_style.brightness < 0.35

    p_flow = "static"
    if analysis.motion.score > 0.6: p_flow = "moving rapidly"
    elif analysis.motion.score > 0.2: p_flow = "moving across frame"

    semantic = AISemanticContext(
        crowd_density=min(1.0, types.count('person') / 12.0),
        traffic_density=min(1.0, (types.count('car') + types.count('truck') + types.count('bus')) / 10.0),
        greenery_level=min(1.0, types.count('tree') / 6.0),
        urban_density=min(1.0, types.count('building') / 5.0),
        water_presence=has_water,
        skyline_visibility=1.0 if analysis.composition.horizon == "lower_third" else 0.4,
        pedestrian_flow=p_flow,
        movement_intensity=analysis.motion.intensity,
        construction_level=min(1.0, types.count('truck') / 4.0) if 'building' in types else 0.0,
        time_of_day="night" if is_night else "day"
    )

    hero = None
    if analysis.main_subject:
        best = analysis.main_subject
        pos = "center"
        role = "primary subject"
        if best['track_id'] != "environment":
            t_info = next((t for t in analysis.tracked_objects if t.track_id == best['track_id']), None)
            if t_info:
                cx = t_info.average_bbox.x + t_info.average_bbox.width/2
                if cx < 640: pos = "left"
                elif cx > 1280: pos = "right"
                if (t_info.average_bbox.width * t_info.average_bbox.height) / (1920*1080) < 0.05:
                    role = "background subject"
        else:
            role = "environmental focus"

        hero = AIHeroSubject(
            type=best['type'],
            position=pos,
            size_ratio=float(avg_area),
            importance=best['importance_score'],
            confidence=best['confidence'],
            role=role
        )

    tx_pos = analysis.scene_summary.text_position.decision.replace('place_text_', '')
    # Ensure preferred text region is strictly derived from high-confidence organic safe zones
    if analysis.recommended_text_region.confidence > 0.7:
        rx, ry = analysis.recommended_text_region.x, analysis.recommended_text_region.y
        if rx < 640: tx_pos = "left"
        elif rx > 1280: tx_pos = "right"
        if ry < 360: tx_pos = f"top_{tx_pos}"
        elif ry > 720: tx_pos = f"bottom_{tx_pos}"

    secondaries = list(set([s.type for s in analysis.main_subjects[1:5]]))

    shot_desc = f"{analysis.shot_analysis.shot_type.capitalize()} {analysis.shot_analysis.camera_height} shot"
    scene_desc = f"of {analysis.scene_type.replace('_', ' ')}"
    layout_desc = f"The primary focus is on the {hero.type if hero else 'environment'} on the {hero.position if hero else 'center'}."
    graphics_desc = f"The {analysis.composition.negative_space.replace('_', ' ')} provides clean negative space for typography."
    full_desc = f"{shot_desc} {scene_desc}. {layout_desc} {graphics_desc}"

    return AISummary(
        scene_id=context.get('scene_id', 'SCENE_XX') if context else "SCENE_XX",
        scene_type=analysis.scene_type,
        environment=analysis.shot_analysis.environment,
        shot=AIShotSummary(
            type=analysis.shot_analysis.shot_type,
            camera_height=analysis.shot_analysis.camera_height,
            camera_motion=analysis.camera_motion.type
        ),
        composition=AICompositionSummary(
            balance=analysis.composition.visual_balance,
            negative_space=analysis.composition.negative_space,
            horizon=analysis.composition.horizon,
            busy_score=analysis.composition.busy_score
        ),
        hero_subject=hero,
        secondary_subjects=secondaries,
        semantic_context=semantic,
        camera_recommendation={
            "animation": analysis.scene_summary.recommended_animation,
            "overlay_side": analysis.composition.negative_space
        },
        text_region={"preferred": tx_pos},
        visual_style=analysis.visual_style,
        semantic_description=full_desc
    )
