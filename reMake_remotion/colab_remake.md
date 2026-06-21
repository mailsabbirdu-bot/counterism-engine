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

!python reMake_remotion/remaker.py
```
