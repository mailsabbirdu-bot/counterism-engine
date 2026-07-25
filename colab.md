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

# 1. Mount Google Drive
print_banner("📂 MOUNTING GOOGLE DRIVE")
if not os.path.exists('/content/drive'):
    try:
        from google.colab import drive
        drive.mount('/content/drive')
    except Exception as e:
        print("⚠️ Standard mount failed: ", e)
        print("💡 TIP: Please click the folder icon on the left panel of Colab and click the 'Mount Drive' button to mount your Drive instantly and securely in your WebView!")
else:
    print("✅ Google Drive is already mounted and ready!")

# 2. Setup Project Environment
PROJECT_NAME = "counterism-engine"
DRIVE_BASE_PATH = "/content/drive/MyDrive/Counterism_Studio_V4"
REPO_URL = "https://github.com/mailsabbirdu-bot/counterism-engine"

%cd /content
if not os.path.exists(PROJECT_NAME):
    print(f"🚀 Cloning repository: {REPO_URL}")
    !git clone {REPO_URL}
else:
    print(f"✅ Project folder '{PROJECT_NAME}' already exists.")

%cd {PROJECT_NAME}
# Fetch and checkout active feature branch containing the threading loop fix
!git fetch origin && git checkout feature/evidence-asyncio-loop-fix || true

# 3. Handle External Assets (Renders, Audio, Fonts, SFX)
print_banner("🔍 ASSET VERIFICATION & COPYING")

# Crucial: Clean and create directories in the correct order
!rm -rf public/renders
!mkdir -p public/renders/audios
!mkdir -p public/audio
!mkdir -p public/fonts

# Sync Background Videos
drive_renders = f"{DRIVE_BASE_PATH}/renders"
if os.path.exists(drive_renders):
    print(f"📡 Syncing renders from: {drive_renders}")
    import glob
    for f in glob.glob(os.path.join(drive_renders, "*.mp4")):
        shutil.copy(f, "public/renders/")
else:
    print(f"❌ FATAL: 'renders' folder NOT FOUND in Drive: {drive_renders}")

# Sync Voiceovers
drive_audio = f"{DRIVE_BASE_PATH}/audio"
if os.path.exists(drive_audio):
    !cp -r {drive_audio}/* public/audio/

# Sync SFX & Narration (Recursive sync from multiple Drive locations)
print("📡 Searching for SFX and narration assets...")
import glob
for sfx_path in [f"{DRIVE_BASE_PATH}/renders/audios", f"{DRIVE_BASE_PATH}/renders/audio", f"{DRIVE_BASE_PATH}/audio"]:
    if os.path.exists(sfx_path):
        print(f"📦 Syncing audio from: {sfx_path}")
        for ext in ["*.mp3", "*.wav", "*.m4a", "*.aac", "*.ogg"]:
            for f in glob.glob(os.path.join(sfx_path, "**", ext), recursive=True):
                shutil.copy(f, "public/renders/audios/")

# Sync Fonts
drive_fonts = f"{DRIVE_BASE_PATH}/fonts"
if os.path.exists(drive_fonts):
    !cp -r {drive_fonts}/* public/fonts/

# 4. Manifest Verification
print_banner("📜 MANIFEST VERIFICATION")
DRIVE_JSON = f"{DRIVE_BASE_PATH}/manifests/remotion_render.json"
if os.path.exists(DRIVE_JSON):
    print(f"✅ Found Drive manifest: {DRIVE_JSON}")
else:
    print(f"❌ FATAL: Manifest NOT FOUND in Drive: {DRIVE_JSON}")

# 5. Install Dependencies
print_banner("🛠️ INSTALLING DEPENDENCIES")
# Use -qq and --silent to ignore verbose node/apt messages
import shutil
if not shutil.which('ffmpeg'):
    print("📡 ffmpeg not found. Installing via apt-get...")
    !apt-get update -y -qq && apt-get install -y -qq ffmpeg build-essential
else:
    print("✅ ffmpeg and build-essential are already installed. Skipping slow apt-get update.")
!npm install --silent

# 6. Render Pipeline
print_banner("🎬 STARTING RENDERING PIPELINE")
!npm run render -- --concurrency=1

# 7. Automatic Drive Upload
print_banner("💾 SAVING RESULTS TO GOOGLE DRIVE")
LOCAL_RENDER_DIR = "renders/overlays/remotion"
DRIVE_RENDER_DIR = f"{DRIVE_BASE_PATH}/renders/overlays/remotion"
if os.path.exists(LOCAL_RENDER_DIR):
    os.makedirs(DRIVE_RENDER_DIR, exist_ok=True)
    !cp -rvu {LOCAL_RENDER_DIR}/* {DRIVE_RENDER_DIR}/

print_banner("🏁 PROCESS COMPLETE")
```
