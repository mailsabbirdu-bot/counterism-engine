import os
import json
import subprocess
import argparse
import re
import whisperx
import torch
from typing import List, Dict, Any

class VideoProcessor:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.renders_dir = os.path.join(base_dir, "renders")
        self.manifests_dir = os.path.join(base_dir, "manifests")
        self.audio_dir = os.path.join(base_dir, "audio")

        # Ensure directories exist
        os.makedirs(self.manifests_dir, exist_ok=True)

    def _get_ffprobe_info(self, video_path: str) -> Dict[str, Any]:
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

    def task1_fps_update(self):
        print("🚀 Starting Task 1: FPS and Frame Count Calculation")
        if not os.path.exists(self.renders_dir):
            print(f"⚠️ Renders directory not found at {self.renders_dir}")
            return

        results = []
        video_files = sorted([f for f in os.listdir(self.renders_dir) if f.startswith("scene_SC_") and f.endswith(".mp4")])

        for filename in video_files:
            video_path = os.path.join(self.renders_dir, filename)
            info = self._get_ffprobe_info(video_path)
            if not info:
                continue

            duration = float(info.get("duration", 0))

            # Original FPS
            fps_str = info.get("avg_frame_rate", "0/1")
            num, den = map(int, fps_str.split("/"))
            fps = num / den if den else 0

            # Total frames
            nb_frames = info.get("nb_frames")
            if nb_frames is not None and nb_frames != "N/A":
                total_frames = int(nb_frames)
            else:
                total_frames = int(round(duration * fps))

            # Frames at 30 FPS
            frames_at_30fps = int(round(duration * 30))

            result_line = f"{filename} | Original FPS: {fps:.3f} | Total Frames: {total_frames} | 30fps Frames: {frames_at_30fps}"
            results.append(result_line)
            print(f"✅ Processed {filename}")

        output_file = os.path.join(self.manifests_dir, "fps_update.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(results))
        print(f"📂 Results saved to {output_file}")

    def task2_timestamps(self):
        print("🎙️ Starting Task 2: Word-level Timestamps using WhisperX")

        story_file = os.path.join(self.audio_dir, "story.txt")
        if not os.path.exists(story_file):
            print(f"⚠️ Story file not found at {story_file}")
            return

        with open(story_file, "r", encoding="utf-8") as f:
            story_content = f.read()

        # Split story into scenes
        scenes_text = re.split(r'দৃশ্য\s+[0-9০-৯]+', story_content)
        scenes_text = [s.strip() for s in scenes_text if s.strip()]

        device = "cuda" if torch.cuda.is_available() else "cpu"
        batch_size = 16 # adjust as needed
        compute_type = "float16" if device == "cuda" else "int8"

        print(f"🖥️ Using device: {device} ({compute_type})")

        # Load whisper model
        model = whisperx.load_model("large-v3", device, compute_type=compute_type)

        all_timestamps = []
        video_files = sorted([f for f in os.listdir(self.renders_dir) if f.startswith("scene_SC_") and f.endswith(".mp4")])

        for i, filename in enumerate(video_files):
            video_path = os.path.join(self.renders_dir, filename)
            print(f"🔍 Processing timestamps for {filename}...")

            # 1. Transcribe
            audio = whisperx.load_audio(video_path)
            result = model.transcribe(audio, batch_size=batch_size)

            # 2. Align
            # We try to detect language if not specified, but for Bangla/English mix,
            # whisperx alignment needs a model for that language.
            language_code = result["language"]
            try:
                model_a, metadata = whisperx.load_align_model(language_code=language_code, device=device)
                result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
            except Exception as e:
                print(f"⚠️ Alignment failed for {language_code}: {e}. Using transcription timestamps.")

            # 3. Process segments and words
            scene_label = f"SCENE_{i+1:02d}"
            for segment in result["segments"]:
                if "words" in segment:
                    for word_info in segment["words"]:
                        if "start" in word_info and "end" in word_info:
                            start_frame = int(round(word_info["start"] * 30))
                            end_frame = int(round(word_info["end"] * 30))
                            word = word_info["word"]
                            all_timestamps.append(f"{scene_label}: [{start_frame} - {end_frame}] \"{word}\"")
                else:
                    # Fallback if alignment didn't provide word-level
                    start_frame = int(round(segment["start"] * 30))
                    end_frame = int(round(segment["end"] * 30))
                    text = segment["text"].strip()
                    all_timestamps.append(f"{scene_label}: [{start_frame} - {end_frame}] \"{text}\"")

        output_file = os.path.join(self.manifests_dir, "timestamp.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(all_timestamps))
        print(f"📂 Timestamps saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Counterism Studio V4 Video Processor")
    parser.add_argument("--base-dir", default="/content/drive/MyDrive/Counterism_Studio_V4", help="Base directory in Google Drive")
    args = parser.parse_args()

    processor = VideoProcessor(args.base_dir)
    processor.task1_fps_update()
    processor.task2_timestamps()

if __name__ == "__main__":
    main()
