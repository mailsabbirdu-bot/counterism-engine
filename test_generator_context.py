import re

def _is_bangla(text):
    return any('\u0980' <= c <= '\u09FF' for c in text)

def generate_mock(story):
    pattern = r'দৃশ্য\s+[0-9০-৯]+'
    story_parts = re.split(pattern, story)
    if story_parts and not story_parts[0].strip():
        story_parts = story_parts[1:]

    scene_narrations = []
    for i, text in enumerate(story_parts, 1):
        narration = text.strip()
        lang = "BANGLA" if _is_bangla(narration) else "ENGLISH"
        scene_narrations.append(f"SCENE_{i:02d} ({lang}): {narration}")

    return "\n".join(scene_narrations)

story = """দৃশ্য ০১
ঢাকা।
দৃশ্য ০২
Crowded city.
"""

print(generate_mock(story))
