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
!mkdir -p public/renders
!mkdir -p public/audio

# Sync renders folder (using symlinks for nested structures from Drive)
if os.path.exists(f"{DRIVE_BASE_PATH}/renders"):
    print("✅ Found 'renders' in Drive. Linking files...")
    !cp -rs {DRIVE_BASE_PATH}/renders/* public/renders/ 2>/dev/null || true
else:
    print("⚠️ 'renders' folder not found in Drive.")

# Sync audio folder
if os.path.exists(f"{DRIVE_BASE_PATH}/audio"):
    print("✅ Found 'audio' in Drive. Linking files...")
    !cp -rs {DRIVE_BASE_PATH}/audio/* public/audio/ 2>/dev/null || true
else:
    print("⚠️ 'audio' folder not found in Drive.")

# 4. Install System & Node Dependencies
print("🛠️ Installing system dependencies (ffmpeg, build-essential)...")
!apt-get update -y && apt-get install -y ffmpeg build-essential

print("📦 Installing Node.js dependencies...")
!npm install

# 5. Render Pipeline with Ultra-Debugging
print("\n🎬 STARTING RENDERING PIPELINE...")
print("--------------------------------------------------------------------------------")
!DEBUG=remotion:* npm run render -- --verbose 2>&1 | tee render_debug.log

# 6. Automatic Drive Upload
print("\n--------------------------------------------------------------------------------")
print("💾 SAVING RESULTS TO GOOGLE DRIVE...")

LOCAL_RENDER_DIR = "renders/overlays/remotion"
DRIVE_RENDER_DIR = f"{DRIVE_BASE_PATH}/renders/overlays/remotion"

if os.path.exists(LOCAL_RENDER_DIR):
    print(f"📂 Creating destination in Drive: {DRIVE_RENDER_DIR}")
    os.makedirs(DRIVE_RENDER_DIR, exist_ok=True)

    print(f"📤 Copying rendered files to Drive...")
    for filename in os.listdir(LOCAL_RENDER_DIR):
        if filename.endswith(".mp4") or filename.endswith(".webm"):
            src = os.path.join(LOCAL_RENDER_DIR, filename)
            dst = os.path.join(DRIVE_RENDER_DIR, filename)
            print(f"   -> {filename}")
            shutil.copy2(src, dst)

    print("\n✅ All rendered scenes have been saved to your Google Drive!")
else:
    print("❌ No rendered files found in local 'renders/overlays/remotion' directory.")

print("\n🏁 PROCESS COMPLETE.")
```
