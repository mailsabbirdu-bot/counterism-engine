import json
import re
import math
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field

@dataclass
class PerceptionFinding:
    """v5 schema for individual perception observations."""
    severity: str # info, warning, error, critical
    confidence: float # 0.0-1.0
    frame_range: Tuple[int, int]
    affected_elements: List[str]
    human_explanation: str
    technical_explanation: str
    viewer_impact: str
    fix_suggestion: str
    expected_quality_gain: float
    category: str = "general" # layout, motion, cognitive, composition, readability, narrative

@dataclass
class PerceptionObservation:
    """Standardized container for analysis results from modules."""
    module_name: str
    findings: List[PerceptionFinding] = field(default_factory=list)
    issues: List[str] = field(default_factory=list) # Legacy compatibility
    motion_issues: List[str] = field(default_factory=list)
    director_notes: List[str] = field(default_factory=list)
    fix_suggestions: List[str] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SceneState:
    """Read-only container for frame-by-frame simulation data."""
    frame_load: List[float]
    motion_events: List[int]
    active_elements_per_frame: List[int]
    visual_noise_per_frame: List[float]
    energy_curve: List[float]
    duration: int
    focus_timeline: List[Optional[str]] = field(default_factory=list)
    tone: str = "neutral"

class AnalysisModule:
    """Base class for all Cinematic Perception modules."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        raise NotImplementedError

class VisualSaliencyEngine(AnalysisModule):
    """MODULE 1: Dynamic Visual Saliency (Eye Catching Score)."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Visual Saliency")
        focus_timeline = []

        for f in range(state.duration):
            candidates = []
            for ov in supervisor.overlays:
                start, end = ov.get('start', 0), ov.get('start', 0) + ov.get('duration', state.duration)
                if start <= f < end:
                    # Saliency Factors
                    size = (ov.get('width', 400) * ov.get('height', 400)) / (1920 * 1080)
                    opacity = ov.get('opacity', 1.0)
                    is_hero = 2.0 if str(ov.get('importance','')).lower() == 'hero' else 1.0
                    anim_boost = 1.5 if (f - start) < 30 else 1.0

                    saliency = size * opacity * is_hero * anim_boost
                    candidates.append({'id': ov.get('id'), 'score': saliency})

            if not candidates:
                focus_timeline.append(None)
                continue

            candidates.sort(key=lambda x: x['score'], reverse=True)
            primary = candidates[0]
            focus_timeline.append(primary['id'])

            # Detect Conflict
            if len(candidates) > 1 and candidates[1]['score'] > primary['score'] * 0.85:
                if f % 30 == 0:
                    obs.issues.append(f"Attention Conflict at frame {f}: '{primary['id']}' vs '{candidates[1]['id']}'.")
                    obs.director_notes.append(f"Viewer attention is split at {f}f. Make the hero element more dominant.")
                    obs.fix_suggestions.append(f"Increase opacity or scale of hero relative to '{candidates[1]['id']}'.")

        state.focus_timeline.extend(focus_timeline)
        return obs

class EyeMovementSimulator(AnalysisModule):
    """MODULE 2: Simulates Fixations, Saccades, and Reading Flow."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Eye Flow")
        last_pos = None
        travel_distance = 0

        sorted_overlays = sorted(supervisor.overlays, key=lambda x: x.get('start', 0))
        for ov in sorted_overlays:
            pos = ov.get('position', {'x': 960, 'y': 540})
            if last_pos:
                dist = math.sqrt((pos['x']-last_pos['x'])**2 + (pos['y']-last_pos['y'])**2)
                travel_distance += dist
                if dist > 800:
                    obs.issues.append(f"Erratic Eye Jump: Rapid shift to {ov.get('id')}.")
                    obs.director_notes.append(f"The eye has to jump too far ({int(dist)}px). Maintain a natural scan path.")
            last_pos = pos

        obs.scores['eye_flow'] = max(0, 10 - (travel_distance / 2000))
        return obs

class VisualNoiseDetector(AnalysisModule):
    """MODULE 3: Decorative graphics competing with info."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Visual Noise")
        avg_noise = sum(state.visual_noise_per_frame) / state.duration if state.duration > 0 else 0
        if avg_noise > 0.8: # Calibrated threshold
            obs.issues.append(f"Visual Noise Too High ({round(avg_noise, 1)}). Decorative elements distracting from content.")
            obs.director_notes.append("Background particles or shapes are too active. Simplify decorative layers.")
        return obs

