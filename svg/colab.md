# 🚀 SVG Motion Graphics - Remotion Colab

Run this cell to render the SVG showcase.

```python
import os

# --- 1. SETUP ---
print("📦 Setting up environment...")
if not os.path.exists("/content/drive"):
    from google.colab import drive
    drive.mount('/content/drive')

ENGINE_DIR = "/content/engine"
if not os.path.exists(ENGINE_DIR):
    !git clone https://github.com/mailsabbirdu-bot/counterism-engine {ENGINE_DIR}

%cd {ENGINE_DIR}

# --- 2. INSTALL DEPS ---
print("🛠️ Installing dependencies...")
!pip install playwright playwright-stealth
!playwright install chromium
!playwright install-deps
!npm install

# --- 3. CREATE TEST MANIFEST ---
print("📄 Creating SVG showcase manifest...")
import json

manifest = {
  "project_name": "SVG Motion Showcase",
  "global_settings": { "width": 1920, "height": 1080, "fps": 30 },
  "scenes": [
    {
      "scene_id": "SCENE_SVG",
      "duration_in_frames": 150,
      "background_type": "procedural",
      "procedural_config": { "variant": "neon_grid" },
      "overlays": [
        {
          "id": "icon1",
          "type": "svg",
          "query": "cpu",
          "provider": "lucide",
          "animation": "draw",
          "start": 0,
          "duration": 90,
          "position": { "x": 480, "y": 540 },
          "width": 400,
          "height": 400,
          "color": "#3b82f6",
          "strokeWidth": 3
        },
        {
          "id": "icon2",
          "type": "svg",
          "query": "zap",
          "provider": "lucide",
          "animation": "bounce",
          "start": 30,
          "duration": 90,
          "position": { "x": 960, "y": 540 },
          "width": 300,
          "height": 300,
          "color": "#eab308"
        },
        {
          "id": "icon3",
          "type": "svg",
          "query": "shield",
          "provider": "lucide",
          "animation": "pop",
          "start": 60,
          "duration": 60,
          "position": { "x": 1440, "y": 540 },
          "width": 350,
          "height": 350,
          "color": "#10b881"
        }
      ]
    }
  ]
}

with open("svg_showcase.json", "w") as f:
    json.dump(manifest, f, indent=2)

# --- 4. RENDER ---
print("🎬 Rendering SVG Video...")
!node --loader ts-node/esm render.ts --template=svg_showcase.json --output=svg_motion.mp4

print("✅ DONE! Check the renders folder.")
```
