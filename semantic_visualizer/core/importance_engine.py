from typing import Dict, Any

class ImportanceEngine:
    def __init__(self):
        self.emotion_weights = {
            "intense": 1.5,
            "alert": 1.3,
            "growing": 1.2,
            "calm": 1.0
        }

    def calculate_weight(self, node: Dict[str, Any], centrality: float) -> float:
        importance = node.get('importance', 1.0)
        emotion = node.get('emotion', 'calm')
        scale = node.get('scale', 1.0)

        emotion_multiplier = self.emotion_weights.get(emotion, 1.0)

        # Formula: visual_weight = (importance + centrality) * emotion_multiplier * scale
        visual_weight = (importance + centrality) * emotion_multiplier * scale
        return round(visual_weight, 2)

class EmotionEngine:
    def __init__(self):
        pass

    def analyze_shift(self, current_scene_tone: str, previous_scene_tone: str) -> str:
        if current_scene_tone == "intense" and previous_scene_tone != "intense":
            return "dramatic_reveal"
        if current_scene_tone == "growing":
            return "progressive_expansion"
        return "stable_flow"
