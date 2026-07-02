import json
import re
import math
from typing import Dict, Any, List, Tuple

class SceneSupervisor:
    """
    Cinematic Element Supervisor AI (v3.0) — Cinematic Perception Engine.
    Behaves like a creative director, simulating real-time human perception.
    """

    # --- PERCEPTION CONSTANTS ---
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
        'fade': 1, 'fade_in': 1, 'fade_out': 1,
        'slide': 2, 'slide_up': 2, 'slide_down': 2,
        'wordReveal': 2, 'glassReveal': 2,
        'zoom': 3, 'zoom_in': 3, 'zoom_out': 3,
        'pan': 3, 'pan_right': 3,
        'orbit': 4,
        'dramatic_reveal': 5,
        'networkGrow': 3, 'barsRise': 3,
        'multi-direction': 5
    }

    # Reading speeds (seconds per word)
    READING_SPEEDS = {
        'english': 0.3,
        'bangla': 0.4, # Slightly slower for complex scripts
        'numeric': 0.2, # Fast scanning
        'mixed': 0.35
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
        self.director_notes = []

        self.scores = {
            "clarity": 10.0,
            "motion_quality": 10.0,
            "comprehension": 10.0,
            "modernity": 10.0,
            "visual_hierarchy": 10.0,
            "eye_flow": 10.0,
            "motion_rhythm": 10.0,
            "information_density": 10.0,
            "camera_quality": 10.0,
            "narrative_strength": 10.0,
            "overall_cinematic_score": 10.0
        }

        # Internal Simulation data
        self.frame_load = [0.0] * self.duration
        self.motion_events = [0] * self.duration
        self.active_elements_per_frame = [0] * self.duration
        self.visual_noise_per_frame = [0.0] * self.duration
        self.energy_curve = [0.0] * self.duration
        self.focus_data = [] # List of {frame, focus_target, focus_strength, focus_competitors}

    def analyze(self) -> Dict[str, Any]:
        """Runs all supervisor modules (Rules 1-8 + Perception Engine) and returns a report."""
        self._simulate_timeline()

        # Perception Engine
        self._simulate_visual_focus()
        self._simulate_eye_path()
        self._detect_visual_noise()
        self._analyze_motion_rhythm()
        self._calculate_energy_curve()
        self._analyze_camera_intelligence()
        self._validate_narrative_flow()
        self._estimate_emotional_pacing()
        self._calculate_information_density()
        self._check_transition_continuity()

        # Existing Rules
        self._check_structure_and_hierarchy() # Rule 4
        self._check_time_aware_limits()       # Rule 2
        self._check_cognitive_load()          # Rule 3
        self._check_motion_intelligence()     # Rule 5, 7
        self._check_comprehension_rules()     # Rule 1, 8
        self._check_resting_time()            # Rule 6

        # Scoring & Normalization
        # Composite score calculation
        self.scores['overall_cinematic_score'] = (
            self.scores['clarity'] * 0.15 +
            self.scores['motion_quality'] * 0.15 +
            self.scores['comprehension'] * 0.2 +
            self.scores['visual_hierarchy'] * 0.1 +
            self.scores['eye_flow'] * 0.1 +
            self.scores['motion_rhythm'] * 0.1 +
            self.scores['narrative_strength'] * 0.1 +
            self.scores['camera_quality'] * 0.1
        )

        for k in self.scores:
            self.scores[k] = max(0.0, min(10.0, round(self.scores[k], 1)))

        status = "CLEAN"
        if len(self.issues) > 3 or self.scores['overall_cinematic_score'] < 6.0:
            status = "OVERLOADED"
        elif len(self.issues) > 0 or self.scores['overall_cinematic_score'] < 8.0:
            status = "ACCEPTABLE"

        # Derive info density label
        total_bits = 0
        for ov in self.overlays:
            o_type = str(ov.get('type','')).lower()
            if o_type == 'text': total_bits += len(str(ov.get('content','')).split())
            elif 'chart' in o_type: total_bits += 15
            elif 'indicator' in o_type: total_bits += 8
        bits_per_sec = total_bits / (self.duration / 30.0) if self.duration > 0 else 0
        info_density_label = "Extreme" if bits_per_sec > 10.0 else "Busy" if bits_per_sec > 6.0 else "Safe"

        return {
            "scene_id": self.scene_id,
            "status": status,
            "scores": self.scores,
            "issues": self.issues,
            "motion_issues": self.motion_issues,
            "comprehension_breakpoints": self.comprehension_breakpoints,
            "resting_time_violations": self.resting_time_violations,
            "director_notes": list(set(self.director_notes)),
            "attention_budget_used": self._calculate_attention_budget(),
            "fix_suggestions": list(set(self.fix_suggestions)),
            "simplified_version": self._generate_simplified_version(),
            "perceived_tone": self.tone,
            "info_density": info_density_label
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

                # Visual Noise Calculation
                if o_type in ['shape', 'svg', 'connector']:
                    noise_val = 0.5 if ov.get('animation') else 0.1
                    self.visual_noise_per_frame[f] += noise_val

            if 0 <= start < self.duration:
                self.motion_events[start] += 1

        # Incorporate camera shots into motion events and energy
        for shot in self.scene.get('camera', {}).get('shots', []):
            s_start = shot.get('startFrame', 0)
            s_dur = shot.get('duration', 60)
            if 0 <= s_start < self.duration:
                self.motion_events[s_start] += 1

            for f in range(s_start, min(self.duration, s_start + s_dur)):
                self.energy_curve[f] += 0.5 # Camera motion adds energy

    def _simulate_visual_focus(self):
        """1. Visual Focus Simulator: Tracks primary focus and detects conflicts."""
        for f in range(self.duration):
            visible = []
            for ov in self.overlays:
                start = ov.get('start', 0)
                end = start + ov.get('duration', self.duration - start)
                if start <= f < end:
                    # Calculate current visual weight
                    o_type = str(ov.get('type', 'text')).lower()
                    base_weight = self.ELEMENT_WEIGHTS.get(o_type, 1.0)
                    # Boost weight if animating
                    anim_boost = 1.5 if (f - start) < 30 else 1.0
                    imp_boost = 2.0 if str(ov.get('importance','')).lower() == 'hero' else 1.0
                    weight = base_weight * anim_boost * imp_boost
                    visible.append({'id': ov.get('id'), 'weight': weight})

            if not visible:
                self.focus_data.append({'frame': f, 'target': None, 'strength': 0, 'competitors': []})
                continue

            visible.sort(key=lambda x: x['weight'], reverse=True)
            primary = visible[0]
            competitors = [v for v in visible[1:] if v['weight'] > primary['weight'] * 0.7] # Slightly lower threshold for conflict

            if competitors and f % 30 == 0:
                self.issues.append(f"Focus Conflict at frame {f}: '{primary['id']}' and '{competitors[0]['id']}' have equal visual weight.")
                self.scores['visual_hierarchy'] -= 0.2
                self.director_notes.append(f"Viewer attention splits between {primary['id']} and {competitors[0]['id']}. Stagger their entries.")

            self.focus_data.append({
                'frame': f,
                'target': primary['id'],
                'strength': primary['weight'],
                'competitors': [c['id'] for c in competitors]
            })

    def _simulate_eye_path(self):
        """2. Eye Path Simulator: Estimates movement flow (Top -> Center -> Bottom)."""
        last_pos = None
        for ov in sorted(self.overlays, key=lambda x: x.get('start', 0)):
            pos = ov.get('position', {'x': 960, 'y': 540})
            if last_pos:
                # Check for erratic jumps
                dist = math.sqrt((pos['x'] - last_pos['x'])**2 + (pos['y'] - last_pos['y'])**2)
                if dist > 1000:
                    self.issues.append(f"Eye Path Broken: Erratic jump from {last_pos} to {pos}.")
                    self.scores['eye_flow'] -= 1.0
                    self.director_notes.append(f"The eye has to jump too far between {ov.get('id')} and previous element. Group related info spatially.")
            last_pos = pos

    def _detect_visual_noise(self):
        """3. Visual Noise Detector: Decorative graphics competing with info."""
        avg_noise = sum(self.visual_noise_per_frame) / self.duration if self.duration > 0 else 0
        if avg_noise > 2.0:
            self.issues.append(f"Visual Noise Too High ({round(avg_noise, 1)}). Decorative elements distracting from content.")
            self.scores['modernity'] -= 1.0
            self.director_notes.append("Background particles or shapes are too active. Simplify decorative layers.")

    def _analyze_motion_rhythm(self):
        """4. Motion Rhythm Analyzer: Evaluates reveal/pause patterns."""
        # Detect patterns like Reveal -> Pause -> Reveal
        events = [i for i, count in enumerate(self.motion_events) if count > 0]
        if len(events) < 2:
            self.scores['motion_rhythm'] = 10.0
            return

        gaps = [events[i+1] - events[i] for i in range(len(events)-1)]
        # Good rhythm has varied gaps and avoids clustering
        if any(g < 10 for g in gaps):
            self.issues.append("Bad Motion Rhythm: Simultaneous or rapid-fire reveals detected.")
            self.scores['motion_rhythm'] -= 2.0
            self.director_notes.append("The scene feels mechanically animated. Stagger reveals with 15-20 frame gaps.")

        # Calculate consistency score
        avg_gap = sum(gaps) / len(gaps)
        rhythm_variance = sum((g - avg_gap)**2 for g in gaps) / len(gaps)
        if rhythm_variance < 5.0: # Too mechanical
             self.scores['motion_rhythm'] -= 1.0

    def _calculate_energy_curve(self):
        """5. Scene Energy Curve: Tracks motion intensity and camera strength."""
        # Energy = motion_events + frame_load + camera_weight
        for f in range(self.duration):
            event_energy = self.motion_events[f] * 4.0 # Boost event impact
            load_energy = self.frame_load[f] * 0.5   # Boost load impact
            self.energy_curve[f] += event_energy + load_energy # Camera already added in _simulate_timeline

        # Check for dynamic variation
        max_e = max(self.energy_curve) if self.energy_curve else 0
        min_e = min(self.energy_curve) if self.energy_curve else 0
        if max_e > 0 and (max_e - min_e) < 1.0:
            self.issues.append("No Dynamic Energy Variation: Scene intensity is too flat.")
            self.scores['overall_cinematic_score'] -= 1.0
            self.director_notes.append("The scene energy is flat. Create 'peaks' of activity followed by 'valleys' of rest.")

    def _analyze_camera_intelligence(self):
        """6. Camera Intelligence: Detects purposeful vs distracting movement."""
        camera = self.scene.get('camera', {})
        shots = camera.get('shots', [])

        # Check for camera movement during reading
        for shot in shots:
            s_start = shot.get('startFrame', 0)
            s_dur = shot.get('duration', 60)
            s_style = shot.get('style', 'cinematic_drift')

            # Find text active during this shot
            for ov in self.overlays:
                if str(ov.get('type','')).lower() == 'text':
                    t_start = ov.get('start', 0)
                    if s_start < t_start + 30 and 'pan' in s_style:
                        self.issues.append(f"Camera Distracts From Info: Pan during text reveal of '{ov.get('id')}'.")
                        self.scores['camera_quality'] -= 1.5
                        self.director_notes.append(f"Camera movement makes it hard to read {ov.get('id')}. Hold camera still during text entry.")

    def _validate_narrative_flow(self):
        """7. Narrative Flow Validator: Verifies Hero/Evidence/Decoration hierarchy."""
        heroes = [o for o in self.overlays if str(o.get('importance','')).lower() == 'hero' or o.get('hero_config')]
        evidence = [o for o in self.overlays if o.get('type') in ['chart', 'shadcn_chart', 'indicator', 'graph']]

        if heroes and not evidence:
            self.scores['narrative_strength'] -= 1.0 # Opinion without proof
        if evidence and not heroes:
            self.issues.append("Narrative Hierarchy Missing: Proof provided without a clear Hero statement.")
            self.scores['narrative_strength'] -= 2.0

    def _estimate_emotional_pacing(self):
        """8. Emotional Pacing: Categorizes the scene's emotional tone."""
        # Tone derived from motion intensity and visual weight
        avg_energy = sum(self.energy_curve) / self.duration if self.duration > 0 else 0
        if avg_energy > 3.0: self.tone = "chaotic"
        elif avg_energy > 2.0: self.tone = "dramatic"
        elif avg_energy > 1.0: self.tone = "tense"
        elif avg_energy > 0.5: self.tone = "neutral"
        else: self.tone = "calm"

        # Check for tone-story mismatch (heuristic)
        if self.tone == "chaotic":
            self.issues.append(f"Emotional Pacing mismatch: Scene is too '{self.tone}' for documentary flow.")
            self.scores['overall_cinematic_score'] -= 1.0

    def _calculate_information_density(self):
        """9. Information Density: Bits of info per second."""
        # Rough estimate: 1 point per word, 15 per chart, 8 per indicator
        total_bits = 0
        for ov in self.overlays:
            o_type = str(ov.get('type','')).lower()
            if o_type == 'text': total_bits += len(str(ov.get('content','')).split())
            elif 'chart' in o_type: total_bits += 15 # Complex data
            elif 'indicator' in o_type: total_bits += 8

        bits_per_sec = total_bits / (self.duration / 30.0) if self.duration > 0 else 0
        if bits_per_sec > 10.0:
            self.issues.append(f"Information Density too high ({round(bits_per_sec, 1)} bits/sec). Viewer cannot absorb this much data.")
            self.scores['information_density'] -= 3.0
            self.director_notes.append("The information density is extreme. Split this data into two scenes or increase duration.")
        elif bits_per_sec > 5.0:
            self.scores['information_density'] -= 1.0 # Busy but acceptable

    def _check_transition_continuity(self):
        """10. Transition Continuity: Detects random vs natural reveal sequences."""
        anims = [ov.get('animation') for ov in sorted(self.overlays, key=lambda x: x.get('start', 0)) if ov.get('animation')]
        if len(anims) < 3: return

        # Detect too much variety (randomness)
        unique_anims = len(set(anims))
        if unique_anims > 3:
            self.issues.append("Transition Continuity Broken: Too many different animation styles in one scene.")
            self.scores['motion_quality'] -= 1.0
            self.director_notes.append("The motion language is inconsistent. Stick to 2-3 standard reveal types.")

    def _check_structure_and_hierarchy(self):
        """Rule 4: Visual Hierarchy (Single Hero)."""
        if len(self.overlays) > 7:
            self.issues.append(f"Element count too high ({len(self.overlays)}). Max 7 recommended.")
            self.scores['clarity'] -= 1.0

        heroes = [o for o in self.overlays if str(o.get('importance', '')).lower() in ['hero', 'primary']]
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
        """Rule 2: Time-Aware Video Limits (Adaptive)."""
        sec = self.duration / 30.0
        project_type = self.scene.get('project_type', 'documentary') # Default to documentary

        # Adaptive limits based on content style
        limits = {
            'fast_social': {'max_overlays_5s': 5, 'max_overlays_10s': 8, 'min_chart_sec': 1.5},
            'documentary': {'max_overlays_5s': 3, 'max_overlays_10s': 5, 'min_chart_sec': 2.5},
            'educational': {'max_overlays_5s': 2, 'max_overlays_10s': 4, 'min_chart_sec': 4.0}
        }.get(project_type, {'max_overlays_5s': 3, 'max_overlays_10s': 5, 'min_chart_sec': 2.5})

        if sec <= 5.1: # 5 Second Shot
            charts = [o for o in self.overlays if 'chart' in str(o.get('type',''))]
            if len(charts) > 0:
                self.issues.append(f"5s scene is too short for a Chart. Viewer needs {limits['min_chart_sec']}s+ to process data.")
            if len(self.overlays) > limits['max_overlays_5s']:
                self.issues.append(f"Too many overlays ({len(self.overlays)}) for a 5s window. Max {limits['max_overlays_5s']} allowed.")

        elif sec <= 10.1: # 10 Second Beat
            if len(self.overlays) > limits['max_overlays_10s']:
                self.issues.append(f"10s scene crowded with {len(self.overlays)} elements. Max {limits['max_overlays_10s']} recommended.")

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
        """Rule 3: Cognitive Load Limits (Safe Load Algorithm)."""
        # Safe Load = Visible Elements * Animation Strength * Motion Density * Reading Demand
        total_motion_density = sum(self.motion_events) / (self.duration / 30.0)

        for f in range(self.duration):
            visible_count = self.active_elements_per_frame[f]
            # Animation strength: 1.5 if an animation started within last 15 frames
            recent_anim = 1.5 if sum(self.motion_events[max(0, f-15):f+1]) > 0 else 1.0

            # Safe Load Formula
            safe_load = visible_count * recent_anim * (1.0 + total_motion_density * 0.2)
            if safe_load > 5.0 and f % 60 == 0:
                 self.issues.append(f"Cognitive Overload at frame {f}: Safe load ({round(safe_load,1)}) exceeded.")
                 self.scores['comprehension'] -= 0.5

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

        # Rule 5: Motion Purpose and Fatigue
        has_info = any(o.get('type') in ['chart', 'shadcn_chart', 'indicator'] for o in self.overlays)
        motion_count = 0
        for ov in self.overlays:
            anim = ov.get('animation', 'static')
            if anim != 'static':
                motion_count += 1
                o_type = str(ov.get('type','')).lower()

                # Check for decorative misuse
                if o_type == 'shape' and has_info:
                    self.motion_issues.append(f"Decorative motion on '{ov.get('id')}' distracts from data-heavy scene.")
                    self.scores['motion_quality'] -= 1.0

        if motion_count > 5:
            self.issues.append("Motion Fatigue: Too many elements moving in one scene.")
            self.scores['motion_quality'] -= 2.0
            self.director_notes.append("The scene has too much movement. Viewer is experiencing motion fatigue.")

    def _check_comprehension_rules(self):
        """Rule 1 & 8: Visibility Limits & Attention Flow."""
        # Rule 1: Minimum Visibility (Language-Aware)
        for ov in self.overlays:
            o_type = str(ov.get('type','')).lower()
            o_id = ov.get('id','unknown')
            frames = ov.get('duration', self.duration)
            sec = frames / 30.0

            if o_type == 'text':
                content = str(ov.get('content',''))
                words = len(re.sub(r'[.।]', '', content).split())

                # Detect language
                lang = 'english'
                if any('\u0980' <= c <= '\u09FF' for c in content): lang = 'bangla'
                if any(c.isdigit() for c in content) and words < 3: lang = 'numeric'

                speed = self.READING_SPEEDS.get(lang, 0.3)
                req_sec = words * speed

                if sec < req_sec:
                    self.issues.append(f"Readability failure ({lang}): Text '{o_id}' needs {round(req_sec,1)}s, has {round(sec,1)}s.")
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
            # Estimate actual animation duration from properties
            anim_dur = ov.get('animation_duration', ov.get('transition_duration', 20))
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