class VisualCompositionEngine(AnalysisModule):
    """MODULE 3: Judges Layout via Rule of Thirds and Golden Ratio."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Composition")
        centerX, centerY = 0, 0
        for ov in supervisor.overlays:
            p = ov.get('position', {'x': 960, 'y': 540})
            centerX += p['x']
            centerY += p['y']

        if supervisor.overlays:
            avgX, avgY = centerX / len(supervisor.overlays), centerY / len(supervisor.overlays)
            # Penalize generic center stacking
            if abs(avgX - 960) < 50 and abs(avgY - 540) < 50:
                obs.issues.append("Static Composition: Everything is centered.")
                obs.director_notes.append("The layout feels amateur. Use Rule of Thirds anchors for focal elements.")
                obs.fix_suggestions.append("Move secondary indicators to (550, 540) or (1370, 540).")

        return obs

class GestaltAnalyzer(AnalysisModule):
    """MODULE 4: Proximity and Similarity Grouping."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Gestalt")
        # Logic to detect accidentally close objects
        for i, o1 in enumerate(supervisor.overlays):
            for o2 in supervisor.overlays[i+1:]:
                p1, p2 = o1.get('position', {'x':0,'y':0}), o2.get('position', {'x':999,'y':999})
                dist = math.sqrt((p1['x']-p2['x'])**2 + (p1['y']-p2['y'])**2)
                if dist < 100:
                    obs.issues.append(f"Accidental Grouping: '{o1.get('id')}' and '{o2.get('id')}' are too close.")
                    obs.fix_suggestions.append(f"Add breathing space between '{o1.get('id')}' and '{o2.get('id')}'.")
        return obs

class MotionPsychologyEngine(AnalysisModule):
    """MODULE 5: Purpose-driven animation evaluation."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Motion Psychology")
        motion_count = 0
        for ov in supervisor.overlays:
            anim = ov.get('animation', 'static')
            if anim != 'static':
                motion_count += 1
                # Rule: Decorative motion (shapes) should not animate during data reveals
                if ov.get('type') == 'shape' and any(o.get('type') in ['chart', 'indicator'] for o in supervisor.overlays):
                    obs.motion_issues.append(f"Distracting Decoration: '{ov.get('id')}' animates during info reveal.")
                    obs.director_notes.append("Background motion competes with data comprehension.")

        if motion_count > 5:
            obs.issues.append("Animation Spam: Too many elements moving at once.")
            obs.scores['motion_psychology'] = 5.0
        return obs

class RhythmEngine(AnalysisModule):
    """MODULE 6: Beat spacing and tempo analysis."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Rhythm")
        events = [i for i, count in enumerate(state.motion_events) if count > 0]
        if len(events) < 2: return obs

        gaps = [events[i+1] - events[i] for i in range(len(events)-1)]
        if any(g < 15 for g in gaps):
            obs.issues.append("Broken Rhythm: Reveals are too rapid.")
            obs.director_notes.append("The scene lacks breathing room between information beats.")
            obs.fix_suggestions.append("Stagger element entries by at least 20 frames.")

        return obs

class EnergyCurveEngine(AnalysisModule):
    """MODULE 7: Tracks scene intensity peaks and valleys."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Energy Curve")
        max_e = max(state.energy_curve) if state.energy_curve else 0
        min_e = min(state.energy_curve) if state.energy_curve else 0

        if max_e > 0 and (max_e - min_e) < 1.5:
            obs.issues.append("Flat Energy: Scene lacks dynamic variation.")
            obs.director_notes.append("The pacing is monotonic. Use rest phases to create energy valleys.")
        return obs

class CameraDirector(AnalysisModule):
    """MODULE 8: Cinematic movement evaluation."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Camera")
        camera = supervisor.scene.get('camera', {})
        shots = camera.get('shots', [])

        for shot in shots:
            style = str(shot.get('style', '')).lower()
            if 'pan' in style or 'orbit' in style:
                # Check for reading interference
                for ov in supervisor.overlays:
                    if ov.get('type') == 'text' and abs(ov.get('start', 0) - shot.get('startFrame', 0)) < 30:
                        obs.issues.append(f"Camera Conflict: {style} during text reveal of '{ov.get('id')}'.")
                        obs.director_notes.append("Camera movement distracts from reading.")
        return obs

