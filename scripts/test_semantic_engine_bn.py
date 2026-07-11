import sys
import os
import json
import stanza

# Add project root to path
sys.path.append(os.getcwd())

from semantic_engine.main import SemanticEngine

def test_engine():
    # Pre-download Bangla model
    # stanza.download('bn', processors='tokenize,pos,lemma,depparse', verbose=False)

    engine = SemanticEngine(lang='bn')

    test_cases = [
        "২০২৪ সালে অ্যাপল ইনকর্পোরেটেড ১৫ শতাংশ প্রবৃদ্ধি রিপোর্ট করেছে।",
        "ঢাকা বাংলাদেশের রাজধানী এবং এটি একটি জনবহুল শহর।"
    ]

    for i, text in enumerate(test_cases):
        print(f"\n--- Bangla Test Case {i+1} ---")
        print(f"Narration: {text}")
        result = engine.process(text, scene_id=f"test_scene_bn_{i+1}")
        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_engine()
