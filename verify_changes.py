import json
import os
import sys
from remotion_jsonMaker.generator import RemotionJsonMaker

# Problematic AI JSON from the user's request
ai_json = {
  "project_name": "Dhaka_Geological_Clock_Documentary",
  "global_settings": {
    "width": 1920,
    "height": 1080,
    "fps": 30
  },
  "scenes": [
    {
      "scene_id": "SCENE_01",
      "background_type": "video",
      "video_path": "renders/scene_SC_01.mp4",
      "audio_enabled": True,
      "duration_in_frames": 160,
      "camera": {
        "enabled": True,
        "preset": "slow_push",
        "shots": [
          {
            "targetId": "SC1_TITLE_HERO",
            "startFrame": 0,
            "duration": 90,
            "zoom": 1.1,
            "style": "push_in",
            "inDuration": 30
          },
          {
            "targetId": "SC1_UI_PANEL",
            "startFrame": 90,
            "duration": 70,
            "zoom": 1.2,
            "style": "pan_right",
            "inDuration": 45
          }
        ]
      },
      "overlays": [
        {
          "id": "SC1_BG_GRAPH",
          "type": "graph",
          "start": 0,
          "duration": 160,
          "position": { "x": 960, "y": 540 },
          "nodes": 40,
          "links": 60,
          "nodeColor": "#FF3B30",
          "linkColor": "#3a3a3a",
          "speed": 0.05
        },
        {
          "id": "SC1_TITLE_HERO",
          "type": "text",
          "importance": "hero",
          "start": 0,
          "duration": 160,
          "position": { "x": 480, "y": 350 },
          "content": "ঢাকা।\nমেগাসিটি।",
          "fontSize": "96px"
        },
        {
          "id": "SC1_UI_PANEL",
          "type": "ui_panel",
          "start": 45,
          "duration": 115,
          "position": { "x": 1400, "y": 540 },
          "title": "CLASSIFICATION: MEGACITY"
        }
      ]
    },
    {
      "scene_id": "SCENE_04",
      "background_type": "video",
      "video_path": "renders/scene_SC_04.mp4",
      "audio_enabled": True,
      "duration_in_frames": 211,
      "camera": {
        "enabled": True,
        "shots": [
          {
            "targetId": "SC4_GAUGE_CLOCK",
            "startFrame": 9,
            "duration": 111,
            "zoom": 1.2,
            "style": "pull_out",
            "inDuration": 50
          },
          {
            "targetId": "SC4_TEXT_INTENSE",
            "startFrame": 120,
            "duration": 91,
            "zoom": 1.05,
            "style": "static",
            "inDuration": 30
          }
        ]
      },
      "overlays": [
        {
          "id": "SC4_BG_NET",
          "type": "graph",
          "start": 0,
          "duration": 211,
          "position": { "x": 960, "y": 540 },
          "nodes": 60,
          "links": 90
        },
        {
          "id": "SC4_TEXT_INTENSE",
          "type": "text",
          "importance": "hero",
          "start": 9,
          "duration": 202,
          "position": { "x": 500, "y": 540 },
          "content": "জিওলজিক্যাল ক্লক\nশব্দ আরও তীব্র হচ্ছে",
          "fontSize": "56px"
        },
        {
          "id": "SC4_GAUGE_CLOCK",
          "type": "data_indicator",
          "start": 35,
          "duration": 176,
          "position": { "x": 1400, "y": 540 },
          "indicator_type": "semiGauge",
          "value": 92
        }
      ]
    }
  ]
}

maker = RemotionJsonMaker()
# Mock assets to prevent issues
maker.video_files = ["scene_SC_01.mp4", "scene_SC_04.mp4"]
maker.bangla_fonts = ["Sohid_bangla"]
maker.english_fonts = ["Arial"]

print("🛠️ Running Hardening Engine on problematic JSON...")
hardened_json = maker.finalize_json_durations(ai_json)

# Save for QA check
with open("test_manifest.json", "w", encoding="utf-8") as f:
    json.dump(hardened_json, f, indent=2, ensure_ascii=False)

print("\n✅ Hardened manifest saved to test_manifest.json")

# Verification checks
s1 = hardened_json['scenes'][0]
print(f"\n--- SCENE_01 Verification ---")
# Check camera preservation
shots = s1['camera']['shots']
print(f"Camera Shot 1 Target: {shots[0]['targetId']}, Style: {shots[0]['style']}")
print(f"Camera Shot 2 Target: {shots[1]['targetId']}, Style: {shots[1]['style']}")

# Check Hero Font Size protection
hero = next(o for o in s1['overlays'] if o['id'] == 'SC1_TITLE_HERO')
print(f"Hero Font Size: {hero['fontSize']}")

# Check split screen preservation (roughly)
panel = next(o for o in s1['overlays'] if o['id'] == 'SC1_UI_PANEL')
print(f"Hero X: {hero['position']['x']}, Panel X: {panel['position']['x']}")

s4 = hardened_json['scenes'][1]
print(f"\n--- SCENE_04 Verification ---")
# Check camera preservation
shots = s4['camera']['shots']
print(f"Camera Shot 1 Target: {shots[0]['targetId']}, Style: {shots[0]['style']}")
print(f"Camera Shot 2 Target: {shots[1]['targetId']}, Style: {shots[1]['style']}")

text_intense = next(o for o in s4['overlays'] if o['id'] == 'SC4_TEXT_INTENSE')
gauge = next(o for o in s4['overlays'] if o['id'] == 'SC4_GAUGE_CLOCK')
print(f"Text X: {text_intense['position']['x']}, Gauge X: {gauge['position']['x']}")
