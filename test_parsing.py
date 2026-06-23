import re

def load_story_mock(content):
    story_scenes = {}
    pattern = r'দৃশ্য\s+[0-9০-৯]+'
    parts = re.split(pattern, content)
    if parts and not parts[0].strip():
        parts = parts[1:]

    for i, text in enumerate(parts, 1):
        story_scenes[f"SCENE_{i:02d}"] = text.strip()
    return story_scenes

test_content = """দৃশ্য ০১
ঢাকা। এই প্ল্যানেটের অন্যতম ক্রাউডেড একটা মেগাসিটি।
দৃশ্য ০২
দুই কোটিরও বেশি মানুষ এখানে বাঁচছে।
"""

scenes = load_story_mock(test_content)
print(f"Parsed scenes: {scenes}")

test_content_no_leading_space = """দৃশ্য ০১: ঢাকা।
দৃশ্য ০২: মানুষ।"""
scenes2 = load_story_mock(test_content_no_leading_space)
print(f"Parsed scenes (no leading space): {scenes2}")
