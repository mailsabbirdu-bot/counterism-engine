# ☁️ Google Colab Setup (Counterism Studio V4)

Run the following cell in Google Colab to automate the entire process with ultra-debugging enabled.

```python
# ==============================================================================
# COUNTERISM STUDIO V4 — AUTOMATED CINEMATIC PIPELINE (ULTRA VERBOSE DEBUG)
# ==============================================================================

import os
import shutil
import subprocess

def check_file(path):
    if os.path.exists(path):
        size = os.path.getsize(path) / (1024 * 1024)
        print(f"✅ [FOUND] {path} ({size:.2f} MB)")
        return True
    else:
        print(f"❌ [MISSING] {path}")
        return False

# 1. Mount Google Drive
from google.colab import drive
print("📂 Mounting Google Drive...")
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
print("\n🔍 ASSET VERIFICATION & LINKING...")
print("--------------------------------------------------------------------------------")

# Ensure local directories exist
os.makedirs("public/renders", exist_ok=True)
os.makedirs("public/audio", exist_ok=True)

# Robust sync for renders folder
drive_renders = f"{DRIVE_BASE_PATH}/renders"
if os.path.exists(drive_renders):
    print(f"📡 Found Drive renders folder: {drive_renders}")
    print("🔗 Creating symbolic links...")
    # Clear existing links to avoid duplicates/errors
    !rm -rf public/renders/*
    !cp -rs {drive_renders}/* public/renders/ 2>/dev/null || true

    # Comprehensive Verification
    print("\n🧐 Verifying linked files in 'public/renders':")
    files = os.listdir("public/renders")
    if not files:
        print("⚠️ Warning: No files found in 'public/renders' after linking!")
    else:
        for f in files:
            local_path = os.path.join("public/renders", f)
            if os.path.islink(local_path):
                target = os.readlink(local_path)
                if os.path.exists(target):
                    print(f"✅ LINK OK: {f} -> {target} ({os.path.getsize(target)/(1024*1024):.2f} MB)")
                else:
                    print(f"❌ BROKEN LINK: {f} -> {target} (Target does not exist!)")
            else:
                print(f"📄 FILE (Not Link): {f} ({os.path.getsize(local_path)/(1024*1024):.2f} MB)")
else:
    print(f"❌ FATAL: 'renders' folder NOT FOUND in Drive at: {drive_renders}")
    print("   Please check your Drive folder structure: Counterism_Studio_V4/renders/")

# Sync audio folder
drive_audio = f"{DRIVE_BASE_PATH}/audio"
if os.path.exists(drive_audio):
    print(f"\n📡 Found Drive audio folder: {drive_audio}")
    !rm -rf public/audio/*
    !cp -rs {drive_audio}/* public/audio/ 2>/dev/null || true
    print(f"✅ Linked {len(os.listdir('public/audio'))} audio files.")
else:
    print(f"⚠️ 'audio' folder not found in Drive at: {drive_audio}")

# 4. Install System & Node Dependencies
print("\n🛠️ INSTALLING DEPENDENCIES...")
print("--------------------------------------------------------------------------------")
print("📦 Installing system dependencies (ffmpeg, build-essential)...")
!apt-get update -y && apt-get install -y ffmpeg build-essential

print("📦 Installing Node.js dependencies...")
!npm install

# 5. Render Pipeline with Optimized Concurrency
print("\n🎬 STARTING RENDERING PIPELINE...")
print("--------------------------------------------------------------------------------")
# Pass concurrency=1 for maximum stability in Colab
!npm run render -- --concurrency=1

# 6. Automatic Drive Upload (Recursive)
print("\n--------------------------------------------------------------------------------")
print("💾 SAVING RESULTS TO GOOGLE DRIVE...")

LOCAL_RENDER_DIR = "renders/overlays/remotion"
DRIVE_RENDER_DIR = f"{DRIVE_BASE_PATH}/renders/overlays/remotion"

if os.path.exists(LOCAL_RENDER_DIR):
    print(f"📂 Destination in Drive: {DRIVE_RENDER_DIR}")
    os.makedirs(DRIVE_RENDER_DIR, exist_ok=True)

    print(f"📤 Uploading rendered files...")
    # Use -u (update) and -v (verbose)
    !cp -uv {LOCAL_RENDER_DIR}/* {DRIVE_RENDER_DIR}/

    print("\n✅ Rendered scenes saved successfully!")
else:
    print("❌ No rendered files found to upload.")

print("\n🏁 PROCESS COMPLETE.")
```
