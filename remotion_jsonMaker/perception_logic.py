import math
from typing import Dict, Any, List, Tuple, Optional

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
    """Authoritative cognitive load calculation logic."""
    @staticmethod
    def calculate_fused_load(bg_busy_score: float, overlays: List[Dict[str, Any]], motion_intensity: float = 0.3) -> float:
        # Overlays density component (normalized)
        ov_density = len(overlays) / 6.0

        # Area-based load (total screen coverage)
        total_area_load = 0
        for ov in overlays:
            w, h = ov.get('width', 400), ov.get('height', 300)
            total_area_load += (w * h) / (1920 * 1080)

        # Complexity penalty for specific types
        type_penalty = 0
        for ov in overlays:
            o_type = str(ov.get('type', '')).lower()
            if 'chart' in o_type or 'graph' in o_type: type_penalty += 0.2
            if 'hub_network' in o_type or 'flow_diagram' in o_type: type_penalty += 0.3

        load = bg_busy_score + ov_density + total_area_load + motion_intensity + type_penalty
        return round(load, 2)

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

class NarrativeLogic:
    """Detects narrative gaps and flow issues."""
    @staticmethod
    def check_narrative_integrity(overlays: List[Dict[str, Any]]) -> Dict[str, Any]:
        has_data = any(str(ov.get('type', '')).lower() in ['chart', 'shadcn_chart', 'indicator', 'graph'] for ov in overlays)
        has_hero = any(str(ov.get('importance', '')).lower() == 'hero' or ov.get('hero_config') for ov in overlays)

        if has_data and not has_hero:
            return {
                'status': 'gap',
                'explanation': "Evidence provided without a Hero statement.",
                'severity': 'warning'
            }
        return {'status': 'clean'}
