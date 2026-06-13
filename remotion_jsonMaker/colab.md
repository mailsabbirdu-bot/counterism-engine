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
PROJECT_NAME = "counterism-engine"

# Input/Output Drive Path: /content/drive/MyDrive/Counterism_Studio_V4/
DRIVE_BASE_PATH = "/content/drive/MyDrive/Counterism_Studio_V4"
STORY_FILE = f"{DRIVE_BASE_PATH}/audio/story.txt"

# Manifest and Prompt Output Path: /content/drive/MyDrive/Counterism_Studio_V4/manifests/
OUTPUT_JSON = f"{DRIVE_BASE_PATH}/manifests/remotion_render.json"
PROMPT_FILE = f"{DRIVE_BASE_PATH}/manifests/remotion_prompt.txt"

# Path for persistent browser session (optional)
# This can still be kept in a separate folder or same base
USER_DATA_DIR = f"{DRIVE_BASE_PATH}/browser_session"

# 2. Setup
print_banner("📂 MOUNTING GOOGLE DRIVE")
drive.mount('/content/drive')

# Ensure we are in the right base directory
%cd /content

if not os.path.exists(PROJECT_NAME):
    print("🚀 Cloning engine...")
    !git clone https://github.com/mailsabbirdu-bot/counterism-engine
else:
    print("✅ Engine already cloned.")

%cd {PROJECT_NAME}/remotion_jsonMaker

print_banner("🛠️ INSTALLING PLAYWRIGHT STACK")
!pip install -r requirements.txt
!playwright install chromium
!playwright install-deps chromium

# 3. Context Verification
print_banner("📝 CONTEXT VERIFICATION")

if os.path.exists(STORY_FILE):
    print(f"✅ Found story file at: {STORY_FILE}")
else:
    print(f"❌ FATAL: Story file NOT FOUND: {STORY_FILE}")
    print(f"Please ensure your story and durations are in 'story.txt' inside: {DRIVE_BASE_PATH}/audio/")
    sys.exit("Input story file missing.")

# 4. Generate Master JSON
print_banner("🧠 GEMINI BROWSER AUTOMATION")
print("🚀 Using Playwright to interact with Gemini. This may take a few minutes.")

# We use xvfb-run to provide a virtual display for Playwright
# The command below correctly maps input and output paths as requested
# Using --user-data-dir allows you to reuse an authenticated session from your Drive
!xvfb-run python generator.py \
    --story-file="{STORY_FILE}" \
    --output="{OUTPUT_JSON}" \
    --prompt-output="{PROMPT_FILE}" \
    --drive-prompt="/content/counterism-engine/guideline_prompt.txt" \
    --user-data-dir="{USER_DATA_DIR}"

print_banner("🏁 PROCESS FINISHED")
if os.path.exists(OUTPUT_JSON):
    print(f"✅ Master manifest saved to: {OUTPUT_JSON}")
    print(f"📄 Full prompt saved to: {PROMPT_FILE}")
else:
    print(f"❌ ERROR: Output JSON was not created. Check the logs above.")
```
