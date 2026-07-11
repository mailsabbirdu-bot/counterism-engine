# ☁️ Google Colab Setup (Counterism Studio V4)

Run the following cell in Google Colab to automate the process: Semantic Analysis -> Manifest Hardening -> Remotion Rendering.

```python
# ==============================================================================
# COUNTERISM STUDIO V4 — ONE-CELL SEMANTIC PIPELINE
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

# --- 1. MOUNT GOOGLE DRIVE ---
print_banner("📂 MOUNTING GOOGLE DRIVE")
from google.colab import drive
drive.mount('/content/drive')

# --- 2. SETUP ENVIRONMENT ---
PROJECT_NAME = "counterism-engine"
DRIVE_BASE_PATH = "/content/drive/MyDrive/Counterism_Studio_V4"
STORY_FILE = f"{DRIVE_BASE_PATH}/audio/story.txt"
TIMESTAMP_FILE = f"{DRIVE_BASE_PATH}/manifests/timestamp.txt"
FPS_UPDATE_FILE = f"{DRIVE_BASE_PATH}/manifests/fps_update.txt"
OUTPUT_JSON = "remotion_render.json"
DRIVE_MANIFEST_DIR = f"{DRIVE_BASE_PATH}/manifests"

%cd /content
if not os.path.exists(PROJECT_NAME):
    !git clone https://github.com/mailsabbirdu-bot/counterism-engine
%cd {PROJECT_NAME}

# --- 3. INSTALL NLP & RENDERING DEPENDENCIES ---
print_banner("🛠️ INSTALLING DEPENDENCIES")
!pip install -q stanza networkx pydantic regex
!apt-get update -y -qq && apt-get install -y -qq ffmpeg build-essential
!npm install --silent

# Download Stanza models for English (required for Semantic Engine)
import stanza
stanza.download('en', verbose=False)

# --- 4. SYNC ASSETS FROM DRIVE ---
print_banner("🔍 SYNCING ASSETS")
!mkdir -p public/renders/audios public/fonts public/audio

# Background Videos
if os.path.exists(f"{DRIVE_BASE_PATH}/renders"):
    !cp {DRIVE_BASE_PATH}/renders/*.mp4 public/renders/ 2>/dev/null || true

# Voiceovers & SFX
for sfx_path in [f"{DRIVE_BASE_PATH}/renders/audios", f"{DRIVE_BASE_PATH}/audio"]:
    if os.path.exists(sfx_path):
        !cp -r {sfx_path}/* public/renders/audios/ 2>/dev/null || true

# Fonts
if os.path.exists(f"{DRIVE_BASE_PATH}/fonts"):
    !cp -r {DRIVE_BASE_PATH}/fonts/* public/fonts/

# --- 5. SEMANTIC ANALYSIS (RULE-BASED PROTOTYPE) ---
print_banner("🧠 SEMANTIC UNDERSTANDING")
if os.path.exists(STORY_FILE):
    with open(STORY_FILE, 'r') as f:
        story_content = f.read()

    print("Running deterministic NLP analysis on script...")
    # Import from the newly created semantic_engine package
    import sys
    sys.path.append(os.getcwd())
    from semantic_engine.main import SemanticEngine

    engine = SemanticEngine()
    semantic_results = engine.process(story_content)

    # Save semantic results for reference
    os.makedirs("out/analysis", exist_ok=True)
    with open("out/analysis/semantic_model.json", 'w') as f:
        json.dump(semantic_results, f, indent=2)
    print("✅ Semantic Model generated in out/analysis/semantic_model.json")
else:
    print("⚠️ Skipping semantic analysis: story.txt not found in Drive.")

# --- 6. MANIFEST HARDENING & GENERATION (TITAN GUARD) ---
print_banner("🛡️ MANIFEST HARDENING (TITAN GUARD)")
# This runs the production generator which handles AI-hallucination repair and rhythmic staggering
!python3 remotion_jsonMaker/generator.py \
    --story-file {STORY_FILE} \
    --output {OUTPUT_JSON} \
    --timestamp-file {TIMESTAMP_FILE} \
    --fps-update-file {FPS_UPDATE_FILE} \
    --public-dir public/

# Sync generated manifest back to Drive
if os.path.exists(OUTPUT_JSON):
    os.makedirs(DRIVE_MANIFEST_DIR, exist_ok=True)
    shutil.copy(OUTPUT_JSON, f"{DRIVE_MANIFEST_DIR}/remotion_render.json")
    print(f"✅ Hardened manifest synced to Drive: {DRIVE_MANIFEST_DIR}/remotion_render.json")

# --- 7. START RENDERING ---
print_banner("🎬 STARTING RENDERING PIPELINE")
!npm run render -- --concurrency=1

# --- 8. SYNC RENDERS TO DRIVE ---
print_banner("💾 SAVING RESULTS TO GOOGLE DRIVE")
LOCAL_RENDER_DIR = "renders/overlays/remotion"
DRIVE_RENDER_DIR = f"{DRIVE_BASE_PATH}/renders/overlays/remotion"
if os.path.exists(LOCAL_RENDER_DIR):
    os.makedirs(DRIVE_RENDER_DIR, exist_ok=True)
    !cp -rvu {LOCAL_RENDER_DIR}/* {DRIVE_RENDER_DIR}/

print_banner("🏁 ALL TASKS COMPLETE")
```
