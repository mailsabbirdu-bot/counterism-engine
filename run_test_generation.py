import json
import os
import sys
from remotion_jsonMaker.generator import RemotionJsonMaker

def test():
    maker = RemotionJsonMaker(manual=False)
    # Mock scanned fonts
    maker.bangla_fonts = ["Sohid_bangla"]
    maker.english_fonts = ["Audiowide-Regular_english"]
    maker.story_scenes = {
        "SCENE_01": "ঢাকা: মেগাসিটি"
    }

    with open("bad_manifest.json", "r") as f:
        data = json.load(f)

    print("Running finalize_json_durations (Hardening Pass)...")
    fixed_data = maker.finalize_json_durations(data, public_dir="public")

    with open("fixed_manifest.json", "w") as f:
        json.dump(fixed_data, f, indent=2, ensure_ascii=False)

    print("\nRunning QA on FIXED manifest...")
    from scripts.test_manifest_quality import test_manifest_quality
    success, score, feedback = test_manifest_quality("fixed_manifest.json", "public")

    print(f"\nResult: Success={success}, Score={score}%")
    if feedback:
        print("Feedback items:", len(feedback))

if __name__ == "__main__":
    test()
