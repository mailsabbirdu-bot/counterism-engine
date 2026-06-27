# 🎬 Counterism Studio V4 - Scene Remake Cell

This single cell enables interactive refinement and re-rendering of specific scenes from your manifest.

```python
import os
import shutil

# --- 1. ENVIRONMENT SETUP ---
print("🚀 Initializing Remake Environment...")
if not os.path.exists("/content/drive"):
    from google.colab import drive
    drive.mount('/content/drive')

# Paths
ENGINE_DIR = "/content/engine"
DRIVE_MANIFEST = "/content/drive/MyDrive/Counterism_Studio_V4/manifests/remotion_render.json"

# Clone / Update Engine
if not os.path.exists(ENGINE_DIR):
    !git clone https://github.com/mailsabbirdu-bot/counterism-engine {ENGINE_DIR}
else:
    %cd {ENGINE_DIR}
    !git pull

%cd {ENGINE_DIR}

# --- 1b. SYNC ASSETS FROM DRIVE ---
print("📡 Syncing Assets from Drive...")
!mkdir -p public/renders/audios public/fonts

# Sync Renders
!cp -f /content/drive/MyDrive/Counterism_Studio_V4/renders/*.mp4 public/renders/ 2>/dev/null || true
# Sync SFX
!find /content/drive/MyDrive/Counterism_Studio_V4/renders/audios -maxdepth 2 -type f \( -iname "*.mp3" -o -iname "*.wav" -o -iname "*.m4a" -o -iname "*.aac" -o -iname "*.ogg" \) -exec cp -f '{}' public/renders/audios/ ';' 2>/dev/null || true
!find /content/drive/MyDrive/Counterism_Studio_V4/audio -maxdepth 2 -type f \( -iname "*.mp3" -o -iname "*.wav" -o -iname "*.m4a" -o -iname "*.aac" -o -iname "*.ogg" \) -exec cp -f '{}' public/renders/audios/ ';' 2>/dev/null || true
# Sync Fonts
!cp -f /content/drive/MyDrive/Counterism_Studio_V4/*.ttf public/fonts/ 2>/dev/null || true
!cp -f /content/drive/MyDrive/Counterism_Studio_V4/fonts/*.ttf public/fonts/ 2>/dev/null || true

# Install Playwright for Gemini Refinement
if shutil.which("playwright") is None:
    print("🛠️ Installing Automation Tools...")
    !pip install playwright playwright-stealth
    !playwright install chromium
    !playwright install-deps

# Install Project Deps
if not os.path.exists("node_modules"):
    print("🛠️ Installing Project Dependencies...")
    !npm install

# --- 2. RUN INTERACTIVE REMAKER ---
print("\n" + "="*80)
print(" 🛠️  SCENE REMAKER INTERACTIVE CLI")
print("="*80)

# IMPORTANT: We use %run instead of !python to allow rich HTML output and terminal input in Colab.
%run reMake_remotion/remaker.py
```
