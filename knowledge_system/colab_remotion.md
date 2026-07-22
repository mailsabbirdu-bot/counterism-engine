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
# Fetch and checkout active feature branch containing the threading loop fix
!git fetch origin && git checkout feature/evidence-asyncio-loop-fix || true

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
import shutil
if not shutil.which('ffmpeg'):
    print("📡 ffmpeg not found. Installing via apt-get...")
    !apt-get update -y -qq && apt-get install -y -qq ffmpeg build-essential
else:
    print("✅ ffmpeg and build-essential are already installed. Skipping slow apt-get update.")
!npm install --silent

# --- 5. EXECUTE REMOTION RENDER ---
print_banner("🎬 STARTING RENDERING PIPELINE")
# Pass the custom manifest to the render script
!npm run render -- --template=remotion_render.json --concurrency=1

# --- 6. SAVE OUTPUT TO DRIVE ---
print_banner("💾 SAVING FINAL VIDEO TO DRIVE")
# Standard naming for CRVE renders in Colab
import glob
renders = glob.glob("renders/**/*.mp4", recursive=True)

if renders:
    print(f"📦 Found {len(renders)} render artifacts. Copying to Drive...")
    for i, r_path in enumerate(sorted(renders)):
        filename = os.path.basename(r_path)
        dest = f"{OUTPUT_DIR}/final_{filename}"
        shutil.copy(r_path, dest)
        print(f"   ✅ Saved: {dest}")
    print(f"\n✨ SUCCESS! All renders saved to: {OUTPUT_DIR}")
else:
    print("❌ ERROR: No render output (.mp4) found in project directory.")

print_banner("🏁 RENDER COMPLETE")
```
