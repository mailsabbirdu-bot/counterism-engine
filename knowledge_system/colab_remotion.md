# 🎬 Remotion Render Engine (Cinematic Knowledge System)

Run this cell in Google Colab to render your final cinematic knowledge manifest (`remotion_render_crve.json`). This will produce a high-end MP4 video and save it to your analysis folder in Google Drive.

```python
# ==============================================================================
# REMOTION RENDERER — KNOWLEDGE SYSTEM PIPELINE
# ==============================================================================

import os
import shutil
import subprocess

def print_banner(text):
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80)

# --- 1. MOUNT GOOGLE DRIVE ---
print_banner("📂 MOUNTING GOOGLE DRIVE")
from google.colab import drive
drive.mount('/content/drive')

# --- 2. CONFIGURATION ---
DRIVE_BASE_PATH = "/content/drive/MyDrive/Counterism_Studio_V4"
MANIFEST_FILE = f"{DRIVE_BASE_PATH}/analysis/semantic/remotion_render_crve.json"
OUTPUT_DIR = f"{DRIVE_BASE_PATH}/analysis/semantic"
PROJECT_NAME = "counterism-engine"
REPO_URL = "https://github.com/mailsabbirdu-bot/counterism-engine"

%cd /content
if not os.path.exists(PROJECT_NAME):
    print(f"🚀 Cloning repository: {REPO_URL}")
    !git clone {REPO_URL}
%cd {PROJECT_NAME}

# --- 3. SYNC ASSETS & MANIFEST ---
print_banner("📡 SYNCING ASSETS & MANIFEST")
if os.path.exists(MANIFEST_FILE):
    # Copy manifest to local for rendering
    shutil.copy(MANIFEST_FILE, "remotion_render.json")
    print(f"✅ Found and synced manifest: {MANIFEST_FILE}")
else:
    print(f"❌ ERROR: Manifest not found at {MANIFEST_FILE}")
    print("Please run the Knowledge System Pipeline cell first.")
    raise FileNotFoundError("Manifest missing.")

# Sync fonts and other assets if needed (similar to main colab.md)
!mkdir -p public/fonts public/renders/audios
if os.path.exists(f"{DRIVE_BASE_PATH}/fonts"):
    !cp -r {DRIVE_BASE_PATH}/fonts/* public/fonts/

# --- 4. INSTALL SYSTEM DEPENDENCIES ---
print_banner("🛠️ INSTALLING SYSTEM DEPENDENCIES")
!apt-get update -y -qq && apt-get install -y -qq ffmpeg build-essential
!npm install --silent

# --- 5. EXECUTE REMOTION RENDER ---
print_banner("🎬 STARTING RENDERING PIPELINE")
# Pass the custom manifest to the render script
!npm run render -- --template=remotion_render.json --concurrency=1

# --- 6. SAVE OUTPUT TO DRIVE ---
print_banner("💾 SAVING FINAL VIDEO TO DRIVE")
LOCAL_OUTPUT = "renders/overlays/remotion/SCENE_1.mp4" # Default Remotion output path
FINAL_OUTPUT_NAME = "cinematic_knowledge_demo.mp4"

if os.path.exists(LOCAL_OUTPUT):
    dest_path = f"{OUTPUT_DIR}/{FINAL_OUTPUT_NAME}"
    shutil.copy(LOCAL_OUTPUT, dest_path)
    print(f"\n✨ SUCCESS! Video rendered and saved.")
    print(f"📍 Final Video: {dest_path}")
else:
    # Try to find any mp4 in the local render directory
    import glob
    renders = glob.glob("renders/**/*.mp4", recursive=True)
    if renders:
        shutil.copy(renders[0], f"{OUTPUT_DIR}/{FINAL_OUTPUT_NAME}")
        print(f"✅ Found and saved render: {renders[0]}")
    else:
        print("❌ ERROR: Render output not found locally.")

print_banner("🏁 RENDER COMPLETE")
```
