import json
import re
import math
from typing import Dict, Any, List, Tuple

class SceneSupervisor:
    """
    Cognitive-Aware Motion Graphics Compiler & Supervisor.
    Evaluates scenes for comprehension, pacing, motion clarity, and aesthetic consistency.
    """

    ELEMENT_WEIGHTS = {
        'text': 1.0,
        'indicator': 1.2,
        'shadcn_indicator': 1.2,
        'chart': 1.5,
        'shadcn_chart': 1.5,
        'ui_panel': 1.6,
        'connector': 1.3,
        'shape': 0.6,
        'svg': 0.8,
        'image': 1.1,
        'video': 1.4,
        'graph': 1.2
    }

    ATTENTION_COSTS = {
        'text': 30,
        'indicator': 25,
        'shadcn_indicator': 25,
        'chart': 40,
        'shadcn_chart': 40,
        'ui_panel': 35,
        'connector': 15,
        'shape': 10,
        'svg': 15,
        'image': 20,
        'video': 30,
        'graph': 25
    }

    MOTION_SCORES = {
        'static': 0,
        'fade_in': 1,
        'fade_out': 1,
        'slide_up': 2,
        'slide_down': 2,
        'wordReveal': 2,
        'glassReveal': 2,
        'zoom_in': 3,
        'zoom_out': 3,
        'pan_right': 3,
        'orbit': 4,
        'dramatic_reveal': 5,
        'networkGrow': 3,
        'barsRise': 3
    }

    def __init__(self, scene_json: Dict[str, Any]):
        self.scene = scene_json
        self.overlays = scene_json.get('overlays', [])
        self.duration = scene_json.get('duration_in_frames', 180)
        self.scene_id = scene_json.get('scene_id', 'UNKNOWN')

        # Reports
        self.issues = []
        self.motion_issues = []
        self.comprehension_breakpoints = []
        self.resting_time_violations = []
        self.fix_suggestions = []
        self.scores = {
            "clarity": 10.0,
            "motion_quality": 10.0,
            "comprehension": 10.0,
            "modernity": 10.0
        }

    def analyze(self) -> Dict[str, Any]:
        """Runs all supervisor modules and returns a comprehensive report."""
        self._module_structure_analyzer()
        self._module_timeline_simulator()
        self._module_cognitive_load_engine()
        self._module_motion_intelligence()
        self._module_comprehension_engine()
        self._module_resting_time_engine()

        # Normalize scores to 0-10
        for k in self.scores:
            self.scores[k] = max(0.0, min(10.0, round(self.scores[k], 1)))

        status = "CLEAN"
        if len(self.issues) > 3 or self.scores['comprehension'] < 6:
            status = "OVERLOADED"
        elif len(self.issues) > 0 or self.scores['comprehension'] < 8:
            status = "ACCEPTABLE"

        return {
            "scene_id": self.scene_id,
            "status": status,
            "scores": self.scores,
            "issues": self.issues,
            "motion_issues": self.motion_issues,
            "comprehension_breakpoints": self.comprehension_breakpoints,
            "resting_time_violations": self.resting_time_violations,
            "attention_budget_used": self._calculate_attention_budget(),
            "fix_suggestions": list(set(self.fix_suggestions)),
            "simplified_version": self._generate_simplified_version()
        }

    def _module_structure_analyzer(self):
        """Checks overlay count, hierarchy, and basic structure."""
        if len(self.overlays) > 7:
            self.issues.append(f"High overlay count ({len(self.overlays)}). Risk of cognitive clutter.")
            self.scores['clarity'] -= 1.5

        # Hierarchy check: count 'hero' elements
        heroes = [o for o in self.overlays if str(o.get('importance', '')).lower() == 'hero']
        if len(heroes) > 1:
            self.issues.append(f"Multiple PRIMARY elements detected ({len(heroes)}). Only one HERO allowed per scene.")
            self.scores['clarity'] -= 2.0
            self.fix_suggestions.append("Downgrade secondary heroes to 'secondary' importance.")
        elif len(heroes) == 0:
            # Check if any element has hero_config
            hero_configs = [o for o in self.overlays if o.get('hero_config')]
            if len(hero_configs) > 1:
                self.issues.append("Multiple elements with hero_config. Focus is split.")
                self.scores['clarity'] -= 1.0

        # Z-Index check
        z_indices = [o.get('zIndex', 0) for o in self.overlays]
        if len(z_indices) != len(set(z_indices)) and len(z_indices) > 0:
            self.issues.append("Z-index collision: multiple layers on same depth.")
            self.fix_suggestions.append("Stagger zIndex values to ensure proper layering.")

    def _module_timeline_simulator(self):
        """Simulates frame-by-frame activity."""
        self.frame_load = [0] * self.duration
        self.motion_events = [0] * self.duration

        for ov in self.overlays:
            start = ov.get('start', 0)
            end = start + ov.get('duration', self.duration - start)
            o_type = str(ov.get('type', 'text')).lower()
            weight = self.ELEMENT_WEIGHTS.get(o_type, 1.0)

            for f in range(max(0, start), min(self.duration, end)):
                self.frame_load[f] += weight

            # Animation events (entry)
            if 0 <= start < self.duration:
                self.motion_events[start] += 1

        # Camera shots as motion events
        for shot in self.scene.get('camera', {}).get('shots', []):
            s_start = shot.get('startFrame', 0)
            if 0 <= s_start < self.duration:
                self.motion_events[s_start] += 1

    def _module_cognitive_load_engine(self):
        """Calculates attention budget and frame-based overload."""
        max_load = max(self.frame_load) if self.frame_load else 0
        if max_load > 4.0:
            self.issues.append(f"Peak cognitive load too high ({round(max_load, 2)}). Scene is unwatchable at peaks.")
            self.scores['comprehension'] -= 2.5

        budget = self._calculate_attention_budget()
        if budget > 100:
            self.issues.append(f"Attention budget exceeded ({budget}/100).")
            self.scores['comprehension'] -= 1.5
            self.fix_suggestions.append("Remove low-priority indicators or shapes to free attention budget.")

    def _module_motion_intelligence(self):
        """Checks motion purpose, density, and conflicts."""
        total_events = sum(self.motion_events)
        density = total_events / (self.duration / 30.0) # events per second

        if density > 0.9:
            self.motion_issues.append(f"Motion density too high ({round(density, 2)}). Scene feels chaotic.")
            self.scores['motion_quality'] -= 3.0
            self.scores['comprehension'] -= 2.0
        elif density < 0.3:
            # cinematic/calm is good, but if too low it might be boring? user says <0.3 is cinematic.
            pass

        # Decoration vs Info check
        is_info_heavy = any(o.get('type') in ['chart', 'shadcn_chart', 'indicator'] for o in self.overlays)
        has_decoration_motion = False
        for ov in self.overlays:
            if ov.get('type') == 'shape' and ov.get('animation') not in [None, 'static', 'fade_in']:
                has_decoration_motion = True
                break

        if is_info_heavy and has_decoration_motion:
            self.motion_issues.append("Decorative motion (shapes) overlaps with information-heavy content.")
            self.scores['motion_quality'] -= 1.5
            self.fix_suggestions.append("Freeze background shapes or use simple fades during data reveals.")

    def _module_comprehension_engine(self):
        """Detects event clustering and readability."""
        # Check 1.5s windows (45 frames at 30fps)
        window_size = 45
        for f in range(self.duration - window_size):
            events_in_window = sum(self.motion_events[f : f + window_size])
            if events_in_window > 3:
                self.comprehension_breakpoints.append(
                    f"Frame {f}-{f+window_size}: {events_in_window} events in {round(window_size/30.0, 1)}s window"
                )
                if len(self.comprehension_breakpoints) == 1: # Only flag once for issues
                    self.issues.append("Visual events are clustered too tightly. Viewer cannot process simultaneous changes.")
                self.scores['comprehension'] -= 0.5

        # Readability check
        for ov in self.overlays:
            if ov.get('type') == 'text':
                content = str(ov.get('content', ''))
                words = len(re.sub(r'[.।]', '', content).split())
                if words == 0: continue

                # Rule: 0.3s per word
                required_duration = words * 0.3 * 30
                actual_duration = ov.get('duration', self.duration)

                if actual_duration < required_duration:
                    self.issues.append(f"Text '{ov.get('id')}' disappears too fast for reading speed.")
                    self.scores['comprehension'] -= 1.0
                    self.fix_suggestions.append(f"Increase duration of '{ov.get('id')}' to at least {int(required_duration)} frames.")

    def _module_resting_time_engine(self):
        """Ensures viewer has time to absorb meaning after animations."""
        for i, ov in enumerate(self.overlays):
            o_id = ov.get('id', f'ov_{i}')
            # Estimate animation duration (default 20f if not specified)
            anim_dur = 20 # Standard entrance
            req_rest = anim_dur * 0.4

            # Find next event after this overlay's start
            start = ov.get('start', 0)
            next_event_frame = self.duration
            for f in range(start + 1, self.duration):
                if self.motion_events[f] > 0:
                    next_event_frame = f
                    break

            actual_rest = next_event_frame - (start + anim_dur)
            if actual_rest < req_rest and actual_rest < 10: # Allow some leniency
                self.resting_time_violations.append(
                    f"{o_id} has only {int(actual_rest)} frames rest after reveal (required: {int(req_rest)})"
                )
                self.scores['comprehension'] -= 0.5
                self.fix_suggestions.append(f"Add a brief hold (min {int(req_rest)}f) after {o_id} finishes its reveal animation.")

    def _calculate_attention_budget(self) -> int:
        total = 0
        for ov in self.overlays:
            o_type = str(ov.get('type', 'text')).lower()
            total += self.ATTENTION_COSTS.get(o_type, 20)
        return total

    def _generate_simplified_version(self) -> str:
        heroes = [o for o in self.overlays if str(o.get('importance', '')).lower() == 'hero']
        hero_id = heroes[0].get('id') if heroes else "Main Subject"
        return f"Single focus: '{hero_id}' reveal + slow cinematic drift + resting phases."

def supervise_manifest(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    reports = []
    for scene in manifest.get('scenes', []):
        supervisor = SceneSupervisor(scene)
        reports.append(supervisor.analyze())
    return reports
