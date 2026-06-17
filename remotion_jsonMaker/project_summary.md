# 🚀 Counterism Studio V4: JSON Maker & Rendering Pipeline

This project is a high-precision, automated video generation engine that transforms narrative stories into professional-grade cinematic documentaries using **Remotion** and **Gemini AI**.

---

## 🏗️ Architecture Overview

The system consists of three main stages: **Semantic Analysis**, **Manifest Generation**, and **Cinematic Rendering**.

### 1. Semantic Analysis & Timing
The engine first parses the `story.txt` file (located in Google Drive).
- **Word-Level Timestamping**: `generator.py` uses Gemini to estimate the precise frame boundaries for every word in the voiceover, mapped to a **30fps** target.
- **Duration Probing**: The engine uses `ffprobe` to detect the exact length of background video assets (`renders/scene_SC_##.mp4`) and forces the scene duration to match perfectly (`duration_sec * 30`).

### 2. Manifest Generation (`remotion_jsonMaker`)
This stage uses browser automation (Playwright) to interact with Gemini and create the `remotion_render.json` blueprint.
- **Slot-Based Layout Engine**: To ensure a "well-planned" professional look, the engine defines 7 safe **Layout Slots**:
  - `TOP_LEFT`, `TOP_RIGHT`, `BOTTOM_LEFT`, `BOTTOM_RIGHT`, `CENTER_FOCAL`, `MID_LEFT`, `MID_RIGHT`.
  - The AI is instructed to balance elements (e.g., if a Chart is in `TOP_RIGHT`, Text should be in `BOTTOM_LEFT`).
- **Collision Nudging & Safety**: A post-processing step (`finalize_json_durations`) implements **AABB Bounding Box detection**. If two overlays occupy the same time and space, the engine "nudges" them apart. Finally, it clamps all elements within a **150px safety margin** of the 1920x1080 canvas.
- **Local SFX Mapping**: The engine no longer downloads random sounds. It scans your Drive (`renders/audios`) for `in_X.mp3` and `out_X.mp3` files. These are assigned uniquely to every layer's entrance and exit animation.

### 3. Cinematic Rendering (Remotion)
The final stage renders the video frames.
- **Screen Safety**: `TextEngine.tsx` enforces a `maxWidth` and text-wrapping to prevent bleed.
- **Smooth Animations**: High-fidelity Bezier curves are used for all camera work and layer transitions.

---

## 📂 File Naming Conventions

- **Background Videos**: `renders/scene_SC_01.mp4`, `renders/scene_SC_02.mp4`...
- **Transition SFX**:
  - Entrance: `in_1.mp3`, `in_2.mp3`...
  - Exit: `out_1.mp3`, `out_2.mp3`...
- **Story Source**: `audio/story.txt`
- **Output Blueprint**: `manifests/remotion_render.json`

---

## 🚀 Usage in Google Colab

1. **Manifest Generation**: Use `remotion_jsonMaker/colab.md`. This will create the JSON manifest and the `timestamp.txt` in your Drive.
2. **Video Rendering**: Use the root `colab.md`. This will render the final video scenes based on the generated manifest.

*Note: Ensure your Drive assets are correctly named and placed before running the generation.*
