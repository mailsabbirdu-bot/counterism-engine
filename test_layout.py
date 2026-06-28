
import sys
import os
import json
sys.path.append(os.path.abspath('remotion_jsonMaker'))
from generator import RemotionJsonMaker

def test():
    maker = RemotionJsonMaker(headless=True, manual=False)
    # Mock some data so it doesn't try to scan real assets if they don't exist
    maker.bangla_fonts = ["Sohid_bangla"]
    maker.english_fonts = ["Audiowide-Regular_english"]

    test_data = {
        "scenes": [
            {
                "scene_id": "SCENE_01",
                "duration": 180,
                "overlays": [
                    {"id": "t1", "type": "text", "content": "ঢাকা: মেগাসিটি", "fontSize": "150px"},
                    {"id": "c1", "type": "chart", "chart_type": "glass_area", "title": "Density"}
                ]
            },
            {
                "scene_id": "SCENE_02",
                "duration": 200,
                "overlays": [
                    {"id": "t2", "type": "text", "content": "Population Growth", "fontSize": "120px"},
                    {"id": "i1", "type": "shadcn_indicator", "indicator_type": "metric_tile", "value": "20M"}
                ]
            }
        ]
    }

    print("Running finalize_json_durations...")
    result = maker.finalize_json_durations(test_data, public_dir="public")

    with open("test_output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("\n--- RESULTS ---")
    for scene in result['scenes']:
        print(f"Scene: {scene['scene_id']}")
        for ov in scene['overlays']:
            pos = ov.get('position', {})
            scale_info = ""
            if ov.get('width'): scale_info = f" | Size: {ov['width']}x{ov['height']}"
            if ov.get('fontSize'): scale_info += f" | Font: {ov['fontSize']}"
            print(f"  Overlay {ov['id']} ({ov['type']}) -> Pos: ({pos.get('x')}, {pos.get('y')}){scale_info}")

    # Check for center-stacking (960, 540) or (960, 700)
    for scene in result['scenes']:
        positions = [(ov['position']['x'], ov['position']['y']) for ov in scene['overlays']]
        if len(set(positions)) < len(positions):
            print("❌ ERROR: Collision detected!")
        else:
            print("✅ No immediate overlaps.")

if __name__ == "__main__":
    test()
