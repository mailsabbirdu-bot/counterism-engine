# 🚀 SVG Motion Graphics - Powerful Showcase

Run this cell to render the SVG showcase defined in `svg/amazon_example.json`.

```python
import os
import json

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

# --- 3. PRELOAD ASSETS (Offline Rendering) ---
print("📡 Preloading SVG assets for deterministic rendering...")
!npx ts-node --esm svg/scripts/preloadAssets.ts svg/amazon_example.json

# --- 4. LOAD MANIFEST ---
print("📄 Loading SVG directions from svg/amazon_example.json...")
example_path = "svg/amazon_example.json"
if os.path.exists(example_path):
    with open(example_path, 'r') as f:
        manifest = json.load(f)

    with open("remotion_render.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print("✅ Manifest loaded successfully.")
else:
    print("❌ ERROR: svg/amazon_example.json not found!")

# --- 5. RENDER ---
print("🎬 Rendering Powerful SVG Video...")
!node --loader ts-node/esm render.ts --template=remotion_render.json --output=svg_powerful_showcase.mp4 --no-resume

print("✅ DONE! Check the renders folder for 'svg_powerful_showcase.mp4'.")
```
