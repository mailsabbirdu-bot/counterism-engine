# 🤖 Counterism Studio V4 JSON Maker (One-Cell Solution)

Run this cell in Google Colab to generate your `remotion_render.json` automatically based on any story or topic.

```python
# ==============================================================================
# COUNTERISM STUDIO V4 — AI JSON MASTER GENERATOR
# ==============================================================================

import os
from google.colab import drive, userdata

def print_banner(text):
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80)

# 1. Configuration
PROJECT_NAME = "counterism-engine"
DRIVE_BASE_PATH = "/content/drive/MyDrive/Counterism_Studio_V4"
MANIFEST_DIR = f"{DRIVE_BASE_PATH}/manifests"
OUTPUT_JSON = f"{MANIFEST_DIR}/remotion_render.json"

# 2. Setup
print_banner("📂 MOUNTING GOOGLE DRIVE")
drive.mount('/content/drive')

if not os.path.exists(PROJECT_NAME):
    print("🚀 Cloning engine...")
    !git clone https://github.com/mailsabbirdu-bot/counterism-engine
%cd {PROJECT_NAME}/remotion_jsonMaker

print_banner("🛠️ INSTALLING AI DEPENDENCIES")
!pip install -r requirements.txt

# 3. Get User Inputs
print_banner("📝 CONTENT GENERATION")
# Note: You should have a GEMINI_API_KEY stored in Colab Secrets
try:
    api_key = userdata.get('GEMINI_API_KEY')
except:
    api_key = input("🔑 Enter your Gemini API Key: ")

story_prompt = input("\n🎬 Describe the story or topic for your video: \n> ")

# 4. Generate Master JSON
print_banner("🧠 AI GENERATION IN PROGRESS")
!python generator.py --story="{story_prompt}" --api-key="{api_key}" --output="{OUTPUT_JSON}"

print_banner("🏁 MASTER JSON READY")
print(f"Your master manifest has been saved to: {OUTPUT_JSON}")
print("You can now run the rendering pipeline to generate the video.")
```
