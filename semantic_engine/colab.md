# 🧠 Semantic Understanding Engine (Deterministic NLP)

Run this cell in Google Colab to extract structured knowledge from your scene narration (`story.txt`). This engine uses rule-based NLP and does not require AI/LLMs.

```python
# ==============================================================================
# SEMANTIC ENGINE — STANDALONE NLP PIPELINE
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
print("🛠️ Installing NLP dependencies...")
!pip install -q stanza networkx pydantic regex
import stanza
print("Downloading NLP models (English & Bangla)...")
stanza.download('en', verbose=False)
stanza.download('bn', verbose=False)

# --- 4. PROCESS NARRATION ---
print("🧠 Initializing Semantic Engine...")
sys.path.append(os.getcwd())
from semantic_engine.main import SemanticEngine

if os.path.exists(STORY_FILE):
    with open(STORY_FILE, 'r', encoding='utf-8') as f:
        story_text = f.read()

    print(f"📄 Processing: {STORY_FILE}")
    engine = SemanticEngine()
    result = engine.process(story_text)

    # --- 5. SAVE RESULTS TO DRIVE ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Save Model
    model_path = f"{OUTPUT_DIR}/semantic_model.json"
    with open(model_path, 'w', encoding='utf-8') as f:
        json.dump(result['model'], f, indent=2, ensure_ascii=False)

    # Save Knowledge Graph
    graph_path = f"{OUTPUT_DIR}/knowledge_graph.json"
    with open(graph_path, 'w', encoding='utf-8') as f:
        json.dump(result['graph'], f, indent=2, ensure_ascii=False)

    print(f"\n✅ SUCCESS! Semantic analysis complete.")
    print(f"📍 Model saved to: {model_path}")
    print(f"📍 Graph saved to: {graph_path}")
else:
    print(f"❌ ERROR: Story file not found at {STORY_FILE}")
    print("Please ensure your script is named 'story.txt' and placed in the 'audio' folder of your project in Drive.")
```
