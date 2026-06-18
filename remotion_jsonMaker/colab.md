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

# Deep link SFX files (Search multiple possible Drive locations)
print("Linking audio SFX files...")
for drive_sfx in [f"{DRIVE_BASE_PATH}/renders/audios", f"{DRIVE_BASE_PATH}/render/audio"]:
    if os.path.exists(drive_sfx):
        print(f"📦 Found SFX folder: {drive_sfx}")
        !find {drive_sfx} -maxdepth 2 -type f -exec ln -sf '{}' public/renders/audios/ ';' 2>/dev/null

# Sync background videos and fonts
print("Linking background videos...")
!find {DRIVE_BASE_PATH}/renders -maxdepth 1 -name "*.mp4" -exec ln -sf '{}' public/renders/ ';' 2>/dev/null
v_count = !ls public/renders/*.mp4 | wc -l
print(f"✅ Linked {v_count[0]} background videos.")

print("Linking fonts...")
# Try both the direct fonts folder and a recursive search
if os.path.exists(f"{DRIVE_BASE_PATH}/fonts"):
    !ln -sf {DRIVE_BASE_PATH}/fonts/* public/fonts/ 2>/dev/null
# Direct recursive search for all supported font files in the base Drive path to be thorough
!find {DRIVE_BASE_PATH} -maxdepth 4 -type f \( -iname "*.ttf" -o -iname "*.otf" -o -iname "*.woff" -o -iname "*.woff2" \) -exec ln -sf '{}' public/fonts/ ';' 2>/dev/null

f_count = !ls public/fonts/ | wc -l
print(f"✅ Linked {f_count[0]} fonts into public/fonts/")

print("✅ Drive assets linked to public folder.")

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
    --user-data-dir="{USER_DATA_DIR}"

print_banner("🏁 PROCESS FINISHED")
if os.path.exists(OUTPUT_JSON):
    print(f"✅ Master manifest saved to: {OUTPUT_JSON}")
else:
    print(f"❌ ERROR: Output JSON was not created.")
```
