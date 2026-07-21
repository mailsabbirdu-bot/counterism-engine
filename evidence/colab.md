# 🔬 Google Colab Documentary Evidence Automation

This Markdown document provides a clean, single-cell runner blueprint for Google Colab to automate historical evidence searching, screenshotting, matching, cropping, and stitching.

## Colab Execution Steps

Create a new cell in your Colab notebook and run the following code to mount Google Drive, install all playwright, pillow, and NLP dependencies, and generate evidence images of online newspaper pages and historical sources matching your story.

```python
# ==============================================================================
# DOCUMENTARY EVIDENCE SCENE CROP & STITCH PIPELINE
# ==============================================================================

import os
import subprocess

def print_banner(title):
    print("\n" + "="*80)
    print(f" 📂 {title}")
    print("="*80)

# --- 1. MOUNT GOOGLE DRIVE ---
print_banner("MOUNTING GOOGLE DRIVE")
from google.colab import drive
drive.mount('/content/drive')

# --- 2. CLONE REPOSITORY ---
print_banner("CLONING DOCUMENTARY ENGINE")
PROJECT_NAME = "counterism-engine"
%cd /content
if not os.path.exists(PROJECT_NAME):
    !git clone https://github.com/mailsabbirdu-bot/counterism-engine
%cd {PROJECT_NAME}

# --- 3. INSTALL PYTHON SYSTEM DEPENDENCIES ---
print_banner("INSTALLING PYTHON SYSTEM DEPENDENCIES")
# Install Playwright, Sentence-Transformers, RapidFuzz and SerpAPI
!pip install -q playwright sentence-transformers rapidfuzz google-search-results Pillow httpx numpy
!playwright install chromium --with-deps --silent

# --- 4. EXECUTE EVIDENCE CAPTURE ENGINE ---
print_banner("STARTING EVIDENCE ACQUISITION SEQUENCE")
# Run main.py which automatically reads story.txt from GDrive, segment scenes,
# captures web page regions matching narrations and stitches headers.
!python3 evidence/main.py

print_banner("COMPLETED EVIDENCE EXTRACITON PIPELINE")
print("✨ Photos and documentary evidence saved directly to: ")
print("📍 /content/drive/MyDrive/Counterism_Studio_V4/renders/overlays/evidence/photos/")
```
