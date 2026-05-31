# 🤖 Counterism Studio V4 JSON Maker (Playwright Gemini Edition)

Run this cell in Google Colab to generate your `remotion_render.json` using **Gemini** via browser automation.

**Note:** Since Gemini requires authentication, you may need to provide a `user_data_dir` that contains an authenticated session, or run in non-headless mode locally to log in first. On Colab, you might need to handle login or use an API-based approach if session persistence is difficult.

```python
# ==============================================================================
# COUNTERISM STUDIO V4 — GEMINI BROWSER JSON MASTER GENERATOR
# ==============================================================================

import os
from google.colab import drive

def print_banner(text):
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80)

# 1. Configuration
PROJECT_NAME = "counterism-engine"
DRIVE_BASE_PATH = "/content/drive/MyDrive/google audio"
MANIFEST_DIR = f"{DRIVE_BASE_PATH}/manifests"
OUTPUT_JSON = f"{MANIFEST_DIR}/remotion_render.json"
# Path for persistent browser session (optional)
USER_DATA_DIR = f"{DRIVE_BASE_PATH}/browser_session"

# 2. Setup
print_banner("📂 MOUNTING GOOGLE DRIVE")
drive.mount('/content/drive')

if not os.path.exists(PROJECT_NAME):
    print("🚀 Cloning engine...")
    !git clone https://github.com/mailsabbirdu-bot/counterism-engine
%cd {PROJECT_NAME}/remotion_jsonMaker

print_banner("🛠️ INSTALLING PLAYWRIGHT STACK")
!pip install -r requirements.txt
!playwright install chromium
!playwright install-deps chromium

# 3. Story Source Verification
print_banner("📝 STORY SOURCE VERIFICATION")
STORY_FILE = f"{DRIVE_BASE_PATH}/manifests/guideline_prompt.txt"

if os.path.exists(STORY_FILE):
    print(f"✅ Found story file at: {STORY_FILE}")
else:
    print(f"❌ FATAL: Story file NOT FOUND: {STORY_FILE}")
    print(f"Please ensure your story is written in 'guideline_prompt.txt' inside the manifests folder: {STORY_FILE}")

# 4. Generate Master JSON
print_banner("🧠 GEMINI BROWSER AUTOMATION")
print("🚀 Using Playwright to interact with Gemini. This may take a few minutes.")
print("⏳ Stripping example JSON from guidelines to prevent model hallucination...")

# If you have an authenticated session, add: --user-data-dir="{USER_DATA_DIR}"
!python generator.py --story-file="{STORY_FILE}" --output="{OUTPUT_JSON}"

print_banner("🏁 MASTER JSON READY")
print(f"Your master manifest has been saved to: {OUTPUT_JSON}")
print("You can now run the rendering pipeline to generate the video.")
```