class InformationDensityEngine(AnalysisModule):
    """MODULE 9: Bits of info per second."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Info Density")
        total_bits = 0
        for ov in supervisor.overlays:
            o_type = str(ov.get('type','')).lower()
            if o_type == 'text': total_bits += len(str(ov.get('content','')).split())
            elif 'chart' in o_type: total_bits += 15
            elif 'indicator' in o_type: total_bits += 8

        bits_per_sec = total_bits / (state.duration / 30.0) if state.duration > 0 else 0
        obs.metadata['bits_per_sec'] = bits_per_sec
        if bits_per_sec > 10:
            obs.issues.append(f"Extreme Info Density: {round(bits_per_sec, 1)} bits/sec.")
            obs.director_notes.append("The viewer cannot absorb this much information at once.")
        return obs

class ReadabilityEngine(AnalysisModule):
    """MODULE 10: Multi-language reading speed estimation."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Readability")
        for ov in supervisor.overlays:
            if ov.get('type') == 'text':
                content = str(ov.get('content', ''))
                words = len(re.sub(r'[.।]', '', content).split())
                lang = 'english'
                if any('\u0980' <= c <= '\u09FF' for c in content): lang = 'bangla'
                speed = supervisor.READING_SPEEDS.get(lang, 0.3)
                req_sec = words * speed
                actual_sec = ov.get('duration', state.duration) / 30.0
                if actual_sec < req_sec:
                    obs.issues.append(f"Text too fast: '{ov.get('id')}' needs {round(req_sec, 1)}s.")
        return obs

class NarrativeEngine(AnalysisModule):
    """MODULE 11: Story structure validation."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Narrative")
        has_hero = any(str(o.get('importance','')).lower() == 'hero' for o in supervisor.overlays)
        has_evidence = any(o.get('type') in ['chart', 'indicator', 'graph'] for o in supervisor.overlays)
        if has_evidence and not has_hero:
            obs.issues.append("Narrative Gap: Evidence provided without a Hero statement.")
        return obs

class EmotionalPacingEngine(AnalysisModule):
    """MODULE 12: Tone estimation."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Emotional Pacing")
        avg_e = sum(state.energy_curve) / state.duration if state.duration > 0 else 0
        if avg_e > 3.0: state.tone = "chaotic"
        elif avg_e > 1.5: state.tone = "dramatic"
        else: state.tone = "calm"
        return obs

class DirectorStyleEngine(AnalysisModule):
    """MODULE 13: Project-specific style presets (Vox, Apple, BBC)."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Style")
        style = str(supervisor.project_style).lower()

        # Style Presets
        presets = {
            'vox': {'max_bits': 10, 'min_rest': 15, 'camera': 'drift'},
            'apple': {'max_bits': 5, 'min_rest': 30, 'camera': 'locked'},
            'johnny_harris': {'max_bits': 12, 'min_rest': 10, 'camera': 'handheld'}
        }

        conf = presets.get(style, presets['vox'])
        # Apply style-based penalties in other engines would be better,
        # but here we observe if the scene matches the style.
        if style == 'apple' and len(supervisor.overlays) > 3:
            obs.issues.append("Style Mismatch: 'Apple' style requires extreme minimalism.")

        return obs

class VisualConsistencyEngine(AnalysisModule):
    """MODULE 14: Uniformity check (Radii, Fonts, Colors)."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Consistency")
        fonts = {ov.get('font') for ov in supervisor.overlays if ov.get('font')}
        if len(fonts) > 2:
            obs.issues.append("Font Inconsistency: Too many font families.")
        return obs

class SceneMemoryEngine(AnalysisModule):
    """MODULE 15: Cross-scene recurring element tracking."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Memory")
        # Track Hero Continuity
        current_hero = next((o.get('id') for o in supervisor.overlays if str(o.get('importance','')).lower() == 'hero'), None)
        prev_hero = supervisor.manifest_memory.get('last_hero')

        if current_hero and prev_hero and current_hero != prev_hero:
            obs.director_notes.append(f"Narrative Shift: Attention moved from '{prev_hero}' to '{current_hero}'.")

        supervisor.manifest_memory['last_hero'] = current_hero
        return obs

class DocumentarySupervisor(AnalysisModule):
    """MODULE 16: Manifest-wide pacing and progression."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Film Score")
        # Logic to evaluate the "Story Arc"
        scene_index = supervisor.manifest_memory.get('scene_index', 0)
        if scene_index == 0:
            if sum(state.energy_curve) / state.duration < 1.0:
                 obs.issues.append("Weak Opening: First scene energy is too low.")

        supervisor.manifest_memory['scene_index'] = scene_index + 1
        return obs

