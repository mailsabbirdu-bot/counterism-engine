# 🎵 Counterism Studio V4 Audio System

This document describes how the automated sound effects (SFX) and synchronization system works in Counterism Studio V4.

## 🧠 How it Works

The audio system operates in a 4-stage pipeline orchestrated by `remotion_jsonMaker/audio_generator.py`:

1.  **Analysis:** The engine reads `story.txt` and `timestamp.txt` to identify semantic cues (e.g., "digital transformation", "sudden drop") and visual cues (UI entrances, chart transitions).
2.  **Orchestration:** Using Gemini, the engine decides which sound effects are appropriate for each scene and precisely when they should start and end based on the frame-accurate timestamps.
3.  **Acquisition:** The engine generates specific search queries and uses `yt-dlp` to download the most relevant non-copyright sound effects from YouTube directly to the `Counterism_Studio_V4/renders/audios` folder on Google Drive.
4.  **Synchronization:** A `timestamp_audio.txt` manifest is generated, mapping every downloaded file to its specific scene, start frame, end frame, and volume level.

## 🎬 Remotion Integration

During the rendering process, the Remotion project:
- Loads the `timestamp_audio.txt` manifest from the public directory.
- For each scene, it filters the relevant SFX.
- Renders native `<Audio />` components with precise timing using the `startInVideo` and `durationInFrames` props.

## 🔊 Audio Sources & Licensing

- **Sources:** Dynamically sourced from YouTube (optimized for non-copyright/royalty-free results).
- **Background Music:** Sourced from the `audio/` folder in the Google Drive project root (manual selection).
- **Voiceover:** Sourced from the `audio/` folder (AI-generated or manual).
- **SFX:** Procedurally sourced and placed based on story context.

## 🛠️ Usage

The entire video production pipeline (Manifest Generation -> SFX Orchestration -> Video Rendering) is unified in a single Colab cell.

**Entry Point:** `remotion_jsonMaker/colab.md`

1.  **Mount Drive:** Accesses story, renders, and fonts.
2.  **Dependencies:** Installs Playwright, `yt-dlp`, Node.js, and FFmpeg.
3.  **JSON Maker:** Generates the master Remotion manifest using Gemini.
4.  **Audio Generator:** Analyzes the manifest, downloads SFX, and creates the audio timestamp mapping.
5.  **Remotion Renderer:** Executes the multi-scene render and syncs the final `.mp4` files back to Google Drive.
