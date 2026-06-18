# 🚀 Counterism Studio V4 FPS & Timestamp Master Tool

Run this cell in Google Colab to automate FPS calculation and word-level timestamp generation.

```python
# ==============================================================================
# COUNTERISM STUDIO V4 — FPS & STABLE-WHISPER TIMESTAMP MASTER
# ==============================================================================

import os
import sys
import json
import subprocess
import argparse
import re
import torch
import shutil
from google.colab import drive

def print_banner(text):
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80)

# 1. Configuration
DRIVE_BASE_PATH = "/content/drive/MyDrive/Counterism_Studio_V4"

# 2. Setup
print_banner("📂 MOUNTING GOOGLE DRIVE")
if not os.path.exists("/content/drive"):
    drive.mount('/content/drive')
else:
    print("✅ Google Drive already mounted.")

print_banner("🛠️ INSTALLING DEPENDENCIES")

# Optimized installation for Colab default environment
# We install stable-ts which is much more robust than whisperx for this environment
print("🎬 Installing Stable Whisper and requirements...")
!pip install --quiet stable-ts

print("🎬 Checking FFmpeg...")
if subprocess.run(["which", "ffmpeg"], capture_output=True).returncode != 0:
    print("📥 Installing FFmpeg...")
    !apt-get update -y && apt-get install -y ffmpeg
else:
    print("✅ FFmpeg is already installed.")

import stable_whisper

# 3. Define Processor Logic
class VideoProcessor:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.renders_dir = os.path.join(base_dir, "renders")
        self.manifests_dir = os.path.join(base_dir, "manifests")
        self.audio_dir = os.path.join(base_dir, "audio")
        os.makedirs(self.manifests_dir, exist_ok=True)

    def _get_ffprobe_info(self, video_path: str) -> dict:
        cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate,avg_frame_rate,nb_frames,duration", "-of", "json", video_path]
        try:
            output = subprocess.check_output(cmd).decode("utf-8")
            data = json.loads(output)
            return data['streams'][0] if data.get('streams') else {}
        except: return {}

    def _detect_language_from_text(self, text: str) -> str:
        if not text: return None
        if any(ord(c) >= 0x0980 and ord(c) <= 0x09FF for c in text): return "bn"
        return "en"

    def task1_fps_update(self):
        print_banner("🚀 Task 1: FPS & Frame Count Calculation")
        if not os.path.exists(self.renders_dir):
            print(f"⚠️ Renders directory not found at {self.renders_dir}"); return

        results = []
        video_files = sorted([f for f in os.listdir(self.renders_dir) if f.startswith("scene_SC_") and f.endswith(".mp4")])

        for filename in video_files:
            video_path = os.path.join(self.renders_dir, filename)
            info = self._get_ffprobe_info(video_path)
            if not info: continue

            duration = float(info.get("duration", 0))
            fps_str = info.get("avg_frame_rate", "0/1")
            num, den = map(int, fps_str.split("/"))
            fps = num / den if den else 0

            nb_frames = info.get("nb_frames")
            total_frames = int(nb_frames) if nb_frames is not None and nb_frames != "N/A" else int(round(duration * fps))
            frames_at_30fps = int(round(duration * 30))

            results.append(f"{filename} | Original FPS: {fps:.3f} | Total Frames: {total_frames} | 30fps Frames: {frames_at_30fps}")
            print(f"✅ {filename}: {total_frames}f -> {frames_at_30fps}f (@30fps)")

        output_file = os.path.join(self.manifests_dir, "fps_update.txt")
        with open(output_file, "w", encoding="utf-8") as f: f.write("\n".join(results))
        print(f"\n📂 Saved to {output_file}")

    def task2_timestamps(self):
        print_banner("🎙️ Task 2: Word-level Timestamps (Stable Whisper)")
        story_file = os.path.join(self.audio_dir, "story.txt")
        if not os.path.exists(story_file):
            print(f"⚠️ Story file not found at {story_file}"); return

        with open(story_file, "r", encoding="utf-8") as f: story_content = f.read()
        scenes_text = [s.strip() for s in re.split(r'দৃশ্য\s+[0-9০-৯]+', story_content) if s.strip()]
        print(f"📖 Loaded {len(scenes_text)} scenes.")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🖥️ Device: {device}")
        model = stable_whisper.load_model("large-v3", device=device)

        all_timestamps = []
        video_files = sorted([f for f in os.listdir(self.renders_dir) if f.startswith("scene_SC_") and f.endswith(".mp4")])

        for i, filename in enumerate(video_files):
            video_path = os.path.join(self.renders_dir, filename)
            scene_text = scenes_text[i] if i < len(scenes_text) else None
            print(f"\n🔍 Processing {filename}...")
            lang = self._detect_language_from_text(scene_text)
            if lang: print(f"📝 Language: {lang}")

            result = model.transcribe(video_path, language=lang, regroup=True)
            scene_label = f"SCENE_{i+1:02d}"
            for segment in result.segments:
                for word in segment.words:
                    s_f, e_f = int(round(word.start * 30)), int(round(word.end * 30))
                    all_timestamps.append(f"{scene_label}: [{s_f} - {e_f}] \"{word.word.strip()}\"")
            print(f"✅ Done {filename}")

        output_file = os.path.join(self.manifests_dir, "timestamp.txt")
        with open(output_file, "w", encoding="utf-8") as f: f.write("\n".join(all_timestamps))
        print(f"\n📂 Saved to {output_file}")

# 4. Execution
processor = VideoProcessor(DRIVE_BASE_PATH)
processor.task1_fps_update()
processor.task2_timestamps()

print_banner("🏁 ALL PROCESSES FINISHED")
fps_file = os.path.join(DRIVE_BASE_PATH, "manifests/fps_update.txt")
ts_file = os.path.join(DRIVE_BASE_PATH, "manifests/timestamp.txt")
if os.path.exists(fps_file): print(f"✅ FPS Manifest: {fps_file}")
if os.path.exists(ts_file): print(f"✅ Timestamp Manifest: {ts_file}")
print("\n✨ Success.")
```
