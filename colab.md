# ☁️ Google Colab Setup (Counterism Studio V4)

Run the following cell in Google Colab to automate the entire process with ultra-debugging enabled.

```python
# ==============================================================================
# COUNTERISM STUDIO V4 — AUTOMATED CINEMATIC PIPELINE
# ==============================================================================
# One-cell solution to setup, link Drive, and render.

import os

# 1. Mount Google Drive
from google.colab import drive
print("📂 Mounting Google Drive...")
drive.mount('/content/drive')

# 2. Setup Project Environment
PROJECT_NAME = "counterism-engine"
DRIVE_BASE_PATH = "/content/drive/MyDrive/Counterism_Studio_V4"
REPO_URL = "https://github.com/mailsabbirdu-bot/counterism-engine"

print(f"🚀 Cloning repository: {REPO_URL}")
!git clone {REPO_URL}
%cd {PROJECT_NAME}

# 3. Handle External Assets (Renders & Audio)
# We symlink Drive folders to the Project's public folder to ensure Remotion finds them.
print("🔗 Linking Drive assets to project...")
!mkdir -p public/renders
!mkdir -p public/audio

# Sync renders folder
if os.path.exists(f"{DRIVE_BASE_PATH}/renders"):
    print("✅ Found 'renders' in Drive. Linking...")
    # Using 'cp' might be safer than symlinks for some Node/Remotion edge cases in Colab
    !cp -rv {DRIVE_BASE_PATH}/renders/* public/renders/
else:
    print("⚠️ 'renders' folder not found in Drive. Using default project assets.")

# Sync audio folder
if os.path.exists(f"{DRIVE_BASE_PATH}/audio"):
    print("✅ Found 'audio' in Drive. Linking...")
    !cp -rv {DRIVE_BASE_PATH}/audio/* public/audio/
else:
    print("⚠️ 'audio' folder not found in Drive.")

# 4. Install System & Node Dependencies
# Note: node_modules stays in Colab local memory (outside Drive) to prevent sync errors.
print("🛠️ Installing system dependencies (ffmpeg, build-essential)...")
!apt-get update -y && apt-get install -y ffmpeg build-essential

print("📦 Installing Node.js dependencies...")
!npm install

# 5. Render Pipeline with Ultra-Debugging
print("\n🎬 STARTING RENDERING PIPELINE...")
print("--------------------------------------------------------------------------------")
# We use --verbose and pipe output to catch every detail
!DEBUG=remotion:* npm run render -- --verbose 2>&1 | tee render_debug.log

print("\n--------------------------------------------------------------------------------")
print("🏁 RENDERING PROCESS COMPLETE.")
print("📁 Output files are located in 'renders/overlays/remotion/' within the project folder.")
print("💾 Remember to copy them back to your Drive if needed:")
print(f"!mkdir -p {DRIVE_BASE_PATH}/renders/overlays/remotion")
print(f"!cp -rv renders/overlays/remotion/* {DRIVE_BASE_PATH}/renders/overlays/remotion/")
```
