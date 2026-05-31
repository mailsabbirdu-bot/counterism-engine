# 🤖 Counterism Studio V4 JSON Maker (Local LLM Edition)

Run this cell in Google Colab to generate your `remotion_render.json` using a **local 1.5B model**. This is completely free, runs on CPU, and has no usage limits.

```python
# ==============================================================================
# COUNTERISM STUDIO V4 — LOCAL AI JSON MASTER GENERATOR
# ==============================================================================

import os
from google.colab import drive

def print_banner(text):
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80)

# 1. Configuration
PROJECT_NAME = "counterism-engine"
DRIVE_BASE_PATH = "/content/drive/MyDrive/Counterism_Studio_V4"
MANIFEST_DIR = f"{DRIVE_BASE_PATH}/manifests"
OUTPUT_JSON = f"{MANIFEST_DIR}/remotion_render.json"
# Qwen 2.5 1.5B is non-gated and highly efficient on CPU
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

# 2. Setup
print_banner("📂 MOUNTING GOOGLE DRIVE")
drive.mount('/content/drive')

if not os.path.exists(PROJECT_NAME):
    print("🚀 Cloning engine...")
    !git clone https://github.com/mailsabbirdu-bot/counterism-engine
%cd {PROJECT_NAME}/remotion_jsonMaker

print_banner("🛠️ INSTALLING LOCAL LLM STACK")
# We use a lightweight stack optimized for CPU inference
!pip install -r requirements.txt

# 3. Story Source Verification
print_banner("📝 STORY SOURCE VERIFICATION")
STORY_FILE = f"{DRIVE_BASE_PATH}/manifests/guideline_prompt.txt"

if os.path.exists(STORY_FILE):
    print(f"✅ Found story file at: {STORY_FILE}")
else:
    print(f"❌ FATAL: Story file NOT FOUND: {STORY_FILE}")
    print("Please ensure your story is written in 'guideline_prompt.txt' inside the manifests folder.")

# 4. HuggingFace Authentication (Optional but recommended for speed)
try:
    from google.colab import userdata
    hf_token = userdata.get('HF_TOKEN')
except:
    hf_token = ""

# 5. Generate Master JSON
print_banner("🧠 LOCAL AI INFERENCE (CPU)")
print("🚀 This process typically takes 2-5 minutes on a standard Colab CPU.")
print("⏳ Truncating context to 6000 chars to ensure stability...")
# Loading and inference will happen locally on the Colab instance
!python generator.py --story-file="{STORY_FILE}" --model="{MODEL_ID}" --output="{OUTPUT_JSON}" --hf-token="{hf_token}"

print_banner("🏁 MASTER JSON READY")
print(f"Your master manifest has been saved to: {OUTPUT_JSON}")
print("You can now run the rendering pipeline to generate the video.")
```
