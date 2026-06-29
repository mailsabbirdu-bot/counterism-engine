# 🤖 Counterism Studio V4 JSON Maker (Playwright Gemini Edition)

Run this cell in Google Colab to generate your `remotion_render.json` using **Gemini** via browser automation.

```python
# ==============================================================================
# COUNTERISM STUDIO V4 — GEMINI BROWSER JSON MASTER GENERATOR
# ==============================================================================

import os
import sys
from google.colab import drive

def print_banner(text):
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80)

# 1. Configuration
PROJECT_PATH = "/content/engine"
DRIVE_BASE_PATH = "/content/drive/MyDrive/Counterism_Studio_V4"
STORY_FILE = f"{DRIVE_BASE_PATH}/audio/story.txt"
OUTPUT_JSON = f"{DRIVE_BASE_PATH}/manifests/remotion_render.json"
PROMPT_FILE = f"{DRIVE_BASE_PATH}/manifests/remotion_prompt.txt"
TIMESTAMP_FILE = f"{DRIVE_BASE_PATH}/manifests/timestamp.txt"
USER_DATA_DIR = f"{DRIVE_BASE_PATH}/browser_session"
ANALYSIS_DIR = f"{DRIVE_BASE_PATH}/manifests/analysis"

# 2. Setup
print_banner("📂 MOUNTING GOOGLE DRIVE")
drive.mount('/content/drive')

%cd /content
if not os.path.exists(PROJECT_PATH):
    print("🚀 Cloning engine...")
    !git clone https://github.com/mailsabbirdu-bot/counterism-engine {PROJECT_PATH}
else:
    print("✅ Engine already cloned.")

%cd {PROJECT_PATH}

# Link Drive assets to Remotion public folder
print_banner("🔗 LINKING DRIVE ASSETS")
# Ensure public directories exist
!mkdir -p public/renders
!mkdir -p public/fonts
!mkdir -p public/renders/analysis
!rm -rf public/renders/audios
!mkdir -p public/renders/audios

# 1. SFX Assets
print("\n🎵 --- SYNCING SFX ASSETS ---")
import glob
for drive_sfx in [f"{DRIVE_BASE_PATH}/renders/audios", f"{DRIVE_BASE_PATH}/renders/audio", f"{DRIVE_BASE_PATH}/render/audio", f"{DRIVE_BASE_PATH}/audio"]:
    if os.path.exists(drive_sfx):
        print(f"🔍 Linking assets from: {drive_sfx}")
        for ext in ["*.mp3", "*.wav", "*.m4a", "*.aac", "*.ogg"]:
            for f in glob.glob(os.path.join(drive_sfx, "**", ext), recursive=True):
                !ln -sf "{f}" public/renders/audios/ 2>/dev/null

s_count = !ls public/renders/audios/ | wc -l
print(f"📦 Successfully linked {s_count[0]} files to public/renders/audios/")

# 2. Background Videos
print("\n🎬 --- SYNCING BACKGROUND VIDEOS ---")
import glob
drive_renders = f"{DRIVE_BASE_PATH}/renders"
if os.path.exists(drive_renders):
    for f in glob.glob(os.path.join(drive_renders, "*.mp4")):
        !ln -sf "{f}" public/renders/
v_count = !ls public/renders/*.mp4 | wc -l
print(f"✅ Successfully linked {v_count[0]} background videos to public/renders/")

# 3. Visual Eye Analysis
print("\n👁️ --- SYNCING VISUAL ANALYSIS ---")
os.makedirs(ANALYSIS_DIR, exist_ok=True)
!ln -sf {ANALYSIS_DIR}/* public/renders/analysis/ 2>/dev/null
a_count = !ls public/renders/analysis/*.json | wc -l
print(f"✅ Successfully linked {a_count[0]} analysis files.")

# 4. Fonts
print("\n✍️ --- SYNCING FONTS ---")
!find {DRIVE_BASE_PATH} -maxdepth 5 -type f \( -iname "*.ttf" -o -iname "*.otf" -o -iname "*.woff" -o -iname "*.woff2" \) -exec ln -sf '{}' public/fonts/ ';' 2>/dev/null

print("\n✨ All Drive assets successfully linked to local public folder.")

print_banner("🛠️ INSTALLING PROJECT DEPENDENCIES")
!apt-get update -y -qq && apt-get install -y -qq ffmpeg build-essential
!pip install -q -r remotion_jsonMaker/requirements.txt
!playwright install chromium
!playwright install-deps chromium

# 👁️ VISUAL EYE STAGE
print_banner("👁️ VISUAL EYE: PERCEPTION STAGE")
%cd {PROJECT_PATH}
import glob
videos = glob.glob("public/renders/*.mp4")
if videos:
    print(f"🚀 Analyzing {len(videos)} videos for production grounding...")
    # Add project root to path for visual_eye imports
    sys.path.append(PROJECT_PATH)
    from visual_eye.analyzer import analyze_video
    for v in videos:
        analyze_video(v, "public/renders/analysis")
    # Sync back to Drive
    !cp -n public/renders/analysis/*.json {ANALYSIS_DIR}/ 2>/dev/null
    print("✅ Analysis complete and synced to Drive.")
else:
    print("⚠️ No videos found for analysis.")

%cd remotion_jsonMaker

# 4. Generate Master JSON
print_banner("🧠 GEMINI BROWSER AUTOMATION")
FPS_UPDATE_FILE = f"{DRIVE_BASE_PATH}/manifests/fps_update.txt"

%run generator.py \
    --story-file="{STORY_FILE}" \
    --output="{OUTPUT_JSON}" \
    --timestamp-file="{TIMESTAMP_FILE}" \
    --fps-update-file="{FPS_UPDATE_FILE}" \
    --prompt-output="{PROMPT_FILE}" \
    --drive-prompt="{PROJECT_PATH}/guideline_prompt.txt" \
    --user-data-dir="{USER_DATA_DIR}" \
    --public-dir="{PROJECT_PATH}/public" \
    --manual

print_banner("🏁 PROCESS FINISHED")
```
