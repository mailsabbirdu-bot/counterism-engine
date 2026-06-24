import os
import json
import sys

# Mock enough of the environment to run finalize_json_durations
sys.path.append(os.path.abspath('.'))
from remotion_jsonMaker.generator import RemotionJsonMaker

def generate():
    maker = RemotionJsonMaker(headless=True)

    # Showcase manifest with new Shadcn components
    raw_manifest = {
      "project_name": "Studio V4 - Shadcn & Audio Showcase",
      "scenes": [
        {
          "scene_id": "SCENE_01_SHADCN_CHARTS",
          "background_type": "video",
          "video_path": "renders/scene_SC_01.mp4",
          "overlays": [
            { "id": "t1", "type": "text", "content": "SHADCN CHARTS", "start": 0 },
            {
              "id": "chart1",
              "type": "shadcn_chart",
              "chart_type": "glass_area",
              "title": "Cloud Matrix",
              "data": [{"name": "A", "value": 400}, {"name": "B", "value": 700}, {"name": "C", "value": 300}]
            },
            {
              "id": "chart2",
              "type": "shadcn_chart",
              "chart_type": "stacked_line",
              "title": "Neural Flow",
              "data": [{"name": "X", "value": 100, "value2": 200}, {"name": "Y", "value": 300, "value2": 150}]
            }
          ]
        },
        {
          "scene_id": "SCENE_02_SHADCN_INDICATORS",
          "background_type": "video",
          "video_path": "renders/scene_SC_02.mp4",
          "overlays": [
            { "id": "t2", "type": "text", "content": "SHADCN INDICATORS", "start": 0 },
            {
              "id": "ind1",
              "type": "shadcn_indicator",
              "indicator_type": "metric_tile",
              "label": "Network Speed",
              "value": 1240
            },
            {
              "id": "ind2",
              "type": "shadcn_indicator",
              "indicator_type": "crypto_card",
              "label": "Ethereum",
              "value": "2,481"
            }
          ]
        }
      ]
    }

    # Run through the pipeline to add durations, positions, and SFX
    # We use a dummy public dir for this verification script
    final_manifest = maker.finalize_json_durations(raw_manifest, "public")

    output_path = "test_shadcn_final.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_manifest, f, indent=2, ensure_ascii=False)

    print(f"✅ Finalized showcase manifest created: {output_path}")
    print(f"🔍 SFX Mapped: {len(final_manifest.get('audio_sfx_manifest', []))}")

if __name__ == "__main__":
    generate()
