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
!rm -rf public/renders/audios
!mkdir -p public/renders/audios

# 1. SFX Assets
print("\n🎵 --- SYNCING SFX ASSETS ---")
for drive_sfx in [f"{DRIVE_BASE_PATH}/renders/audios", f"{DRIVE_BASE_PATH}/renders/audio", f"{DRIVE_BASE_PATH}/render/audio", f"{DRIVE_BASE_PATH}/audio"]:
    if os.path.exists(drive_sfx):
        print(f"🔍 Searching for SFX in: {drive_sfx}")
        # Link everything found in the audio folder
        !ln -sf {drive_sfx}/* public/renders/audios/ 2>/dev/null
        # Recursive find for common extensions
        !find {drive_sfx} -maxdepth 2 -type f \( -iname "*.mp3" -o -iname "*.wav" -o -iname "*.m4a" -o -iname "*.aac" -o -iname "*.ogg" \) -exec ln -sf '{}' public/renders/audios/ ';' 2>/dev/null
        s_count = !ls public/renders/audios/ | wc -l
        print(f"📦 Successfully linked {s_count[0]} files to public/renders/audios/")
        if int(s_count[0]) > 0:
            !ls -p public/renders/audios/
        break
else:
    print("⚠️ WARNING: No SFX folder found in common Drive locations.")

# 2. Background Videos
print("\n🎬 --- SYNCING BACKGROUND VIDEOS ---")
print(f"🔍 Searching for videos in: {DRIVE_BASE_PATH}/renders")
!find {DRIVE_BASE_PATH}/renders -maxdepth 1 -name "*.mp4" -exec ln -sf '{}' public/renders/ ';' 2>/dev/null
v_count = !ls public/renders/*.mp4 | wc -l
print(f"✅ Successfully linked {v_count[0]} background videos to public/renders/")
if int(v_count[0]) > 0:
    !ls -lh public/renders/*.mp4

    # NEW: Ensure all background videos are consistent with 30fps
    print("🎬 Converting background videos to 30fps for engine consistency...")
    !bash ../scripts/convert_to_30fps.sh public/renders/

# 3. Fonts
print("\n✍️ --- SYNCING FONTS ---")
print(f"🔍 Searching for fonts in base path: {DRIVE_BASE_PATH}")
if os.path.exists(f"{DRIVE_BASE_PATH}/fonts"):
    !ln -sf {DRIVE_BASE_PATH}/fonts/* public/fonts/ 2>/dev/null
!find {DRIVE_BASE_PATH} -maxdepth 5 -type f \( -iname "*.ttf" -o -iname "*.otf" -o -iname "*.woff" -o -iname "*.woff2" \) -exec ln -sf '{}' public/fonts/ ';' 2>/dev/null

f_count = !ls public/fonts/ | wc -l
print(f"✅ Successfully linked {f_count[0]} fonts to public/fonts/")
if int(f_count[0]) > 0:
    !ls -p public/fonts/

print("\n✨ All Drive assets successfully linked to local public folder.")

%cd remotion_jsonMaker

print_banner("🛠️ INSTALLING PROJECT DEPENDENCIES")
!apt-get update -y && apt-get install -y ffmpeg build-essential
!pip install -r requirements.txt
!playwright install chromium
!playwright install-deps chromium

# 3. Context Verification
print_banner("📝 CONTEXT VERIFICATION")
if os.path.exists(STORY_FILE):
    print(f"✅ Found story file at: {STORY_FILE}")
else:
    print(f"❌ FATAL: Story file NOT FOUND: {STORY_FILE}")
    sys.exit("Input story file missing.")

# 4. Generate Master JSON
print_banner("🧠 GEMINI BROWSER AUTOMATION")
print("🚀 Using Playwright to interact with Gemini.")

!xvfb-run python generator.py \
    --story-file="{STORY_FILE}" \
    --output="{OUTPUT_JSON}" \
    --timestamp-output="{TIMESTAMP_FILE}" \
    --prompt-output="{PROMPT_FILE}" \
    --drive-prompt="{PROJECT_PATH}/guideline_prompt.txt" \
    --user-data-dir="{USER_DATA_DIR}" \
    --public-dir="/content/engine/public"

print_banner("🏁 PROCESS FINISHED")
if os.path.exists(OUTPUT_JSON):
    print(f"✅ Master manifest saved to: {OUTPUT_JSON}")
else:
    print(f"❌ ERROR: Output JSON was not created.")
```
