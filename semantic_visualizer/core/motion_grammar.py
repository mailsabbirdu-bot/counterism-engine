from typing import Dict, Any, List
from ..schemas.visualization_schema import MotionLanguage

class MotionGrammarEngine:
    def __init__(self):
        self.meanings = {
            "hidden_danger": {
                "grammar": ["slow_reveal", "depth_movement", "focus_shift"],
                "parameters": {"layers": {"surface": "stable", "hidden": "emerging"}, "camera": "descend"}
            },
            "accumulation": {
                "grammar": ["expand", "float_up", "particles"],
                "parameters": {"particles": True, "direction": "upward"}
            },
            "progressive_intensity": {
                "grammar": ["pulse", "scale_up", "glow_increase"],
                "parameters": {"pulse_frequency": "increase", "scale": "increase", "brightness": "increase"}
            },
            "stable_flow": {
                "grammar": ["slow_drift", "fade_reveal"],
                "parameters": {}
            }
        }

    def select_grammar(self, scene_type: str, emotion: str, label: str) -> MotionLanguage:
        meaning = "stable_flow"
        if emotion == "intense": meaning = "hidden_danger"
        elif scene_type == "growth": meaning = "accumulation"
        elif "ক্লক" in label or "ঘড়ি" in label: meaning = "progressive_intensity"

        config = self.meanings.get(meaning)
        return MotionLanguage(
            meaning=meaning,
            grammar=config["grammar"],
            parameters=config["parameters"]
        )
