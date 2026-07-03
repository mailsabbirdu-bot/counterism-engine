import math
from typing import Dict, Any, List, Tuple, Optional

class VisionConstants:
    """Centralized constants for human perception and cinematography."""
    CENTER_X = 960
    CENTER_Y = 540
    SACCADE_LIMIT = 1000
    NOVELTY_DECAY = 12.0
    MIN_RESTING_FRAMES = 15
    GESTALT_PROXIMITY = 150
    VISUAL_NOISE_THRESHOLD = 0.8
    READING_SPEED_EN = 0.35
    READING_SPEED_BN = 0.45
    READING_SPEED_MIXED = 0.40

    # Rule of Thirds Anchors (Production standard)
    ANCHORS = {
        "L_TOP": (550, 320), "C_TOP": (960, 320), "R_TOP": (1370, 320),
        "L_MID": (550, 540), "C_MID": (960, 540), "R_MID": (1370, 540),
        "L_BOT": (550, 760), "C_BOT": (960, 760), "R_BOT": (1370, 760)
    }

    @staticmethod
    def to_str(val: Any) -> str:
        """Safely flattens potentially hallucinated dictionary values into strings."""
        if not val: return ""
        if not isinstance(val, dict): return str(val)
        # Try common keys used by hallucinating AIs
        return str(val.get('family') or val.get('name') or val.get('type') or val.get('value') or next(iter(val.values()), str(val)))

class StyleThresholds:
    """Adaptive thresholds for different cinematic styles."""
    PRESETS = {
        'vox': {
            'max_cognitive_load': 1.5,
            'motion_tolerance': 0.8,
            'min_resting_frames': 15,
            'max_bits_per_sec': 12,
            'preferred_composition': 'rule_of_thirds'
        },
        'apple': {
            'max_cognitive_load': 0.8,
            'motion_tolerance': 0.3,
            'min_resting_frames': 30,
            'max_bits_per_sec': 5,
            'preferred_composition': 'minimalist_centered'
        },
        'johnny_harris': {
            'max_cognitive_load': 1.8,
            'motion_tolerance': 1.2,
            'min_resting_frames': 10,
            'max_bits_per_sec': 15,
            'preferred_composition': 'dynamic_asymmetric'
        },
        'bbc': {
            'max_cognitive_load': 1.2,
            'motion_tolerance': 0.6,
            'min_resting_frames': 20,
            'max_bits_per_sec': 8,
            'preferred_composition': 'balanced_classic'
        }
    }

    @staticmethod
    def get(style: str, key: str) -> Any:
        style = style.lower()
        preset = StyleThresholds.PRESETS.get(style, StyleThresholds.PRESETS['vox'])
        return preset.get(key)

class CognitiveLoadModel:
    """Nonlinear cognitive load calculation based on perceptual interference."""
    @staticmethod
    def calculate_fused_load(bg_busy_score: float, overlays: List[Dict[str, Any]], motion_intensity: float = 0.0) -> float:
        """Fused cognitive load with quadratic motion interference and nonlinear density."""
        # Base density with nonlinear scaling (simultaneous motion interference)
        num_moving = len([o for o in overlays if o.get('animation', 'static') != 'static'])

        # PRODUCTION: Use log1p for more stable motion interference modeling
        motion_interference = min(2.0, math.log1p(num_moving) * 0.9)

        # PRODUCTION: Add normalization clamps to prevent explosion in dense scenes
        ov_density = min(2.0, len(overlays) / 8.0)

        # Area-based load (total screen coverage)
        total_area_load = 0
        for ov in overlays:
            w, h = ov.get('width', 400), ov.get('height', 300)
            total_area_load += (w * h) / (1920 * 1080)

        # Complexity penalty for specialized cognitive tasks
        type_penalty = 0
        for ov in overlays:
            o_type = str(ov.get('type', '')).lower()
            if 'chart' in o_type or 'graph' in o_type: type_penalty += 0.25
            if 'hub_network' in o_type or 'flow_diagram' in o_type: type_penalty += 0.4
            if ov.get('hero_config'): type_penalty += 0.15 # Hero focus cost

        load = bg_busy_score + ov_density + total_area_load + motion_intensity + motion_interference + type_penalty
        return round(float(load), 2)

