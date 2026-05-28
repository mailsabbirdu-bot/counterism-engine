# ☁️ Google Colab Setup (Counterism Studio V4)

Run the following cell in Google Colab to automate the entire process with ultra-debugging enabled.

```python
# ==============================================================================
# COUNTERISM STUDIO V4 — AUTOMATED CINEMATIC PIPELINE (ULTRA VERBOSE DEBUG)
# ==============================================================================

import os
import shutil
import subprocess

def print_banner(text):
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80)

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

# Ensure local directories exist
os.makedirs("public/renders", exist_ok=True)
os.makedirs("public/audio", exist_ok=True)

# Use real copies instead of symlinks for maximum compatibility in headless environments
drive_renders = f"{DRIVE_BASE_PATH}/renders"
if os.path.exists(drive_renders):
    print(f"📡 Found Drive renders folder: {drive_renders}")
    print("📦 Copying assets to local public/renders (this may take a moment)...")
    !rm -rf public/renders/*
    !cp -r {drive_renders}/* public/renders/

    print("\n🧐 VERIFYING public/renders CONTENT:")
    !ls -lsh public/renders/

    print("\n✅ CHECKING FOR CRITICAL ASSETS:")
    for f in ["scene_SC_01.mp4", "scene_SC_02.mp4"]:
        path = f"public/renders/{f}"
        if os.path.exists(path):
            print(f"  [OK] {path} ({os.path.getsize(path)/(1024*1024):.2f} MB)")
        else:
            print(f"  [!!] {path} is MISSING!")
else:
    print(f"❌ FATAL: 'renders' folder NOT FOUND in Drive: {drive_renders}")

# Sync audio folder
drive_audio = f"{DRIVE_BASE_PATH}/audio"
if os.path.exists(drive_audio):
    print(f"\n📡 Found Drive audio folder: {drive_audio}")
    !rm -rf public/audio/*
    !cp -r {drive_audio}/* public/audio/
    print(f"✅ Copied {len(os.listdir('public/audio'))} audio files.")

print_banner("📂 PROJECT STRUCTURE (DEBUG)")
!find public -maxdepth 2 -not -path '*/.*'

# 4. Install System & Node Dependencies
print_banner("🛠️ INSTALLING DEPENDENCIES")
print("📦 Installing system dependencies...")
!apt-get update -y && apt-get install -y ffmpeg build-essential

print("📦 Installing Node.js dependencies...")
!npm install

# 5. Render Pipeline with Optimized Concurrency
print_banner("🎬 STARTING RENDERING PIPELINE")
# Concurrency=1 is safest for Colab to avoid Protocol Errors
!npm run render -- --concurrency=1

# 6. Automatic Drive Upload (Recursive)
print_banner("💾 SAVING RESULTS TO GOOGLE DRIVE")

LOCAL_RENDER_DIR = "renders/overlays/remotion"
DRIVE_RENDER_DIR = f"{DRIVE_BASE_PATH}/renders/overlays/remotion"

if os.path.exists(LOCAL_RENDER_DIR):
    print(f"📂 Destination: {DRIVE_RENDER_DIR}")
    os.makedirs(DRIVE_RENDER_DIR, exist_ok=True)
    !cp -uv {LOCAL_RENDER_DIR}/* {DRIVE_RENDER_DIR}/
    print("\n✅ Upload complete.")
else:
    print("❌ No rendered files found.")

print_banner("🏁 PROCESS COMPLETE")
```
