# ☁️ Google Colab Setup (Counterism Studio V4)

Run the following cell in Google Colab to automate the entire process with ultra-debugging enabled.

```python
# ==============================================================================
# COUNTERISM STUDIO V4 — AUTOMATED CINEMATIC PIPELINE
# ==============================================================================
# One-cell solution to setup, link Drive, and render.

import os
import shutil

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
print("🔗 Linking Drive assets to project...")
# Ensure local directories exist
os.makedirs("public/renders", exist_ok=True)
os.makedirs("public/audio", exist_ok=True)

# Robust sync for renders folder
drive_renders = f"{DRIVE_BASE_PATH}/renders"
if os.path.exists(drive_renders):
    print(f"✅ Found 'renders' in Drive ({drive_renders}). Linking files...")
    # Using recursive copy for symlinks to handle nested directories correctly
    !cp -rs {drive_renders}/* public/renders/ 2>/dev/null || true

    # Verification check
    linked_files = os.listdir("public/renders")
    print(f"📁 Linked files in public/renders: {linked_files}")
else:
    print(f"⚠️ 'renders' folder not found in Drive at: {drive_renders}")

# Sync audio folder
drive_audio = f"{DRIVE_BASE_PATH}/audio"
if os.path.exists(drive_audio):
    print(f"✅ Found 'audio' in Drive ({drive_audio}). Linking files...")
    !cp -rs {drive_audio}/* public/audio/ 2>/dev/null || true
else:
    print(f"⚠️ 'audio' folder not found in Drive at: {drive_audio}")

# 4. Install System & Node Dependencies
print("🛠️ Installing system dependencies (ffmpeg, build-essential)...")
!apt-get update -y && apt-get install -y ffmpeg build-essential

print("📦 Installing Node.js dependencies...")
!npm install

# 5. Render Pipeline with Optimized Concurrency
print("\n🎬 STARTING RENDERING PIPELINE...")
print("--------------------------------------------------------------------------------")
# The render.ts is already configured with concurrency: 4 for speed
!npm run render

# 6. Automatic Drive Upload (Recursive)
print("\n--------------------------------------------------------------------------------")
print("💾 SAVING RESULTS TO GOOGLE DRIVE...")

LOCAL_RENDER_DIR = "renders/overlays/remotion"
DRIVE_RENDER_DIR = f"{DRIVE_BASE_PATH}/renders/overlays/remotion"

if os.path.exists(LOCAL_RENDER_DIR):
    print(f"📂 Creating destination in Drive: {DRIVE_RENDER_DIR}")
    os.makedirs(DRIVE_RENDER_DIR, exist_ok=True)

    print(f"📤 Uploading rendered files to Drive...")
    # Using 'cp' to handle recursive directory structures if any
    !cp -rv {LOCAL_RENDER_DIR}/* {DRIVE_RENDER_DIR}/

    print("\n✅ All rendered scenes have been saved to your Google Drive!")
else:
    print("❌ No rendered files found in local 'renders/overlays/remotion' directory.")

print("\n🏁 PROCESS COMPLETE.")
```
