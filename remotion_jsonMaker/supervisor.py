import json
import re
import math
from typing import Dict, Any, List, Tuple

class SceneSupervisor:
    """
    Cinematic Element Supervisor AI (v2.0)
    Cognitive-Aware Motion Graphics Compiler & Perception Judge.
    Evaluates scenes for comprehension, pacing, motion clarity, and cognitive load.
    """

    # PLAN 2: Element Weights
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

    # PLAN 2: Attention Costs
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

    # Motion intensity scores for total motion load
    MOTION_INTENSITY = {
        'static': 0,
        'fade_in': 1, 'fade_out': 1,
        'slide_up': 2, 'slide_down': 2,
        'wordReveal': 2, 'glassReveal': 2,
        'zoom_in': 3, 'zoom_out': 3, 'pan_right': 3,
        'orbit': 4,
        'dramatic_reveal': 5,
        'networkGrow': 3, 'barsRise': 3
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

        # Simulation data
        self.frame_load = [0.0] * self.duration
        self.motion_events = [0] * self.duration # Count of start animations per frame
        self.active_elements_per_frame = [0] * self.duration

    def analyze(self) -> Dict[str, Any]:
        """Runs all supervisor modules (Rules 1-8) and returns a perception report."""
        self._simulate_timeline()

        self._check_structure_and_hierarchy() # Rule 4
        self._check_time_aware_limits()       # Rule 2
        self._check_cognitive_load()          # Rule 3
        self._check_motion_intelligence()     # Rule 5, 7
        self._check_comprehension_rules()     # Rule 1, 8
        self._check_resting_time()            # Rule 6

        # Scoring & Normalization
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

    def _simulate_timeline(self):
        """Timeline Simulator: frame-by-frame visibility and motion tracking."""
        for ov in self.overlays:
            start = ov.get('start', 0)
            dur = ov.get('duration', self.duration - start)
            end = start + dur
            o_type = str(ov.get('type', 'text')).lower()
            weight = self.ELEMENT_WEIGHTS.get(o_type, 1.0)

            for f in range(max(0, start), min(self.duration, end)):
                self.frame_load[f] += weight
                self.active_elements_per_frame[f] += 1

            if 0 <= start < self.duration:
                self.motion_events[start] += 1

        # Incorporate camera shots into motion events
        for shot in self.scene.get('camera', {}).get('shots', []):
            s_start = shot.get('startFrame', 0)
            if 0 <= s_start < self.duration:
                self.motion_events[s_start] += 1

    def _check_structure_and_hierarchy(self):
        """Rule 4: Visual Hierarchy (Single Hero)."""
        if len(self.overlays) > 7:
            self.issues.append(f"Element count too high ({len(self.overlays)}). Max 7 recommended.")
            self.scores['clarity'] -= 1.0

        heroes = [o for o in self.overlays if str(o.get('importance', '')).lower() == 'hero']
        if len(heroes) > 1:
            self.issues.append(f"Attention conflict: {len(heroes)} HERO elements detected. Only 1 allowed.")
            self.scores['clarity'] -= 2.0
            self.fix_suggestions.append("Consolidate focus: downgrade secondary heroes to 'secondary' importance.")
        elif len(heroes) == 0:
            # If no explicit hero, check for competing hero_configs
            h_configs = [o for o in self.overlays if o.get('hero_config')]
            if len(h_configs) > 1:
                self.issues.append("Split focus: multiple elements using hero_config simultaneously.")
                self.scores['clarity'] -= 1.0

    def _check_time_aware_limits(self):
        """Rule 2: Time-Aware Video Limits (5s vs 10s vs 30s)."""
        sec = self.duration / 30.0

        if sec <= 5.1: # 5 Second Shot
            charts = [o for o in self.overlays if 'chart' in str(o.get('type',''))]
            if len(charts) > 0:
                self.issues.append("5s scene is too short for a Chart. Viewer needs 2.5s+ to process data.")
                self.fix_suggestions.append("Increase scene duration to 8s+ or remove the chart.")
            if len(self.overlays) > 3:
                self.issues.append(f"Too many overlays ({len(self.overlays)}) for a 5s window. Max 2-3 allowed.")

        elif sec <= 10.1: # 10 Second Beat
            if len(self.overlays) > 5:
                self.issues.append(f"10s scene crowded with {len(self.overlays)} elements. Max 4-5 recommended.")

        # Visual rest zones for long scenes (Rule 2: 30s+)
        if sec >= 25:
            # Check for gaps of low motion (visual rest zones)
            has_rest_zone = False
            for i in range(0, self.duration - 60): # Check 2s windows
                if sum(self.motion_events[i : i+60]) == 0:
                    has_rest_zone = True; break
            if not has_rest_zone:
                self.issues.append("Long scene (30s+) missing a visual rest zone (2s gap with no new animations).")
                self.fix_suggestions.append("Insert a 2-second breathing phase with no new elements or camera shifts.")

    def _check_cognitive_load(self):
        """Rule 3: Cognitive Load Limits (Safe Load & Attention Budget)."""
        max_load = max(self.frame_load) if self.frame_load else 0
        if max_load > 4.0:
            self.issues.append(f"Peak cognitive load ({round(max_load,1)}) exceeds safe limit (4.0). Scene becomes unwatchable.")
            self.scores['comprehension'] -= 2.0

        budget = self._calculate_attention_budget()
        if budget > 100:
            self.issues.append(f"Attention budget exceeded ({budget}/100). Total complexity too high.")
            self.scores['comprehension'] -= 1.5
            self.fix_suggestions.append("Reduce the number of focal elements (indicators/charts) to lower attention cost.")

    def _check_motion_intelligence(self):
        """Rule 5 & 7: Motion Purpose & Clash Rule."""
        # Rule 7: Motion Clash (Max 1 primary + 1 secondary animation at once)
        for f, count in enumerate(self.motion_events):
            if count > 2:
                self.motion_issues.append(f"Motion chaos at frame {f}: {count} simultaneous animations.")
                if len(self.motion_issues) == 1:
                    self.issues.append("Motion clash detected: too many elements animating at the same time.")
                self.scores['motion_quality'] -= 0.5

        # Rule 5: Decorative motion misuse
        has_info = any(o.get('type') in ['chart', 'shadcn_chart', 'indicator'] for o in self.overlays)
        for ov in self.overlays:
            if ov.get('type') == 'shape' and ov.get('animation') not in [None, 'static', 'fade_in']:
                if has_info:
                    self.motion_issues.append(f"Decorative motion on '{ov.get('id')}' distracts from data-heavy scene.")
                    self.scores['motion_quality'] -= 1.0
                    self.fix_suggestions.append(f"Change '{ov.get('id')}' animation to a simple fade or static.")

    def _check_comprehension_rules(self):
        """Rule 1 & 8: Visibility Limits & Attention Flow."""
        # Rule 1: Minimum Visibility
        for ov in self.overlays:
            o_type = str(ov.get('type','')).lower()
            o_id = ov.get('id','unknown')
            frames = ov.get('duration', self.duration)
            sec = frames / 30.0

            if o_type == 'text':
                words = len(re.sub(r'[.।]', '', str(ov.get('content',''))).split())
                req_sec = words * 0.3
                if sec < req_sec:
                    self.issues.append(f"Readability failure: Text '{o_id}' visible for {round(sec,1)}s, needs {round(req_sec,1)}s.")
                    self.scores['comprehension'] -= 1.5
            elif 'chart' in o_type and sec < 2.5:
                self.issues.append(f"Comprehension failure: Chart '{o_id}' disappears too fast ({round(sec,1)}s). Min 2.5s required.")
                self.scores['comprehension'] -= 1.0
            elif 'indicator' in o_type and sec < 1.5:
                self.issues.append(f"Comprehension failure: Indicator '{o_id}' visible for {round(sec,1)}s. Min 1.5s required.")
                self.scores['comprehension'] -= 0.5

        # Rule 8: Attention Flow (Focus stabilization >= 1.5s)
        # Find time between sequential primary reveals
        primary_starts = sorted([o.get('start',0) for o in self.overlays if o.get('importance','').lower() in ['hero', 'primary']])
        for i in range(len(primary_starts)-1):
            gap = (primary_starts[i+1] - primary_starts[i]) / 30.0
            if gap < 1.5:
                self.comprehension_breakpoints.append(f"Cognitive fragmentation: primary focus shifts too fast ({round(gap,1)}s).")
                self.scores['comprehension'] -= 1.0
                self.fix_suggestions.append("Slow down: allow at least 1.5s between primary element entries.")

    def _check_resting_time(self):
        """Rule 6: Resting Time (Post-animation hold)."""
        for ov in self.overlays:
            start = ov.get('start', 0)
            anim_dur = 20 # Standard entrance duration estimate
            required_rest = max(10, anim_dur * 0.4)

            # Find next significant motion event
            next_event = self.duration
            for f in range(start + 1, self.duration):
                if self.motion_events[f] > 0:
                    next_event = f; break

            actual_rest = next_event - (start + anim_dur)
            if actual_rest < required_rest:
                self.resting_time_violations.append(f"'{ov.get('id')}' lacks rest phase after reveal. Found {int(actual_rest)}f, need {int(required_rest)}f.")
                self.scores['comprehension'] -= 0.5

    def _calculate_attention_budget(self) -> int:
        return sum(self.ATTENTION_COSTS.get(str(ov.get('type','')).lower(), 20) for ov in self.overlays)

    def _generate_simplified_version(self) -> str:
        heroes = [o for o in self.overlays if str(o.get('importance', '')).lower() == 'hero']
        target = heroes[0].get('id') if heroes else "Main Focus"
        return f"Single focus: '{target}' reveal + hold + minimal background motion."

def supervise_manifest(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    reports = []
    for scene in manifest.get('scenes', []):
        reports.append(SceneSupervisor(scene).analyze())
    return reports