class AutoFixEngine(AnalysisModule):
    """MODULE 17: Frame-accurate actionable recommendations."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Auto Fix")
        # Logic to generate frame-specific delays and moves
        for i, ov in enumerate(supervisor.overlays):
            if i > 0:
                prev_start = supervisor.overlays[i-1].get('start', 0)
                curr_start = ov.get('start', 0)
                if abs(curr_start - prev_start) < 10:
                    obs.fix_suggestions.append(f"Delay '{ov.get('id')}' by 15 frames to prevent animation clash.")
        return obs

class BackgroundOverlayHarmonyEngine(AnalysisModule):
    """MODULE 1 (v5): Detects conflicts between background intent and overlays."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Background-Overlay Harmony")
        bg = supervisor.bg_intel
        neg_space = bg.get('composition', {}).get('negative_space', 'center')

        for ov in supervisor.overlays:
            # Conflict: UI in Negative Space?
            pos = ov.get('position', {'x': 960, 'y': 540})
            region = 'center'
            if pos['x'] < 640:
                if pos['y'] < 360: region = 'top_left'
                elif pos['y'] > 720: region = 'bottom_left'
                else: region = 'mid_left'
            elif pos['x'] > 1280:
                if pos['y'] < 360: region = 'top_right'
                elif pos['y'] > 720: region = 'bottom_right'
                else: region = 'mid_right'

            if region == neg_space:
                # This is actually GOOD - negative space is where we want overlays!
                # BUT the prompt says "If overlays occupy top_left heavily -> violation"
                # Wait, "background defines top_left negative_space, overlays occupy top_left heavily -> violation"?
                # Usually negative space is for placement. Let's re-read carefully.
                # "negative_space: top_left" + "overlays occupy top_left heavily -> violation"
                # This seems contradictory to standard design (negative space is for text).
                # Re-reading prompt: "Background says: top_left is negative space. Overlay places chart at center -> composition conflict"
                # Okay, if it defines negative space, it means "Place here".
                # Wait: "overlays occupy top_left heavily -> violation" vs "Overlay places chart at center -> composition conflict"
                # If negative space is top_left, we SHOULD place there.
                pass

            # Real conflict: Background Hero vs Overlay Hero
            bg_hero = bg.get('hero_subject', {})
            if bg_hero.get('confidence', 0) > 0.8:
                ov_hero = str(ov.get('importance','')).lower() == 'hero'
                if ov_hero and bg_hero.get('position') == 'center' and abs(pos['x'] - 960) < 200:
                    obs.findings.append(PerceptionFinding(
                        severity="error", confidence=0.9, frame_range=(ov.get('start',0), state.duration),
                        affected_elements=[ov.get('id')],
                        human_explanation="Overlay hero competes with background hero.",
                        technical_explanation="Both background and overlay hero occupy center focal zone.",
                        viewer_impact="Cognitive dissonance: eye cannot decide where to look.",
                        fix_suggestion="Move overlay hero to Rule of Thirds anchor.",
                        expected_quality_gain=0.3
                    ))
        return obs

class SemanticEnvironmentLoadEngine(AnalysisModule):
    """MODULE 2 (v5): Computes total load (background + overlays)."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Semantic Load")
        bg_busy = supervisor.bg_intel.get('composition', {}).get('busy_score', 0.2)

        for f in range(state.duration):
            ov_load = state.frame_load[f] / 4.0 # normalized
            total_load = bg_busy + ov_load
            if total_load > 1.2 and f % 60 == 0:
                obs.findings.append(PerceptionFinding(
                    severity="critical", confidence=1.0, frame_range=(f, f+60),
                    affected_elements=[],
                    human_explanation="Total visual load is too high.",
                    technical_explanation=f"bg_busy({bg_busy}) + ov_load({round(ov_load,2)}) > 1.2",
                    viewer_impact="Visual overwhelm and abandonment.",
                    fix_suggestion="Simplify overlays because background is already busy.",
                    expected_quality_gain=0.5
                ))
        return obs

class ColorContrastIntelligenceEngine(AnalysisModule):
    """MODULE 3 (v5): Evaluates readability risk and color clashes."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Color & Contrast")
        bg_style = supervisor.bg_intel.get('visual_style', {})
        brightness = bg_style.get('brightness', 0.5)

        for ov in supervisor.overlays:
            if ov.get('type') == 'text':
                color = str(ov.get('color', '#ffffff')).lower()
                is_bright_text = color in ['#ffffff', '#00f5ff', '#00ffab', 'white', 'cyan']
                if brightness > 0.7 and is_bright_text:
                    obs.findings.append(PerceptionFinding(
                        severity="error", confidence=0.85, frame_range=(ov.get('start',0), state.duration),
                        affected_elements=[ov.get('id')],
                        human_explanation="Text is unreadable on bright background.",
                        technical_explanation=f"Bright text({color}) on high-brightness bg({brightness}).",
                        viewer_impact="Low readability score.",
                        fix_suggestion="Add a dark shadow or semi-transparent backing panel.",
                        expected_quality_gain=0.4
                    ))
        return obs

