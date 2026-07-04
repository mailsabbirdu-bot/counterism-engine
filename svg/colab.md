# 🚀 SVG Motion Graphics - Powerful Showcase

Run this cell to render the SVG showcase defined in `svg/example.json`.

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
!npm install

# --- 3. LOAD POWERFUL MANIFEST ---
print("📄 Loading SVG directions from svg/example.json...")
example_path = "svg/example.json"
if os.path.exists(example_path):
    with open(example_path, 'r') as f:
        manifest = json.load(f)

    # Save as the active manifest
    with open("remotion_render.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print("✅ Manifest loaded successfully.")
else:
    print("❌ ERROR: svg/example.json not found!")

# --- 4. RENDER ---
print("🎬 Rendering Powerful SVG Video...")
# Pass the manifest via the standard rendering pipeline
!node --no-warnings --loader ts-node/esm render.ts --template=remotion_render.json --no-resume

print("✅ DONE! Check the output directory for your rendered video.")
```
