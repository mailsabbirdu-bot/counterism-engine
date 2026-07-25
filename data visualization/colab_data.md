# 🤖 Bklit UI Data Visualization Generator (Manual Gemini Edition)

Run this single-cell code block in Google Colab to generate your `data_visualization.json` using **Gemini** manually with guided prompts, sleek styling, and interactive copy-paste feedback.

```python
# ==============================================================================
# BKLIT UI DATA VISUALIZATION — GEMINI MANUAL MASTER GENERATOR
# ==============================================================================

import os
import sys
import shutil

def print_banner(text):
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80)

# 1. Configuration
PROJECT_PATH = "/content/engine"
DRIVE_BASE_PATH = "/content/drive/MyDrive/Counterism_Studio_V4"
OUTPUT_DIR = f"{DRIVE_BASE_PATH}/analysis/semantic"
OUTPUT_JSON = f"{OUTPUT_DIR}/data_visualization.json"

# Find story.txt from different possible locations on Google Drive
POSSIBLE_STORY_PATHS = [
    f"{DRIVE_BASE_PATH}/audio/story.txt",
    f"{DRIVE_BASE_PATH}/story.txt",
    "/content/story.txt"
]

# 2. Setup Google Drive
print_banner("📂 MOUNTING GOOGLE DRIVE")
try:
    from google.colab import drive
    drive.mount('/content/drive')
except Exception as e:
    print(f"⚠️ Drive mount skipped or failed: {e}")

# 3. Clone Repository
%cd /content
if not os.path.exists(PROJECT_PATH):
    print("🚀 Cloning engine...")
    !git clone https://github.com/mailsabbirdu-bot/counterism-engine {PROJECT_PATH}
else:
    print("✅ Engine already cloned.")

%cd {PROJECT_PATH}
# Fetch and checkout active feature branch containing the loop fixes
!git fetch origin && git checkout feature/evidence-asyncio-loop-fix || true

# 4. Locate story.txt
story_file = None
for path in POSSIBLE_STORY_PATHS:
    if os.path.exists(path):
        story_file = path
        break

if not story_file:
    print_banner("⚠️ STORY.TXT NOT FOUND ON DRIVE")
    print("Writing a default mock story.txt to continue...")
    default_story = (
        "Scene 1\n"
        "ঢাকা বাংলাদেশের রাজধানী এবং এটি একটি জনবহুল মেগাসিটি। অতিরিক্ত জনঘনত্বের কারণে ঢাকার জ্যাম তীব্র রূপ ধারণ করেছে।\n"
        "Scene 2\n"
        "১৯৭১ সালের ২৬ মার্চ প্রথম প্রহরে বঙ্গবন্ধু শেখ মুজিবুর রহমান বাংলাদেশের স্বাধীনতা ঘোষণা করেন।"
    )
    story_file = "/content/story.txt"
    with open(story_file, 'w', encoding='utf-8') as f:
        f.write(default_story)
else:
    print(f"✅ Found story.txt at: {story_file}")

# 5. Run the Manual Pipeline Interactive Generator
print_banner("🧠 DATA VISUALIZATION GENERATOR INTERACTION")

# Run the pipeline interactive loops using %run magic to cleanly handle spaces in folder path
%run "data visualization/generator.py" \
    --story-file="{story_file}" \
    --output="{OUTPUT_JSON}" \
    --public-dir="{PROJECT_PATH}/public" \
    --manual

print_banner("🏁 PROCESS FINISHED")
print(f"📍 data_visualization.json successfully generated and saved to:")
print(f"👉 {OUTPUT_JSON}")
```
