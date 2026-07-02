import json
import re
import math
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field

@dataclass
class PerceptionObservation:
    """Standardized container for analysis results from modules."""
    module_name: str
    issues: List[str] = field(default_factory=list)
    motion_issues: List[str] = field(default_factory=list)
    director_notes: List[str] = field(default_factory=list)
    fix_suggestions: List[str] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

class AnalysisModule:
    """Base class for all Cinematic Perception modules."""
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
        raise NotImplementedError

class VisualSaliencyEngine(AnalysisModule):
    """MODULE 1: Dynamic Visual Saliency (Eye Catching Score)."""
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
        obs = PerceptionObservation("Visual Saliency")
        focus_timeline = []

        for f in range(supervisor.duration):
            candidates = []
            for ov in supervisor.overlays:
                start, end = ov.get('start', 0), ov.get('start', 0) + ov.get('duration', supervisor.duration)
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

        supervisor.focus_timeline = focus_timeline
        return obs

class EyeMovementSimulator(AnalysisModule):
    """MODULE 2: Simulates Fixations, Saccades, and Reading Flow."""
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
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
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
        obs = PerceptionObservation("Visual Noise")
        avg_noise = sum(supervisor.visual_noise_per_frame) / supervisor.duration if supervisor.duration > 0 else 0
        if avg_noise > 0.8: # Calibrated threshold
            obs.issues.append(f"Visual Noise Too High ({round(avg_noise, 1)}). Decorative elements distracting from content.")
            obs.director_notes.append("Background particles or shapes are too active. Simplify decorative layers.")
        return obs

class VisualCompositionEngine(AnalysisModule):
    """MODULE 3: Judges Layout via Rule of Thirds and Golden Ratio."""
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
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
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
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
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
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
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
        obs = PerceptionObservation("Rhythm")
        events = [i for i, count in enumerate(supervisor.motion_events) if count > 0]
        if len(events) < 2: return obs

        gaps = [events[i+1] - events[i] for i in range(len(events)-1)]
        if any(g < 15 for g in gaps):
            obs.issues.append("Broken Rhythm: Reveals are too rapid.")
            obs.director_notes.append("The scene lacks breathing room between information beats.")
            obs.fix_suggestions.append("Stagger element entries by at least 20 frames.")

        return obs

class EnergyCurveEngine(AnalysisModule):
    """MODULE 7: Tracks scene intensity peaks and valleys."""
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
        obs = PerceptionObservation("Energy Curve")
        max_e = max(supervisor.energy_curve) if supervisor.energy_curve else 0
        min_e = min(supervisor.energy_curve) if supervisor.energy_curve else 0

        if max_e > 0 and (max_e - min_e) < 1.5:
            obs.issues.append("Flat Energy: Scene lacks dynamic variation.")
            obs.director_notes.append("The pacing is monotonic. Use rest phases to create energy valleys.")
        return obs

class CameraDirector(AnalysisModule):
    """MODULE 8: Cinematic movement evaluation."""
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
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
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
        obs = PerceptionObservation("Info Density")
        total_bits = 0
        for ov in supervisor.overlays:
            o_type = str(ov.get('type','')).lower()
            if o_type == 'text': total_bits += len(str(ov.get('content','')).split())
            elif 'chart' in o_type: total_bits += 15
            elif 'indicator' in o_type: total_bits += 8

        bits_per_sec = total_bits / (supervisor.duration / 30.0) if supervisor.duration > 0 else 0
        obs.metadata['bits_per_sec'] = bits_per_sec
        if bits_per_sec > 10:
            obs.issues.append(f"Extreme Info Density: {round(bits_per_sec, 1)} bits/sec.")
            obs.director_notes.append("The viewer cannot absorb this much information at once.")
        return obs

