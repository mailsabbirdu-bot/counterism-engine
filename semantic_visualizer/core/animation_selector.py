from typing import Dict, Any

class AnimationSelector:
    def __init__(self):
        self.scene_rules = {
            "introduction": {"enter": "fade", "motion": "slow_zoom"},
            "growth": {"enter": "reveal", "motion": "expansion"},
            "reveal": {"enter": "mask_reveal", "motion": "jitter"},
            "explanation": {"enter": "scale_in", "motion": "pulse"},
            "trend": {"enter": "fade", "motion": "float"},
            "conflict": {"enter": "reveal", "motion": "jitter"}
        }

    def select(self, scene_type: str, emotion: str) -> Dict[str, str]:
        base = self.scene_rules.get(scene_type, {"enter": "fade", "motion": "float"})

        enter = base["enter"]
        motion = base["motion"]

        if emotion == "intense":
            motion = "jitter"

        return {
            "enter": enter,
            "motion": motion,
            "exit": "fade"
        }

class CameraPlanner:
    def __init__(self):
        self.movement_map = {
            "introduction": "zoom_out",
            "growth": "pan_up",
            "reveal": "push_in",
            "explanation": "focus_shift",
            "trend": "cinematic_drift",
            "conflict": "shaky_push"
        }

    def plan(self, scene_type: str, hero_node: str) -> Dict[str, Any]:
        movement = self.movement_map.get(scene_type, "cinematic_drift")
        zoom = 1.0
        if movement == "push_in":
            zoom = 1.5

        return {
            "movement": movement,
            "focus": hero_node,
            "zoom": zoom,
            "duration": 150
        }