class VisualWeightCalculator:
    """Calculates the perceptual 'gravity' of elements."""
    @staticmethod
    def calculate_weight(ov: Dict[str, Any]) -> float:
        # Size gravity
        w, h = ov.get('width', 400), ov.get('height', 200)
        size_weight = (w * h) / (960 * 540) # normalized to quarter screen

        # Contrast/Color boost
        color = str(ov.get('color', '#ffffff')).lower()
        color_boost = 1.3 if color in ['#00f5ff', '#ff3e6c', '#ffd700'] else 1.0

        # Central bias (human eye prefers center but Professional design avoids it)
        pos = ov.get('position', {'x': 960, 'y': 540})
        dist_from_center = math.sqrt((pos['x'] - 960)**2 + (pos['y'] - 540)**2)
        central_gravity = 1.0 + (1.0 - (dist_from_center / 1100.0)) * 0.5

        # Importance multiplier
        imp = str(ov.get('importance', '')).lower()
        imp_mult = 2.0 if imp == 'hero' else 1.2 if imp == 'secondary' else 1.0

        return round(size_weight * color_boost * central_gravity * imp_mult, 3)

class CompositionAnalyzer:
    """Analyzes spatial balance and negative space utilization."""
    @staticmethod
    def detect_region(x: int, y: int) -> str:
        if x < 640:
            if y < 360: return 'top_left'
            elif y > 720: return 'bottom_left'
            else: return 'mid_left'
        elif x > 1280:
            if y < 360: return 'top_right'
            elif y > 720: return 'bottom_right'
            else: return 'mid_right'
        else:
            if y < 360: return 'top_center'
            elif y > 720: return 'bottom_center'
            else: return 'center'

    @staticmethod
    def check_negative_space_violation(neg_space: str, overlays: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        violations = []
        for ov in overlays:
            pos = ov.get('position', {'x': 960, 'y': 540})
            region = CompositionAnalyzer.detect_region(pos['x'], pos['y'])
            # If negative space is specified, overlays SHOULD be there, not elsewhere if elsewhere is busy.
            # But here we specifically check if it's centering despite available neg space.
            if neg_space and neg_space != 'none' and region == 'center':
                violations.append({
                    'element_id': ov.get('id'),
                    'explanation': f"Element centered while {neg_space} negative space is available.",
                    'fix': f"Move to {neg_space}."
                })
        return violations

def safe_div(a: float, b: float) -> float:
    """Standard division safety for perception engines."""
    return a / b if b and b != 0 else 0.0

class NarrativeLogic:
    """Models professional documentary story arcs."""
    DOCUMENTARY_STAGES = ['hook', 'context', 'conflict', 'evidence', 'payoff']

    @staticmethod
    def check_narrative_integrity(overlays: List[Dict[str, Any]], scene_id: str = "SCENE_01") -> Dict[str, Any]:
        has_data = any(str(ov.get('type', '')).lower() in ['chart', 'shadcn_chart', 'indicator', 'graph'] for ov in overlays)
        has_hero = any(str(ov.get('importance', '')).lower() == 'hero' or ov.get('hero_config') for ov in overlays)

        # V7: Semantic Role check
        roles = {str(ov.get('semantic_role', 'none')).lower() for ov in overlays}

        if has_data and not has_hero:
            return {
                'status': 'gap',
                'explanation': "Evidence provided without a Hero statement.",
                'severity': 'warning'
            }

        # check for opening hook
        if scene_id == "SCENE_01" and 'hook' not in roles and not has_hero:
             return {
                'status': 'weak_opening',
                'explanation': "First scene lacks a semantic 'hook' or 'hero' element.",
                'severity': 'info'
            }

        return {'status': 'clean'}

class MotionVectorLogic:
    """Analyzes directionality of movement to ensure continuity."""
    @staticmethod
    def get_vector(animation: str) -> Tuple[float, float]:
        anim = animation.lower()
        if 'left' in anim: return (-1.0, 0.0)
        if 'right' in anim: return (1.0, 0.0)
        if 'up' in anim: return (0.0, -1.0)
        if 'down' in anim: return (0.0, 1.0)
        if 'zoom_in' in anim or 'scale_up' in anim: return (0.1, 0.1) # expanding
        if 'zoom_out' in anim: return (-0.1, -0.1)
        return (0.0, 0.0)

    @staticmethod
    def check_continuity(bg_pan: str, overlay_anim: str) -> float:
        """Returns directionality alignment score (-1.0 to 1.0)."""
        bg_vec = MotionVectorLogic.get_vector(bg_pan)
        ov_vec = MotionVectorLogic.get_vector(overlay_anim)

        # Dot product for direction alignment
        dot = bg_vec[0] * ov_vec[0] + bg_vec[1] * ov_vec[1]
        return max(-1.0, min(1.0, dot))