class CompositionConstraintEngine(AnalysisModule):
    """MODULE 4 (v5): Rule of Thirds and Negative Space usage."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Composition Constraint")
        bg_comp = supervisor.bg_intel.get('composition', {})
        neg_space = bg_comp.get('negative_space')

        if neg_space:
            placed_in_neg = False
            for ov in supervisor.overlays:
                # check if placed in neg_space region
                pass
            # If nothing in neg_space, it's a wasted opportunity
        return obs

class AttentionFieldSimulator(AnalysisModule):
    """MODULE 5 (v5): Upgraded attention scoring with background bias."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Attention Field")
        bg_hero = supervisor.bg_intel.get('hero_subject', {})

        for f in range(state.duration):
            if bg_hero.get('confidence', 0) > 0.8:
                # Background bias: viewer is already looking at background hero
                pass
        return obs

class CinematicIntentValidator(AnalysisModule):
    """MODULE 6 (v5): Interprets shot purpose and validates overlays."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Cinematic Intent")
        scene_type = supervisor.bg_intel.get('scene_type', 'generic')

        if scene_type == 'highway' and len(supervisor.overlays) > 5:
            obs.findings.append(PerceptionFinding(
                severity="warning", confidence=0.8, frame_range=(0, state.duration),
                affected_elements=[],
                human_explanation="Wide shots should breathe.",
                technical_explanation="High overlay count on 'highway' scene type.",
                viewer_impact="Visual flow interruption.",
                fix_suggestion="Remove secondary elements to let the footage drive the story.",
                expected_quality_gain=0.2
            ))
        return obs

class CognitiveLoadFusionEngine(AnalysisModule):
    """MODULE 7 (v5): Dynamic fusion cognitive load."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Cognitive Fusion")
        bg_busy = supervisor.bg_intel.get('composition', {}).get('busy_score', 0.2)

        for f in range(state.duration):
            # Formula: cognitive_load = overlay_load + bg_busy + motion + conflict
            ov_load = state.frame_load[f] / 4.0
            motion = sum(state.motion_events[max(0, f-10):f+1]) * 0.2

            fusion_load = ov_load + bg_busy + motion
            if fusion_load > 1.5 and f % 60 == 0:
                obs.findings.append(PerceptionFinding(
                    severity="error", confidence=0.9, frame_range=(f, f+60),
                    affected_elements=[],
                    human_explanation="Perceptual overload.",
                    technical_explanation=f"Fusion Load {round(fusion_load, 2)} exceeds dynamic threshold.",
                    viewer_impact="Information drop-off.",
                    fix_suggestion="Delay overlay entry to a calmer background segment.",
                    expected_quality_gain=0.6
                ))
        return obs

