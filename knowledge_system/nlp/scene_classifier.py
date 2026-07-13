from typing import Dict, Any

class SceneClassifier:
    def __init__(self):
        self.type_keywords = {
            'introduction': ['introduce', 'welcome', 'ঢাকা', 'মেগাসিটি'],
            'growth': ['increase', 'growth', 'rise', 'বৃদ্ধি', 'উন্নতি', 'বানাচ্ছে', 'কোটি'],
            'reveal': ['secret', 'hidden', 'threat', 'বিপদ', 'লুকিয়ে আছে', 'টাইমবোম্ব'],
            'explanation': ['because', 'why', 'how', 'ক্লক', 'শব্দ', 'তীব্র'],
            'trend': ['forecast', 'future', 'trend', 'evolution', 'ভবিষ্যৎ'],
            'conflict': ['danger', 'problem', 'risk', 'crisis', 'battle', 'war', 'attack', 'লড়াই', 'সংকট'],
            'comparison': ['vs', 'compare', 'difference', 'better', 'higher', 'scale', 'ratio', 'তুলনা', 'পার্থক্য'],
            'historical': ['past', 'archive', 'ancient', 'was', 'used to', 'century', 'origin', 'অতীত', 'ইতিহাস', 'আগে']
        }

        self.emotion_keywords = {
            'intense': ['crisis', 'emergency', 'urgent', 'disaster', 'incredible', 'তীব্র', 'ভয়াবহ', 'জরুরী', 'টাইমবোম্ব'],
            'alert': ['warning', 'look out', 'watch', 'danger', 'unstable', 'সতর্ক', 'সাবধান', 'বিপদ'],
            'growing': ['expanding', 'more', 'rising', 'gaining', 'ক্রমবর্ধমান', 'বাড়ছে', 'বৃদ্ধি'],
            'welcoming': ['welcome', 'introduce', 'নমস্কার', 'শুভেচ্ছা', 'পরিচিতি'],
            'calm': ['stable', 'peaceful', 'uniform', 'steady', 'শান্ত', 'স্থির']
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
