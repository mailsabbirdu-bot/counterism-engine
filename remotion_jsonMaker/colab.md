# 🤖 Counterism Studio V4 JSON Maker (Playwright Gemini Edition)

Run this cell in Google Colab to generate your `remotion_render.json` using **Gemini** via browser automation.

**Note:** Gemini requires authentication. On Colab, you should first log in to your Google account in the browser. Since Colab instances are ephemeral, you might need to use a persistent `user_data_dir` on Google Drive to store your session.

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
DRIVE_BASE_PATH = "/content/drive/MyDrive/google audio"
# Fallback for different drive naming
if not os.path.exists(DRIVE_BASE_PATH):
    DRIVE_BASE_PATH = "/content/drive/MyDrive/google-audio"

MANIFEST_DIR = f"{DRIVE_BASE_PATH}/manifests"
OUTPUT_JSON = f"{MANIFEST_DIR}/remotion_render.json"
STORY_FILE = f"{MANIFEST_DIR}/guideline_prompt.txt"
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

# 3. Story Source Verification
print_banner("📝 STORY SOURCE VERIFICATION")

if os.path.exists(STORY_FILE):
    print(f"✅ Found story file at: {STORY_FILE}")
else:
    print(f"❌ FATAL: Story file NOT FOUND: {STORY_FILE}")
    print(f"Please ensure your story is written in 'guideline_prompt.txt' inside the manifests folder: {MANIFEST_DIR}")
    # Stop execution if story is missing
    sys.exit("Story file missing.")

# 4. Generate Master JSON
print_banner("🧠 GEMINI BROWSER AUTOMATION")
print("🚀 Using Playwright to interact with Gemini. This may take a few minutes.")

# We use xvfb-run to provide a virtual display for Playwright even in headless mode
# Add --user-data-dir="{USER_DATA_DIR}" to the command below if you have a saved session
!xvfb-run python generator.py --story-file="{STORY_FILE}" --output="{OUTPUT_JSON}" --drive-prompt="{STORY_FILE}"

print_banner("🏁 PROCESS FINISHED")
if os.path.exists(OUTPUT_JSON):
    print(f"✅ Master manifest saved to: {OUTPUT_JSON}")
else:
    print(f"❌ ERROR: Output JSON was not created. Check the logs above.")
```
