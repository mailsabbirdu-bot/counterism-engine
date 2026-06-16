# ☁️ Google Colab Setup (Counterism Studio V4)

Run the following cell in Google Colab to automate the process with dynamic duration adjustment and Drive-based manifests.

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

# 3. Handle External Assets (Renders, Audio, Fonts, SFX)
print_banner("🔍 ASSET VERIFICATION & COPYING")

os.makedirs("public/renders/audios", exist_ok=True)
os.makedirs("public/audio", exist_ok=True)
os.makedirs("public/fonts", exist_ok=True)

# Sync Background Videos
drive_renders = f"{DRIVE_BASE_PATH}/renders"
if os.path.exists(drive_renders):
    print(f"📡 Syncing renders from: {drive_renders}")
    !rm -rf public/renders/*
    # Copy all mp4 files from the renders root, but ignore the audios subfolder which we sync separately
    !find {drive_renders} -maxdepth 1 -name "*.mp4" -exec cp -t public/renders/ {{}} +
    print(f"✅ Synced background videos.")
else:
    print(f"❌ FATAL: 'renders' folder NOT FOUND in Drive: {drive_renders}")

# Sync Voiceovers
drive_audio = f"{DRIVE_BASE_PATH}/audio"
if os.path.exists(drive_audio):
    print(f"📡 Syncing voiceovers from: {drive_audio}")
    !rm -rf public/audio/*
    !cp -r {drive_audio}/* public/audio/
    print(f"✅ Synced voiceover files.")

# Sync SFX
drive_sfx = f"{DRIVE_BASE_PATH}/renders/audios"
if os.path.exists(drive_sfx):
    print(f"📡 Syncing SFX from: {drive_sfx}")
    !rm -rf public/renders/audios/*
    !cp -r {drive_sfx}/* public/renders/audios/
    print(f"✅ Synced SFX assets.")

# Sync Fonts
drive_fonts = f"{DRIVE_BASE_PATH}/fonts"
if os.path.exists(drive_fonts):
    print(f"📡 Syncing fonts from: {drive_fonts}")
    !rm -rf public/fonts/*
    !cp -r {drive_fonts}/* public/fonts/
    print(f"✅ Synced font assets.")
else:
    print(f"⚠️  Drive fonts folder NOT FOUND: {drive_fonts}")

# 4. Manifest Verification
print_banner("📜 MANIFEST VERIFICATION")

MANIFEST_DIR = f"{DRIVE_BASE_PATH}/manifests"
DRIVE_JSON = f"{MANIFEST_DIR}/remotion_render.json"

if os.path.exists(DRIVE_JSON):
    print(f"✅ Found Drive manifest: {DRIVE_JSON}")
else:
    print(f"❌ FATAL: Manifest NOT FOUND in Drive: {DRIVE_JSON}")
    print("Please place your 'remotion_render.json' in the manifests folder on Google Drive.")

# 5. Install Dependencies
print_banner("🛠️ INSTALLING DEPENDENCIES")
!apt-get update -y && apt-get install -y ffmpeg build-essential
!npm install

# 6. Render Pipeline
print_banner("🎬 STARTING RENDERING PIPELINE")
# The pipeline will automatically use remotion_render.json from Google Drive by default
!npm run render -- --concurrency=1

# 7. Automatic Drive Upload
print_banner("💾 SAVING RESULTS TO GOOGLE DRIVE")

LOCAL_RENDER_DIR = "renders/overlays/remotion"
DRIVE_RENDER_DIR = f"{DRIVE_BASE_PATH}/renders/overlays/remotion"

# Check both local and drive locations (since render.ts might output to Drive directly)
if os.path.exists(LOCAL_RENDER_DIR) or os.path.exists(DRIVE_RENDER_DIR):
    # Ensure Drive destination exists
    print(f"📡 Verifying Drive directory: {DRIVE_RENDER_DIR}")
    os.makedirs(DRIVE_RENDER_DIR, exist_ok=True)

    if os.path.exists(LOCAL_RENDER_DIR):
        print("📦 Syncing local renders to Drive...")
        !cp -rvu {LOCAL_RENDER_DIR}/* {DRIVE_RENDER_DIR}/
    else:
        print("ℹ️  Renders already produced in Drive directory.")

    # Final verification of upload
    drive_count = len(os.listdir(DRIVE_RENDER_DIR))
    print(f"✅ Process complete. {drive_count} files currently in Drive render folder.")
else:
    print("❌ FATAL: Render directory NOT FOUND in local or Drive. Rendering may have failed.")

print_banner("🏁 PROCESS COMPLETE")
```