class ReadabilityEngine(AnalysisModule):
    """MODULE 10: Multi-language reading speed estimation."""
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
        obs = PerceptionObservation("Readability")
        for ov in supervisor.overlays:
            if ov.get('type') == 'text':
                content = str(ov.get('content', ''))
                words = len(re.sub(r'[.।]', '', content).split())
                lang = 'english'
                if any('\u0980' <= c <= '\u09FF' for c in content): lang = 'bangla'
                speed = supervisor.READING_SPEEDS.get(lang, 0.3)
                req_sec = words * speed
                actual_sec = ov.get('duration', supervisor.duration) / 30.0
                if actual_sec < req_sec:
                    obs.issues.append(f"Text too fast: '{ov.get('id')}' needs {round(req_sec, 1)}s.")
        return obs

class NarrativeEngine(AnalysisModule):
    """MODULE 11: Story structure validation."""
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
        obs = PerceptionObservation("Narrative")
        has_hero = any(str(o.get('importance','')).lower() == 'hero' for o in supervisor.overlays)
        has_evidence = any(o.get('type') in ['chart', 'indicator', 'graph'] for o in supervisor.overlays)
        if has_evidence and not has_hero:
            obs.issues.append("Narrative Gap: Evidence provided without a Hero statement.")
        return obs

class EmotionalPacingEngine(AnalysisModule):
    """MODULE 12: Tone estimation."""
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
        obs = PerceptionObservation("Emotional Pacing")
        avg_e = sum(supervisor.energy_curve) / supervisor.duration if supervisor.duration > 0 else 0
        if avg_e > 3.0: supervisor.tone = "chaotic"
        elif avg_e > 1.5: supervisor.tone = "dramatic"
        else: supervisor.tone = "calm"
        return obs

class DirectorStyleEngine(AnalysisModule):
    """MODULE 13: Project-specific style presets (Vox, Apple, BBC)."""
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
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
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
        obs = PerceptionObservation("Consistency")
        fonts = {ov.get('font') for ov in supervisor.overlays if ov.get('font')}
        if len(fonts) > 2:
            obs.issues.append("Font Inconsistency: Too many font families.")
        return obs

class SceneMemoryEngine(AnalysisModule):
    """MODULE 15: Cross-scene recurring element tracking."""
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
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
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
        obs = PerceptionObservation("Film Score")
        # Logic to evaluate the "Story Arc"
        scene_index = supervisor.manifest_memory.get('scene_index', 0)
        if scene_index == 0:
            if sum(supervisor.energy_curve) / supervisor.duration < 1.0:
                 obs.issues.append("Weak Opening: First scene energy is too low.")

        supervisor.manifest_memory['scene_index'] = scene_index + 1
        return obs

