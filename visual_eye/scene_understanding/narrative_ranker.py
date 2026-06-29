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
    Ranks tracked objects based on story context and narration keywords.
    """
    try:
        if not tracks:
            return []

        script = str(context.get('script', '')).lower() if context else ""
        title = str(context.get('title', '')).lower() if context else ""
        keywords = [k.lower() for k in context.get('keywords', [])] if context else []

        # Production narrative map
        NARRATIVE_MAP = {
            'building': ['skyscraper', 'architecture', 'concrete', 'city', 'office', 'house', 'empire', 'construction'],
            'person': ['man', 'woman', 'people', 'human', 'worker', 'citizen', 'child', 'individual', 'crowd'],
            'bridge': ['crossing', 'connection', 'viaduct', 'river', 'overpass'],
            'river': ['water', 'flow', 'boat', 'nature', 'delta', 'sea'],
            'mosque': ['prayer', 'religious', 'sacred', 'dome', 'faith', 'temple'],
            'train': ['metro', 'rail', 'transit', 'station', 'transport', 'commute']
        }

        ranked = []
        for track in tracks:
            o_type = track.type.lower()
            n_score = 0.0

            # Exact matches
            if o_type in script: n_score += 0.5
            if o_type in title: n_score += 0.4

            # Contextual matches
            relevant = NARRATIVE_MAP.get(o_type, [])
            for word in relevant:
                if word in script: n_score += 0.3
                if word in keywords: n_score += 0.2

            # Normalize and cap
            final_n = min(1.0, n_score)

            ranked.append(SubjectRank(
                track_id=track.track_id,
                type=track.type,
                narrative_importance=float(final_n)
            ))

        ranked.sort(key=lambda x: x.narrative_importance, reverse=True)
        return ranked
    except Exception as e:
        print(f"⚠️ Narrative Ranker Error: {e}")
        return []
