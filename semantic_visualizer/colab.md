# 🎬 Semantic Visualization Engine (Directorial Brain)

Run this cell in Google Colab to convert your Semantic Model and Knowledge Graph into a cinematic visualization blueprint.

```python
# ==============================================================================
# SEMANTIC VISUALIZER — CINEMATIC PLANNING PIPELINE
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
MODEL_FILE = f"{DRIVE_BASE_PATH}/analysis/semantic/semantic_model.json"
GRAPH_FILE = f"{DRIVE_BASE_PATH}/analysis/semantic/knowledge_graph.json"
OUTPUT_DIR = f"{DRIVE_BASE_PATH}/analysis/semantic"
PROJECT_NAME = "counterism-engine"

%cd /content
if not os.path.exists(PROJECT_NAME):
    !git clone https://github.com/mailsabbirdu-bot/counterism-engine
%cd {PROJECT_NAME}

# --- 3. RUN VISUALIZER ---
print("🧠 Initializing Semantic Visualizer...")
sys.path.append(os.getcwd())

if os.path.exists(MODEL_FILE) and os.path.exists(GRAPH_FILE):
    print(f"📄 Processing model: {MODEL_FILE}")
    print(f"📄 Processing graph: {GRAPH_FILE}")

    output_plan = f"{OUTPUT_DIR}/visualization_plan.json"

    !PYTHONPATH=. python3 semantic_visualizer/main.py \
        --model {MODEL_FILE} \
        --graph {GRAPH_FILE} \
        --output {output_plan}

    print(f"\n✨ SUCCESS! Directorial blueprint generated.")
    print(f"📍 Visualization Plan saved to: {output_plan}")
else:
    if not os.path.exists(MODEL_FILE): print(f"❌ ERROR: Semantic model not found at {MODEL_FILE}")
    if not os.path.exists(GRAPH_FILE): print(f"❌ ERROR: Knowledge graph not found at {GRAPH_FILE}")
    print("Please run the Semantic Understanding Engine (NLP) cell first.")
```
