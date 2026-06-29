import re
from typing import List, Dict, Any, Optional
try:
    from ..schema import TrackedObject, SubjectRank
except (ImportError, ValueError):
    try:
        from visual_eye.schema import TrackedObject, SubjectRank
    except ImportError:
        from schema import TrackedObject, SubjectRank

def rank_narrative_subjects(tracks: List[TrackedObject], context: Optional[Dict[str, Any]] = None) -> List[SubjectRank]:
    """
    Rank objects based on narrative context (script, keywords).
    """
    try:
        if not tracks:
            return []

        script = str(context.get('script', '')).lower() if context else ""
        title = str(context.get('title', '')).lower() if context else ""
        keywords = [k.lower() for k in context.get('keywords', [])] if context else []

        # Comprehensive Keyword mapping for common classes
        NARRATIVE_MAP = {
            'building': ['concrete', 'house', 'empire', 'skyscraper', 'apartment', 'wall', 'brick', 'infrastructure', 'home', 'structure', 'construction'],
            'person': ['man', 'woman', 'people', 'crowd', 'human', 'worker', 'citizen', 'child', 'audience', 'individual'],
            'car': ['traffic', 'vehicle', 'road', 'street', 'transport', 'highway', 'commute', 'driver', 'motor', 'automobile'],
            'truck': ['logistics', 'delivery', 'freight', 'transport', 'cargo', 'supply'],
            'bus': ['transit', 'public transport', 'shuttle', 'commuter'],
            'tree': ['nature', 'forest', 'green', 'leaf', 'garden', 'park', 'environment', 'ecology', 'plants'],
            'water': ['river', 'lake', 'sea', 'ocean', 'boat', 'ship', 'sink', 'flood', 'marine', 'liquid'],
            'bridge': ['span', 'connection', 'crossing', 'viaduct', 'overpass'],
            'mosque': ['religion', 'prayer', 'sacred', 'architecture', 'faith', 'temple', 'church'],
            'train': ['rail', 'subway', 'metro', 'station', 'platform', 'locomotive']
        }

        ranked = []
        for track in tracks:
            o_type = track.type.lower()
            score = 0.0

            # 1. Exact match in script/title/keywords
            if o_type in script: score += 0.5
            if o_type in title: score += 0.4
            if o_type in keywords: score += 0.6

            # 2. Semantic mapping match
            relevant_words = NARRATIVE_MAP.get(o_type, [])
            for word in relevant_words:
                if word in script: score += 0.35
                if word in title: score += 0.2
                if word in keywords: score += 0.4

            # 3. Frequency boost
            # Clean script for counting
            clean_script = re.sub(r'[^\w\s]', '', script)
            words_in_script = clean_script.split()
            count = words_in_script.count(o_type)
            for w in relevant_words:
                count += words_in_script.count(w)

            score += min(0.4, count * 0.1)

            narrative_importance = float(min(1.0, score))

            ranked.append(SubjectRank(
                track_id=track.track_id,
                type=track.type,
                narrative_importance=narrative_importance
            ))

        ranked.sort(key=lambda x: x.narrative_importance, reverse=True)
        return ranked
    except Exception as e:
        print(f"⚠️ Narrative ranking error: {e}")
        return []
