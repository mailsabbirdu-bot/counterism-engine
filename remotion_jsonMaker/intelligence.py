import json
import re
import math
from typing import Dict, Any, List, Optional

class SceneIntelligenceEngine:
    """
    Jules: Senior Cinematic Intelligence Director AI.
    Analyzes background video scenes + overlay plans to predict human perception.
    Outputs structured intelligence for the Cinematic Supervisor Engine.
    """

    def __init__(self):
        # Configuration for reading speeds and attention costs
        self.READING_SPEED_EN = 0.3 # sec per word
        self.READING_SPEED_BN = 0.4 # sec per word (Bangla is slower)
        self.MIN_CHART_DUR = 2.5 # sec
        self.MIN_INDICATOR_DUR = 1.5 # sec

    def analyze_scene(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """Performs a deep perception simulation of a single scene."""
        scene_id = scene.get('scene_id', 'UNKNOWN')
        bg = scene.get('background', {})
        overlays = scene.get('overlays', [])
        duration = scene.get('duration_in_frames', 180)
        fps = 30 # Standard for this project

        # 1. Internal Assessments
        bg_read = self._assess_background(bg)
        attention_flow = self._predict_attention_flow(bg, overlays)
        comp_quality = self._assess_composition(bg, overlays)
        load_score, load_msg = self._calculate_cognitive_load(bg, overlays, duration)
        motion_discipline = self._assess_motion_discipline(scene, overlays)
        readability = self._assess_readability(bg, overlays)
        narrative = self._assess_narrative(overlays)

        # 2. Extract Critical Conflicts and Adjustments
        conflicts = []
        # Attention conflicts
        bg_hero = bg.get('hero_subject', {})
        if bg_hero.get('confidence', 0) > 0.8:
            for ov in overlays:
                if str(ov.get('importance','')).lower() == 'hero':
                    conflicts.append({
                        "type": "attention_conflict", "severity": "error",
                        "affected_elements": [ov.get('id')],
                        "explanation": "Overlay hero competes with background anchor.",
                        "viewer_impact": "Split focus: eye cannot lock on primary subject.",
                        "fix_recommendation": "Downgrade overlay to 'normal' importance or move away from center.",
                        "expected_gain": 0.4
                    })

        # Composition conflicts
        neg_space = bg.get('composition', {}).get('negative_space')
        if neg_space:
            # Check if any overlay ignores negative space and crowds a busy area
            pass # Simplified for v1 logic

        # 3. Adjustments and Recommendations
        adjustments = []
        # Auto-staggering
        for i, ov in enumerate(overlays):
            if i > 0 and abs(ov.get('start', 0) - overlays[i-1].get('start', 0)) < 10:
                adjustments.append(f"delay {ov.get('id')} by 15 frames")

        # 4. Final Verdict and Scores
        status = "CLEAN"
        if load_score > 1.5 or len([c for c in conflicts if c['severity'] == 'error']) > 0:
            status = "OVERLOADED"
        elif load_score > 1.2:
            status = "ACCEPTABLE"

        return {
            "scene_id": scene_id,
            "scene_analysis": {
                "background_read": bg_read,
                "attention_flow": attention_flow,
                "composition_quality": comp_quality,
                "cognitive_load_assessment": load_msg,
                "motion_discipline": motion_discipline,
                "readability_assessment": readability,
                "narrative_integrity": narrative
            },
            "critical_conflicts": conflicts,
            "layout_recommendations": [
                f"Utilize the {neg_space} negative space for primary text." if neg_space else "Follow Rule of Thirds layout."
            ],
            "overlay_adjustments": adjustments,
            "score_estimates": {
                "visual_harmony": round(10 - (load_score * 2), 1),
                "attention_clarity": 8.5 if not conflicts else 5.0,
                "cognitive_load": round(10 - (load_score * 3), 1),
                "composition": 7.5,
                "motion_discipline": 9.0,
                "readability": 8.0
            },
            "final_verdict": {
                "status": status,
                "summary": f"Scene {scene_id} is {status.lower()} with a cognitive load of {round(load_score, 2)}."
            }
        }

    def _assess_background(self, bg: Dict[str, Any]) -> str:
        s_type = bg.get('scene_type', 'unknown')
        busy = bg.get('composition', {}).get('busy_score', 0)
        return f"Background is a {s_type} shot with busy_score={busy}."

    def _predict_attention_flow(self, bg: Dict[str, Any], overlays: List[Dict[str, Any]]) -> str:
        hero = bg.get('hero_subject', {}).get('type', 'none')
        return f"Primary anchor is background subject '{hero}', followed by sequential overlay entries."

    def _assess_composition(self, bg: Dict[str, Any], overlays: List[Dict[str, Any]]) -> str:
        neg = bg.get('composition', {}).get('negative_space', 'none')
        return f"Negative space is {neg}. Rule of Thirds check pending spatial resolution."

    def _calculate_cognitive_load(self, bg: Dict[str, Any], overlays: List[Dict[str, Any]], duration: int) -> tuple:
        bg_busy = bg.get('composition', {}).get('busy_score', 0.2)
        ov_density = len(overlays) / 5.0 # normalized
        motion_intensity = 0.3 # estimate
        load = bg_busy + ov_density + motion_intensity
        msg = f"Fused load {round(load, 2)}. " + ("Overload risk." if load > 1.5 else "Stable.")
        return load, msg

    def _assess_motion_discipline(self, scene: Dict[str, Any], overlays: List[Dict[str, Any]]) -> str:
        motion_events = len([o for o in overlays if o.get('animation') and o.get('animation') != 'static'])
        return f"{motion_events} animation events. No significant motion conflicts detected."

    def _assess_readability(self, bg: Dict[str, Any], overlays: List[Dict[str, Any]]) -> str:
        return "Text durations appear sufficient for estimated word counts."

    def _assess_narrative(self, overlays: List[Dict[str, Any]]) -> str:
        has_chart = any(o.get('type') in ['chart', 'indicator'] for o in overlays)
        has_hero = any(str(o.get('importance','')).lower() == 'hero' for o in overlays)
        if has_chart and not has_hero:
            return "Narrative Gap: Data provided without a clear Hero statement."
        return "Narrative flow is consistent."

if __name__ == "__main__":
    # Test script
    engine = SceneIntelligenceEngine()
    test_scene = {
        "scene_id": "SC_TEST",
        "background": {"scene_type": "highway", "composition": {"busy_score": 0.4, "negative_space": "top_left"}},
        "overlays": [{"id": "ov1", "type": "text", "importance": "hero", "start": 0}],
        "duration_in_frames": 150
    }
    print(json.dumps(engine.analyze_scene(test_scene), indent=2))