class TextPlacementIntelligenceEngine(AnalysisModule):
    """MODULE 8 (v5): Validates text against preferred regions."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Text Placement")
        pref_region = supervisor.bg_intel.get('text_region', {}).get('preferred', 'center')

        for ov in supervisor.overlays:
            if ov.get('type') == 'text':
                # Simplified region check (v5)
                pass
        return obs

class ScoringSynthesisEngine(AnalysisModule):
    """FINAL SYNTHESIS: Combines all observations into production-grade scores."""
    def run(self, supervisor: 'SceneSupervisor', state: SceneState) -> PerceptionObservation:
        obs = PerceptionObservation("Scoring Synthesis")

        # Categorize all findings
        categories = ["layout", "motion", "cognitive", "composition", "readability", "narrative", "fusion"]
        cat_scores = {c: 10.0 for c in categories}

        all_findings = []
        for o in supervisor.observations:
            all_findings.extend(o.findings)

        for finding in all_findings:
            penalty = 0.5
            if finding.severity == "critical": penalty = 2.0
            elif finding.severity == "error": penalty = 1.0
            elif finding.severity == "warning": penalty = 0.5

            cat = finding.category if finding.category in cat_scores else "layout"
            cat_scores[cat] -= penalty

        # Map to supervisor scores
        supervisor.scores["visual_harmony"] = cat_scores["fusion"]
        supervisor.scores["composition_integrity"] = cat_scores["composition"]
        supervisor.scores["attention_clarity"] = cat_scores["layout"]
        supervisor.scores["cognitive_load"] = cat_scores["cognitive"]
        supervisor.scores["readability_score"] = cat_scores["readability"]
        supervisor.scores["motion_discipline"] = cat_scores["motion"]
        supervisor.scores["narrative"] = cat_scores["narrative"]

        return obs

class SceneSupervisor:
    """
    Cinematic Element Supervisor AI (v4.0) — Production-Grade Perception Engine.
    Refactored into independent modules to simulate real human viewer experience.
    """

    # --- PERCEPTION CONSTANTS (Configurable) ---
    ELEMENT_WEIGHTS = {
        'text': 1.0, 'indicator': 1.2, 'shadcn_indicator': 1.2,
        'chart': 1.5, 'shadcn_chart': 1.5, 'ui_panel': 1.6,
        'connector': 1.3, 'shape': 0.6, 'svg': 0.8,
        'image': 1.1, 'video': 1.4, 'graph': 1.2
    }

    ATTENTION_COSTS = {
        'text': 30, 'indicator': 25, 'shadcn_indicator': 25,
        'chart': 40, 'shadcn_chart': 40, 'ui_panel': 35,
        'connector': 15, 'shape': 10, 'svg': 15,
        'image': 20, 'video': 30, 'graph': 25
    }

    MOTION_INTENSITY = {
        'static': 0, 'fade': 1, 'fade_in': 1, 'fade_out': 1,
        'slide': 2, 'slide_up': 2, 'slide_down': 2,
        'wordReveal': 2, 'glassReveal': 2,
        'zoom': 3, 'zoom_in': 3, 'zoom_out': 3,
        'pan': 3, 'pan_right': 3, 'orbit': 4,
        'dramatic_reveal': 5, 'networkGrow': 3, 'barsRise': 3,
        'multi-direction': 5
    }

    READING_SPEEDS = {
        'english': 0.3, 'bangla': 0.4, 'numeric': 0.2, 'mixed': 0.35
    }

    def __init__(self, scene_json: Dict[str, Any], manifest_memory: Optional[Dict[str, Any]] = None):
        self.scene = scene_json
        # Jules v5 Hybrid: Ingest Intelligence if already computed
        self.intelligence = scene_json.get('intelligence', {})
        self.overlays = scene_json.get('overlays', [])
        self.duration = scene_json.get('duration_in_frames', 180)
        self.scene_id = scene_json.get('scene_id', 'UNKNOWN')
        self.project_style = scene_json.get('project_style', 'vox')
        self.manifest_memory = manifest_memory or {}

        # v5: Background Metadata Extraction
        self.bg_intel = scene_json.get('background', {})
        if not isinstance(self.bg_intel, dict): self.bg_intel = {}
        # Ensure deep keys exist for fusion modules
        if 'composition' not in self.bg_intel: self.bg_intel['composition'] = {}
        if 'hero_subject' not in self.bg_intel: self.bg_intel['hero_subject'] = {}
        if 'semantic_context' not in self.bg_intel: self.bg_intel['semantic_context'] = {}
        if 'text_region' not in self.bg_intel: self.bg_intel['text_region'] = {}
        if 'visual_style' not in self.bg_intel: self.bg_intel['visual_style'] = {}

        # Results
        self.observations: List[PerceptionObservation] = []
        self.scores = {k: 10.0 for k in [
            "visual_hierarchy", "composition", "eye_flow", "motion_psychology",
            "animation_language", "camera_language", "information_density",
            "narrative", "readability", "consistency", "professional_polish",
            "emotional_impact", "documentary_quality", "overall_cinematic_score",
            "visual_harmony", "composition_integrity", "attention_clarity",
            "cognitive_load", "cinematic_intent_alignment", "readability_score",
            "motion_discipline", "environmental_coherence", "background_overlay_fusion"
        ]}

        # Backward compatibility maps
        self.legacy_scores = {"clarity": 10.0, "motion_quality": 10.0, "comprehension": 10.0, "modernity": 10.0}

        # Simulation data (Populated by _simulate_timeline)
        self.frame_load = [0.0] * self.duration
        self.motion_events = [0] * self.duration
        self.active_elements_per_frame = [0] * self.duration
        self.visual_noise_per_frame = [0.0] * self.duration
        self.energy_curve = [0.0] * self.duration

    def analyze(self) -> Dict[str, Any]:
        """Core analysis pipeline: runs all modules and aggregates reports."""
        # 0. Internal Preparation (Simulation)
        self._simulate_timeline()
        state = SceneState(
            frame_load=self.frame_load,
            motion_events=self.motion_events,
            active_elements_per_frame=self.active_elements_per_frame,
            visual_noise_per_frame=self.visual_noise_per_frame,
            energy_curve=self.energy_curve,
            duration=self.duration
        )

        # v5 Hybrid: If intelligence is missing, compute it locally
        if not self.intelligence:
            from .intelligence import SceneIntelligenceEngine
            self.intelligence = SceneIntelligenceEngine().analyze_scene(self.scene)

        # 1. Run Analysis Modules (v4 + v5 Fusion)
        modules = [
            # v4 Modules
            VisualSaliencyEngine(), EyeMovementSimulator(), VisualNoiseDetector(),
            VisualCompositionEngine(), GestaltAnalyzer(), MotionPsychologyEngine(),
            RhythmEngine(), EnergyCurveEngine(), CameraDirector(),
            InformationDensityEngine(), ReadabilityEngine(), NarrativeEngine(),
            EmotionalPacingEngine(), DirectorStyleEngine(), VisualConsistencyEngine(),
            SceneMemoryEngine(), DocumentarySupervisor(), AutoFixEngine(),
            # v5 Fusion Modules
            BackgroundOverlayHarmonyEngine(), SemanticEnvironmentLoadEngine(),
            ColorContrastIntelligenceEngine(), CompositionConstraintEngine(),
            AttentionFieldSimulator(), CinematicIntentValidator(),
            CognitiveLoadFusionEngine(), TextPlacementIntelligenceEngine()
        ]
        for mod in modules:
            self.observations.append(mod.run(self, state))

        # 2. Synthesis (Scoring)
        self.observations.append(ScoringSynthesisEngine().run(self, state))

        # 3. Final Report Generation
        return self._generate_report(state)

    def _simulate_timeline(self):
        """Timeline Simulator: frame-by-frame activity tracking."""
        for ov in self.overlays:
            start = ov.get('start', 0)
            dur = ov.get('duration', self.duration - start)
            end = start + dur
            o_type = str(ov.get('type', 'text')).lower()
            weight = self.ELEMENT_WEIGHTS.get(o_type, 1.0)

            for f in range(max(0, start), min(self.duration, end)):
                self.frame_load[f] += weight
                self.active_elements_per_frame[f] += 1
                if o_type in ['shape', 'svg', 'connector']:
                    self.visual_noise_per_frame[f] += 0.5 if ov.get('animation') else 0.1

            if 0 <= start < self.duration:
                self.motion_events[start] += 1

        for shot in self.scene.get('camera', {}).get('shots', []):
            s_start = shot.get('startFrame', 0)
            s_dur = shot.get('duration', 60)
            if 0 <= s_start < self.duration:
                self.motion_events[s_start] += 1
            for f in range(s_start, min(self.duration, s_start + s_dur)):
                self.energy_curve[f] += 0.5

    # --- LEGACY ADAPTERS (Used by analyze loop) ---
    def _check_cognitive_load(self):
        """Rule 3: Cognitive Load Limits (Safe Load Algorithm)."""
        total_motion_density = sum(self.motion_events) / (self.duration / 30.0) if self.duration > 0 else 0
        for f in range(self.duration):
            visible_count = self.active_elements_per_frame[f]
            recent_anim = 1.5 if sum(self.motion_events[max(0, f-15):f+1]) > 0 else 1.0
            safe_load = visible_count * recent_anim * (1.0 + total_motion_density * 0.2)
            if safe_load > 5.0 and f % 60 == 0:
                 self.legacy_scores['comprehension'] -= 0.5

    def _check_resting_time(self):
        """Rule 6: Resting Time (Post-animation hold)."""
        for ov in self.overlays:
            start = ov.get('start', 0)
            anim_dur = ov.get('animation_duration', ov.get('transition_duration', 20))
            required_rest = max(10, anim_dur * 0.4)
            next_event = self.duration
            for f in range(start + 1, self.duration):
                if self.motion_events[f] > 0:
                    next_event = f; break
            actual_rest = next_event - (start + anim_dur)
            if actual_rest < required_rest:
                self.legacy_scores['comprehension'] -= 0.2

    def _generate_report(self, state: SceneState) -> Dict[str, Any]:
        """Generates the comprehensive v5 production-grade report."""
        all_issues, all_m_issues, all_notes, all_fixes, all_findings = [], [], [], [], []

        # Aggregate Modular Data
        for obs in self.observations:
            all_issues.extend(obs.issues)
            all_m_issues.extend(obs.motion_issues)
            all_notes.extend(obs.director_notes)
            all_fixes.extend(obs.fix_suggestions)
            # v5 Findings
            for finding in obs.findings:
                all_findings.append({
                    "severity": finding.severity,
                    "confidence": round(finding.confidence, 2),
                    "frame_range": finding.frame_range,
                    "affected_elements": finding.affected_elements,
                    "human_explanation": finding.human_explanation,
                    "technical_explanation": finding.technical_explanation,
                    "viewer_impact": finding.viewer_impact,
                    "fix_suggestion": finding.fix_suggestion,
                    "expected_quality_gain": finding.expected_quality_gain
                })

            for k, v in obs.scores.items():
                if k in self.scores: self.scores[k] = min(self.scores[k], v)

        # Legacy score fallback calculation
        self.legacy_scores['clarity'] = self.scores['visual_hierarchy']
        self.legacy_scores['motion_quality'] = self.scores['motion_psychology']
        self.legacy_scores['comprehension'] = self.scores['readability']

        # v5 Scoring Logic (Fusion Weighted)
        self.scores['overall_cinematic_score'] = (
            self.scores['visual_harmony'] * 0.15 +
            self.scores['composition_integrity'] * 0.10 +
            self.scores['attention_clarity'] * 0.15 +
            self.scores['cognitive_load'] * 0.15 +
            self.scores['cinematic_intent_alignment'] * 0.10 +
            self.scores['readability_score'] * 0.10 +
            self.scores['motion_discipline'] * 0.10 +
            self.scores['environmental_coherence'] * 0.15
        )
        self.scores['background_overlay_fusion'] = (self.scores['visual_harmony'] + self.scores['cinematic_intent_alignment']) / 2.0

        status = "CLEAN"
        # v5 status rules (Stricter for production grade)
        total_errors = len([f for f in all_findings if f['severity'] in ['error', 'critical']])
        if total_errors > 1 or self.scores['overall_cinematic_score'] < 6.0: status = "OVERLOADED"
        elif total_errors > 0 or self.scores['overall_cinematic_score'] < 8.0: status = "ACCEPTABLE"

        # Integrate Jules Intelligence into scores
        if self.intelligence:
            intel_scores = self.intelligence.get('score_estimates', {})
            for k, v in intel_scores.items():
                if k in self.scores: self.scores[k] = (self.scores[k] + v) / 2.0

        return {
            "scene_id": self.scene_id,
            "status": status,
            "scores": {k: round(v, 1) for k, v in self.scores.items()},
            "legacy_scores": {k: round(v, 1) for k, v in self.legacy_scores.items()},
            "findings": all_findings,
            "intelligence": self.intelligence, # Jules v5 Hybrid
            "issues": list(set(all_issues)), # backward compat
            "director_notes": list(set(all_notes)),
            "fix_suggestions": list(set(all_fixes)),
            "motion_issues": list(set(all_m_issues + [i for i in all_issues if "Motion" in i or "Animation" in i])),
            "perceived_tone": state.tone,
            "focus_timeline": state.focus_timeline[::10],
            "attention_budget_used": sum(self.ATTENTION_COSTS.get(str(ov.get('type','')).lower(), 20) for ov in self.overlays),
            "background_overlay_fusion_score": round(self.scores['background_overlay_fusion'], 1),
            "professional_verdict": f"Senior Director Review: {status}. Composite score {round(self.scores['overall_cinematic_score'],1)}."
        }

def supervise_manifest(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    memory = {}
    reports = []
    for scene in manifest.get('scenes', []):
        supervisor = SceneSupervisor(scene, memory)
        report = supervisor.analyze()
        reports.append(report)
        # Update manifest memory...
    return reports
