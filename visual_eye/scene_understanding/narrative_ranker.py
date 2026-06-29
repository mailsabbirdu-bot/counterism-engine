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
    if not tracks:
        return []

    script = str(context.get('script', '')).lower() if context else ""
    title = str(context.get('title', '')).lower() if context else ""
    keywords = [k.lower() for k in context.get('keywords', [])] if context else []

    # Simple keyword mapping for common classes
    # e.g. "traffic" -> car, bus, truck
    NARRATIVE_MAP = {
        'building': ['concrete', 'house', 'empire', 'skyscraper', 'apartment', 'wall', 'brick'],
        'person': ['man', 'woman', 'people', 'crowd', 'human', 'worker'],
        'car': ['traffic', 'vehicle', 'road', 'street', 'transport', 'highway'],
        'tree': ['nature', 'forest', 'green', 'leaf', 'garden', 'park'],
        'water': ['river', 'lake', 'sea', 'ocean', 'boat', 'ship', 'sink']
    }

    ranked = []
    for track in tracks:
        o_type = track.type.lower()
        score = 0.0

        # 1. Exact match in script/title/keywords
        if o_type in script: score += 0.5
        if o_type in title: score += 0.3
        if o_type in keywords: score += 0.5

        # 2. Semantic mapping match
        relevant_words = NARRATIVE_MAP.get(o_type, [])
        for word in relevant_words:
            if word in script: score += 0.3
            if word in title: score += 0.1
            if word in keywords: score += 0.2

        # 3. Frequency boost
        # If the word appears multiple times, it might be more important
        matches = re.findall(rf'\b{o_type}\b', script)
        score += len(matches) * 0.1

        narrative_importance = min(1.0, score)

        ranked.append(SubjectRank(
            track_id=track.track_id,
            type=track.type,
            narrative_importance=narrative_importance
        ))

    ranked.sort(key=lambda x: x.narrative_importance, reverse=True)
    return ranked
