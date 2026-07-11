from typing import Dict, Any

class SceneClassifier:
    def __init__(self):
        self.type_keywords = {
            'trend': ['increase', 'growth', 'rise', 'forecast', 'future', 'trend', 'evolution'],
            'conflict': ['threat', 'danger', 'problem', 'risk', 'crisis', 'battle', 'war', 'attack'],
            'comparison': ['vs', 'compare', 'difference', 'better', 'higher', 'scale', 'ratio'],
            'historical': ['past', 'archive', 'ancient', 'was', 'used to', 'century', 'origin']
        }

        self.emotion_keywords = {
            'intense': ['crisis', 'emergency', 'urgent', 'disaster', 'incredible'],
            'alert': ['warning', 'look out', 'watch', 'danger', 'unstable'],
            'growing': ['expanding', 'more', 'rising', 'gaining'],
            'calm': ['stable', 'peaceful', 'uniform', 'steady']
        }

    def classify(self, text: str) -> Dict[str, str]:
        text_lower = text.lower()

        scene_type = "trend" # Default
        max_matches = 0
        for s_type, keywords in self.type_keywords.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > max_matches:
                max_matches = matches
                scene_type = s_type

        emotional_tone = "calm" # Default
        max_emo_matches = 0
        for emo, keywords in self.emotion_keywords.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > max_emo_matches:
                max_emo_matches = matches
                emotional_tone = emo

        return {
            "scene_type": scene_type,
            "emotional_tone": emotional_tone
        }
