# 🧠 Unified Cinematic Knowledge System

Extract structured meaning and generate cinematic visualization blueprints from your narration script in a single step using the manual Gemini NLP loop. This cell mounts Google Drive, installs all lightweight dependencies, and processes your `story.txt`.

```python
# ==============================================================================
# KNOWLEDGE SYSTEM — SEMANTIC TO CINEMATIC PIPELINE
# ==============================================================================

import os
import json
import sys

# --- 1. MOUNT GOOGLE DRIVE ---
print("📂 Mounting Google Drive...")
from google.colab import drive
drive.mount('/content/drive')

# --- 2. CONFIGURATION ---
DRIVE_BASE_PATH = "/content/drive/MyDrive/Counterism_Studio_V4"
STORY_FILE = f"{DRIVE_BASE_PATH}/audio/story.txt"
OUTPUT_DIR = f"{DRIVE_BASE_PATH}/analysis/semantic"
PROJECT_NAME = "counterism-engine"

%cd /content
if not os.path.exists(PROJECT_NAME):
    !git clone https://github.com/mailsabbirdu-bot/counterism-engine
%cd {PROJECT_NAME}

# --- 3. INSTALL DEPENDENCIES ---
print("🛠️ Installing System Dependencies...")
!pip install -q networkx pydantic regex

# --- 4. RUN UNIFIED PIPELINE ---
print("🚀 Initializing Knowledge System...")
sys.path.append(os.getcwd())
from knowledge_system.main import KnowledgeSystemPipeline

if os.path.exists(STORY_FILE):
    with open(STORY_FILE, 'r', encoding='utf-8') as f:
        story_text = f.read()

    print(f"📄 Processing: {STORY_FILE}")
    pipeline = KnowledgeSystemPipeline()
    results = pipeline.run(story_text)

    # --- 5. SAVE RESULTS TO DRIVE ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # NLP Model (Sequential Scenes)
    with open(f"{OUTPUT_DIR}/semantic_model.json", 'w', encoding='utf-8') as f:
        json.dump(results["nlp"]["scenes"], f, indent=2, ensure_ascii=False)

    # Knowledge Graph
    with open(f"{OUTPUT_DIR}/knowledge_graph.json", 'w', encoding='utf-8') as f:
        json.dump(results["nlp"]["graph"], f, indent=2, ensure_ascii=False)

    # Directorial Visualization Plan
    with open(f"{OUTPUT_DIR}/visualization_plan.json", 'w', encoding='utf-8') as f:
        json.dump(results["plan"], f, indent=2, ensure_ascii=False)

    # Final Remotion Manifest
    with open(f"{OUTPUT_DIR}/remotion_render_crve.json", 'w', encoding='utf-8') as f:
        json.dump(results["manifest"], f, indent=2, ensure_ascii=False)

    print(f"\n✨ SUCCESS! Pipeline complete.")
    print(f"📍 Artifacts saved to: {OUTPUT_DIR}/")
    print(f"   - semantic_model.json")
    print(f"   - knowledge_graph.json")
    print(f"   - visualization_plan.json")
    print(f"   - remotion_render_crve.json (Final Manifest)")
else:
    print(f"❌ ERROR: Story file not found at {STORY_FILE}")
    print("Please ensure your script is named 'story.txt' and placed in the 'audio' folder of your project in Drive.")
```
