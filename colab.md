# ☁️ Google Colab Setup (Counterism Studio V4)

Run the following cell in Google Colab to automate the entire process with dynamic duration adjustment and Drive-based manifests.

```python
# ==============================================================================
# COUNTERISM STUDIO V4 — AUTOMATED CINEMATIC PIPELINE (DYNAMC DURATION)
# ==============================================================================

import os
import shutil
import subprocess
import json
import math

def print_banner(text):
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80)

def get_video_duration(path):
    """Probes video duration using ffprobe."""
    try:
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', path
        ]
        output = subprocess.check_output(cmd).decode('utf-8').strip()
        return float(output)
    except Exception as e:
        print(f"⚠️  Error probing {path}: {e}")
        return None

# 1. Mount Google Drive
print_banner("📂 MOUNTING GOOGLE DRIVE")
from google.colab import drive
drive.mount('/content/drive')

# 2. Setup Project Environment
PROJECT_NAME = "counterism-engine"
DRIVE_BASE_PATH = "/content/drive/MyDrive/Counterism_Studio_V4"
REPO_URL = "https://github.com/mailsabbirdu-bot/counterism-engine"

if not os.path.exists(PROJECT_NAME):
    print(f"🚀 Cloning repository: {REPO_URL}")
    !git clone {REPO_URL}
else:
    print(f"✅ Project folder '{PROJECT_NAME}' already exists.")

%cd {PROJECT_NAME}

# 3. Handle External Assets (Renders & Audio)
print_banner("🔍 ASSET VERIFICATION & COPYING")

os.makedirs("public/renders", exist_ok=True)
os.makedirs("public/audio", exist_ok=True)

drive_renders = f"{DRIVE_BASE_PATH}/renders"
if os.path.exists(drive_renders):
    print(f"📡 Found Drive renders folder: {drive_renders}")
    print("📦 Copying assets to local public/renders...")
    !rm -rf public/renders/*
    !cp -r {drive_renders}/* public/renders/
    print(f"✅ Copied {len(os.listdir('public/renders'))} render assets.")
else:
    print(f"❌ FATAL: 'renders' folder NOT FOUND in Drive: {drive_renders}")

drive_audio = f"{DRIVE_BASE_PATH}/audio"
if os.path.exists(drive_audio):
    print(f"📡 Found Drive audio folder: {drive_audio}")
    !rm -rf public/audio/*
    !cp -r {drive_audio}/* public/audio/
    print(f"✅ Copied {len(os.listdir('public/audio'))} audio files.")

# 4. Manifest Synchronization & Dynamic Duration
print_banner("📜 MANIFEST SYNCHRONIZATION & DYNAMIC DURATION")

MANIFEST_DIR = f"{DRIVE_BASE_PATH}/manifests"
os.makedirs(MANIFEST_DIR, exist_ok=True)

# Copy template from GitHub to Drive
LOCAL_JSON = "remotion_template.json"
DRIVE_JSON = f"{MANIFEST_DIR}/remotion_template_gdrive.json"

print(f"📄 Syncing manifest to Drive: {DRIVE_JSON}")
shutil.copy(LOCAL_JSON, DRIVE_JSON)

# Load and Update Duration
with open(DRIVE_JSON, 'r') as f:
    template = json.load(f)

fps = template.get('global_settings', {}).get('fps', 30)
updated = False

for scene in template.get('scenes', []):
    if scene.get('background_type') == 'video' and scene.get('video_path'):
        bg_path = os.path.join("public", scene['video_path'])
        if os.path.exists(bg_path):
            duration = get_video_duration(bg_path)
            if duration:
                frames = math.floor(duration * fps)
                print(f"🎬 Scene {scene['scene_id']}: Calculated {frames} frames from {scene['video_path']}")
                scene['duration_in_frames'] = frames
                updated = True
        else:
            print(f"⚠️  Background video not found: {bg_path}")

if updated:
    with open(DRIVE_JSON, 'w') as f:
        json.dump(template, f, indent=2)
    print("✅ Drive manifest updated with dynamic durations.")
else:
    print("ℹ️  No duration updates needed or possible.")

# 5. Install Dependencies
print_banner("🛠️ INSTALLING DEPENDENCIES")
!apt-get update -y && apt-get install -y ffmpeg build-essential
!npm install

# 6. Render Pipeline using Drive Manifest
print_banner("🎬 STARTING RENDERING PIPELINE")
# Pass the Drive manifest to the render command
!npm run render -- --template={DRIVE_JSON} --concurrency=1

# 7. Automatic Drive Upload
print_banner("💾 SAVING RESULTS TO GOOGLE DRIVE")

LOCAL_RENDER_DIR = "renders/overlays/remotion"
DRIVE_RENDER_DIR = f"{DRIVE_BASE_PATH}/renders/overlays/remotion"

if os.path.exists(LOCAL_RENDER_DIR):
    os.makedirs(DRIVE_RENDER_DIR, exist_ok=True)
    !cp -uv {LOCAL_RENDER_DIR}/* {DRIVE_RENDER_DIR}/
    print("✅ Upload complete.")
else:
    print("❌ No rendered files found.")

print_banner("🏁 PROCESS COMPLETE")
```
