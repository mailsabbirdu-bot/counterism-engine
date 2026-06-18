# 🚀 Counterism Studio V4 FPS & Timestamp Master Tool

Run this cell in Google Colab to automate FPS calculation and word-level timestamp generation.

```python
# ==============================================================================
# COUNTERISM STUDIO V4 — FPS & WHISPERX TIMESTAMP MASTER
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

# 2. Setup & Environment Cleanup
print_banner("🧹 CLEANING ENVIRONMENT")
site_pkgs = "/usr/local/lib/python3.12/dist-packages"
if os.path.exists(site_pkgs):
    cleaned = False
    for d in os.listdir(site_pkgs):
        if d.startswith("~"):
            print(f"🗑️ Removing invalid distribution: {d}")
            shutil.rmtree(os.path.join(site_pkgs, d), ignore_errors=True)
            cleaned = True
    if not cleaned: print("✅ No invalid distributions found.")

print_banner("📂 MOUNTING GOOGLE DRIVE")
if not os.path.exists("/content/drive"):
    drive.mount('/content/drive')
else:
    print("✅ Google Drive already mounted.")

print_banner("🛠️ INSTALLING DEPENDENCIES")

def is_installed(package):
    try:
        subprocess.check_output([sys.executable, "-m", "pip", "show", package])
        return True
    except:
        return False

# 1. Force stable CPU-only torch and specific transformers/accelerate stack
print("🎬 Setting up stable CPU environment...")
# Pinning to a very stable combination for WhisperX + Colab CPU
!pip install --quiet --no-cache-dir torch==2.4.0+cpu torchvision==0.19.0+cpu torchaudio==2.4.0+cpu --index-url https://download.pytorch.org/whl/cpu
!pip install --quiet --no-cache-dir transformers==4.44.2 accelerate==0.33.0

print("🎬 Checking FFmpeg...")
if subprocess.run(["which", "ffmpeg"], capture_output=True).returncode != 0:
    print("📥 Installing FFmpeg...")
    !apt-get update -y && apt-get install -y ffmpeg
else:
    print("✅ FFmpeg is already installed.")

print("🎙️ Checking WhisperX...")
if not is_installed("whisperx"):
    print("📥 Installing WhisperX from source...")
    # Using --no-deps to prevent it from pulling in unwanted torch/transformers versions
    !pip install --quiet git+https://github.com/m-bain/whisperX.git --no-deps
    # Manually install required deps to keep environment stable
    !pip install --quiet faster-whisper ctranslate2>=4.4.0 nltk pandas soundfile pyannote.audio>=3.1.1
    print("✅ WhisperX installed.")
else:
    print("✅ WhisperX environment verified.")

import whisperx

# 3. Define Processor Logic
class VideoProcessor:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.renders_dir = os.path.join(base_dir, "renders")
        self.manifests_dir = os.path.join(base_dir, "manifests")
        self.audio_dir = os.path.join(base_dir, "audio")

        # Ensure directories exist
        os.makedirs(self.manifests_dir, exist_ok=True)

    def _get_ffprobe_info(self, video_path: str) -> dict:
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate,avg_frame_rate,nb_frames,duration",
            "-of", "json",
            video_path
        ]
        output = subprocess.check_output(cmd).decode("utf-8")
        data = json.loads(output)
        if not data.get('streams'):
            return {}
        return data['streams'][0]

    def _detect_language_from_text(self, text: str) -> str:
        if not text: return None
        if any(ord(c) >= 0x0980 and ord(c) <= 0x09FF for c in text):
            return "bn"
        return "en"

    def task1_fps_update(self):
        print_banner("🚀 Starting Task 1: FPS and Frame Count Calculation")
        if not os.path.exists(self.renders_dir):
            print(f"⚠️ Renders directory not found at {self.renders_dir}")
            return

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

            result_line = f"{filename} | Original FPS: {fps:.3f} | Total Frames: {total_frames} | 30fps Frames: {frames_at_30fps}"
            results.append(result_line)
            print(f"✅ Processed {filename} -> {frames_at_30fps} frames @ 30fps")

        output_file = os.path.join(self.manifests_dir, "fps_update.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(results))
        print(f"\n📂 Results saved to {output_file}")

    def task2_timestamps(self):
        print_banner("🎙️ Starting Task 2: Word-level Timestamps using WhisperX")

        story_file = os.path.join(self.audio_dir, "story.txt")
        if not os.path.exists(story_file):
            print(f"⚠️ Story file not found at {story_file}")
            return

        with open(story_file, "r", encoding="utf-8") as f:
            story_content = f.read()

        scenes_text = re.split(r'দৃশ্য\s+[0-9০-৯]+', story_content)
        scenes_text = [s.strip() for s in scenes_text if s.strip()]
        print(f"📖 Loaded {len(scenes_text)} scenes from story.txt")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        batch_size = 16
        compute_type = "float16" if device == "cuda" else "int8"
        print(f"🖥️ Using device: {device} ({compute_type})")

        model = whisperx.load_model("large-v3", device, compute_type=compute_type)

        all_timestamps = []
        video_files = sorted([f for f in os.listdir(self.renders_dir) if f.startswith("scene_SC_") and f.endswith(".mp4")])

        for i, filename in enumerate(video_files):
            video_path = os.path.join(self.renders_dir, filename)
            scene_text = scenes_text[i] if i < len(scenes_text) else None

            print(f"\n🔍 Processing timestamps for {filename}...")
            detected_lang = self._detect_language_from_text(scene_text)
            if detected_lang: print(f"📝 Language (from script): {detected_lang}")

            audio = whisperx.load_audio(video_path)
            transcribe_args = {"batch_size": batch_size}
            if detected_lang: transcribe_args["language"] = detected_lang

            result = model.transcribe(audio, **transcribe_args)
            language_code = result["language"]
            print(f"🌍 Aligning language: {language_code}")
            try:
                model_a, metadata = whisperx.load_align_model(language_code=language_code, device=device)
                result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
            except Exception as e:
                print(f"⚠️ Alignment failed for {language_code}: {e}. Proceeding with transcription segments.")

            scene_label = f"SCENE_{i+1:02d}"
            for segment in result["segments"]:
                if "words" in segment:
                    for word_info in segment["words"]:
                        if "start" in word_info and "end" in word_info:
                            start_frame = int(round(word_info["start"] * 30))
                            end_frame = int(round(word_info["end"] * 30))
                            all_timestamps.append(f"{scene_label}: [{start_frame} - {end_frame}] \"{word_info['word']}\"")
                else:
                    start_frame = int(round(segment["start"] * 30))
                    end_frame = int(round(segment["end"] * 30))
                    all_timestamps.append(f"{scene_label}: [{start_frame} - {end_frame}] \"{segment['text'].strip()}\"")
            print(f"✅ Timestamps generated for {filename}")

        output_file = os.path.join(self.manifests_dir, "timestamp.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(all_timestamps))
        print(f"\n📂 Timestamps saved to {output_file}")

# 4. Execution
processor = VideoProcessor(DRIVE_BASE_PATH)
processor.task1_fps_update()
processor.task2_timestamps()

print_banner("🏁 ALL PROCESSES FINISHED")
fps_file = os.path.join(DRIVE_BASE_PATH, "manifests/fps_update.txt")
ts_file = os.path.join(DRIVE_BASE_PATH, "manifests/timestamp.txt")
if os.path.exists(fps_file): print(f"✅ FPS Manifest: {fps_file}")
if os.path.exists(ts_file): print(f"✅ Timestamp Manifest: {ts_file}")
print("\n✨ Process completed successfully.")
```
