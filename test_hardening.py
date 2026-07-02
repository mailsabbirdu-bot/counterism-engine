import json
import os
import sys
from remotion_jsonMaker.generator import RemotionJsonMaker

def test():
    maker = RemotionJsonMaker(manual=False)
    # Mock font scanning
    maker.bangla_fonts = ["Sohid_bangla"]
    maker.english_fonts = ["Audiowide-Regular_english"]
    maker.story_scenes = {
        "SCENE_01": "স্মার্ট মেগাসিটি",
        "SCENE_02": "Neural load analysis"
    }

    with open("remotion_render.json", "r") as f:
        data = json.load(f)

    print("Running finalize_json_durations...")
    fixed_data = maker.finalize_json_durations(data, public_dir="public")

    with open("remotion_fixed.json", "w") as f:
        json.dump(fixed_data, f, indent=2, ensure_ascii=False)

    print("\nRunning QA on fixed manifest...")
    from scripts.test_manifest_quality import test_manifest_quality
    success, score, feedback = test_manifest_quality("remotion_fixed.json", "public")

    print(f"\nResult: Success={success}, Score={score}%")
    if feedback:
        print("Feedback:")
        for f in feedback: print(f"  - {f}")

if __name__ == "__main__":
    test()
