# 🚀 Counterism Studio V4: JSON Maker & Rendering Pipeline

This project is a high-precision, automated video generation engine that transforms narrative stories into professional-grade cinematic documentaries using **Remotion** and **Gemini AI**.

---

## 🏗️ Architecture Overview

The system consists of three main stages: **Semantic Analysis**, **Manifest Generation**, and **Cinematic Rendering**.

### 1. Semantic Analysis & Timing
The engine first parses the `story.txt` file (located in Google Drive).
- **Word-Level Timestamping**: `generator.py` uses Gemini to estimate the precise frame boundaries for every word in the voiceover, mapped to a **30fps** target.
- **Duration Probing**: The engine uses `ffprobe` to detect the exact length of background video assets (`renders/scene_SC_##.mp4`) and forces the scene duration to match perfectly.

### 2. Manifest Generation (`remotion_jsonMaker`)
This stage uses browser automation (Playwright) to interact with Gemini and create the `remotion_render.json` blueprint.
- **Professional Layout Engine**: The AI is instructed to use a **Balanced Quadrant Layout**. It places focal elements (like Nivo Charts and Text) in opposing corners to create visual harmony and professional spacing.
- **Collision Avoidance**: A post-processing step (`finalize_json_durations`) implements **AABB Bounding Box detection**. It calculates the spatial footprint of every overlay and "nudges" them apart if they overlap in time and space.
- **Canvas Safety**: All elements are clamped within a **150px safety margin** of the 1920x1080 canvas to ensure zero text bleed.
- **Local SFX Injection**: The engine scans the `renders/audios` folder for files named `in_X.mp3` and `out_X.mp3`. It automatically maps these to the entrance and exit frames of every visual layer to ensure unique, high-quality transitions.

### 3. Cinematic Rendering (Remotion)
The final stage bundles the assets and renders the video frames.
- **V4 Camera Engine**: A pivot-based 3D camera that tracks overlay IDs with smooth Bezier easing.
- **Robust Font Loading**: `Root.tsx` implements a multi-stage loader that detects local fonts on Google Drive and injects them into the browser context.
- **Optimized CPU Rendering**: All animations use native Remotion primitives (`interpolate`, `spring`) for maximum performance in Google Colab environments.

---

## 📂 File Naming Conventions

- **Background Videos**: `renders/scene_SC_01.mp4`, `renders/scene_SC_02.mp4`, etc.
- **Transition SFX**:
  - Entrance: `in_1.mp3`, `in_2.mp3`...
  - Exit: `out_1.mp3`, `out_2.mp3`...
- **Story Source**: `audio/story.txt`
- **Output Blueprint**: `manifests/remotion_render.json`

---

## 🚀 Usage in Google Colab

1. **Generation**: Run the code cell in `remotion_jsonMaker/colab.md` to create your manifest.
2. **Rendering**: Run the code cell in the root `colab.md` to produce the final MP4 files.

The system is designed to be **cache-agnostic** and **resilient**, automatically handling asset synchronization between Google Drive and the local environment.