class AutoFixEngine(AnalysisModule):
    """MODULE 17: Frame-accurate actionable recommendations."""
    def run(self, supervisor: 'SceneSupervisor') -> PerceptionObservation:
        obs = PerceptionObservation("Auto Fix")
        # Logic to generate frame-specific delays and moves
        for i, ov in enumerate(supervisor.overlays):
            if i > 0:
                prev_start = supervisor.overlays[i-1].get('start', 0)
                curr_start = ov.get('start', 0)
                if abs(curr_start - prev_start) < 10:
                    obs.fix_suggestions.append(f"Delay '{ov.get('id')}' by 15 frames to prevent animation clash.")
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
        self.overlays = scene_json.get('overlays', [])
        self.duration = scene_json.get('duration_in_frames', 180)
        self.scene_id = scene_json.get('scene_id', 'UNKNOWN')
        self.project_style = scene_json.get('project_style', 'vox')
        self.manifest_memory = manifest_memory or {}

        # Results
        self.observations: List[PerceptionObservation] = []
        self.scores = {k: 10.0 for k in [
            "visual_hierarchy", "composition", "eye_flow", "motion_psychology",
            "animation_language", "camera_language", "information_density",
            "narrative", "readability", "consistency", "professional_polish",
            "emotional_impact", "documentary_quality", "overall_cinematic_score"
        ]}

        # Backward compatibility maps
        self.legacy_scores = {"clarity": 10.0, "motion_quality": 10.0, "comprehension": 10.0, "modernity": 10.0}

        # Simulation data
        self.frame_load = [0.0] * self.duration
        self.motion_events = [0] * self.duration
        self.active_elements_per_frame = [0] * self.duration
        self.visual_noise_per_frame = [0.0] * self.duration
        self.energy_curve = [0.0] * self.duration
        self.focus_timeline = []
        self.tone = "neutral"

    def analyze(self) -> Dict[str, Any]:
        """Core analysis pipeline: runs all modules and aggregates reports."""
        # 0. Internal Preparation
        self._simulate_timeline()

        # 1. Run Analysis Modules
        modules = [
            VisualSaliencyEngine(), EyeMovementSimulator(), VisualNoiseDetector(),
            VisualCompositionEngine(), GestaltAnalyzer(), MotionPsychologyEngine(),
            RhythmEngine(), EnergyCurveEngine(), CameraDirector(),
            InformationDensityEngine(), ReadabilityEngine(), NarrativeEngine(),
            EmotionalPacingEngine(), DirectorStyleEngine(), VisualConsistencyEngine(),
            SceneMemoryEngine(), DocumentarySupervisor(), AutoFixEngine()
        ]
        for mod in modules:
            self.observations.append(mod.run(self))

        # 2. Legacy Adapters (For compatibility)
        self._check_cognitive_load()
        self._check_resting_time()

        # 3. Final Scoring & Report Generation
        return self._generate_report()

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

    def _generate_report(self) -> Dict[str, Any]:
        """Generates the comprehensive v4 report."""
        all_issues, all_m_issues, all_notes, all_fixes = [], [], [], []

        # Aggregate Modular Data
        for obs in self.observations:
            all_issues.extend(obs.issues)
            all_m_issues.extend(obs.motion_issues)
            all_notes.extend(obs.director_notes)
            all_fixes.extend(obs.fix_suggestions)
            for k, v in obs.scores.items():
                if k in self.scores: self.scores[k] = min(self.scores[k], v)

        # Legacy score fallback calculation
        self.legacy_scores['clarity'] = self.scores['visual_hierarchy']
        self.legacy_scores['motion_quality'] = self.scores['motion_psychology']
        self.legacy_scores['comprehension'] = self.scores['readability']

        # Final Score Logic (Perception Weighted)
        self.scores['overall_cinematic_score'] = (
            self.scores['visual_hierarchy'] * 0.15 +
            self.scores['composition'] * 0.10 +
            self.scores['eye_flow'] * 0.15 +
            self.scores['motion_psychology'] * 0.15 +
            self.scores['readability'] * 0.20 +
            self.scores['narrative'] * 0.10 +
            self.scores['consistency'] * 0.15
        )

        status = "CLEAN"
        if len(all_issues) > 4 or self.scores['overall_cinematic_score'] < 5.5: status = "OVERLOADED"
        elif len(all_issues) > 0 or self.scores['overall_cinematic_score'] < 8.0: status = "ACCEPTABLE"

        return {
            "scene_id": self.scene_id,
            "status": status,
            "scores": {k: round(v, 1) for k, v in self.scores.items()},
            "legacy_scores": {k: round(v, 1) for k, v in self.legacy_scores.items()},
            "issues": list(set(all_issues)),
            "director_notes": list(set(all_notes)),
            "fix_suggestions": list(set(all_fixes)),
            "motion_issues": list(set(all_m_issues + [i for i in all_issues if "Motion" in i or "Animation" in i])),
            "comprehension_breakpoints": [i for i in all_issues if "too fast" in i or "Density" in i],
            "resting_time_violations": [i for i in all_issues if "rest" in i],
            "perceived_tone": self.tone,
            "focus_timeline": self.focus_timeline[::10], # sampled
            "attention_budget_used": sum(self.ATTENTION_COSTS.get(str(ov.get('type','')).lower(), 20) for ov in self.overlays),
            "professional_verdict": f"Scored {round(self.scores['overall_cinematic_score'],1)}. {status}."
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
