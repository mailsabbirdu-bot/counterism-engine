import os
import json
import subprocess
import argparse
import re
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
        print("\n" + "="*80)
        print(" 🚀 Starting Task 1: FPS and Frame Count Calculation")
        print("="*80)
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
            fps_str = info.get("avg_frame_rate", "0/1")
            num, den = map(int, fps_str.split("/"))
            fps = num / den if den else 0

            nb_frames = info.get("nb_frames")
            if nb_frames is not None and nb_frames != "N/A":
                total_frames = int(nb_frames)
            else:
                total_frames = int(round(duration * fps))

            frames_at_30fps = int(round(duration * 30))

            result_line = f"{filename} | Original FPS: {fps:.3f} | Total Frames: {total_frames} | 30fps Frames: {frames_at_30fps}"
            results.append(result_line)
            print(f"✅ Processed {filename} -> {frames_at_30fps} frames @ 30fps")

        output_file = os.path.join(self.manifests_dir, "fps_update.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(results))
        print(f"\n📂 Results saved to {output_file}")

    def _detect_language_from_text(self, text: str) -> str:
        if not text:
            return None
        if any(ord(c) >= 0x0980 and ord(c) <= 0x09FF for c in text):
            return "bn"
        return "en"

    def task2_timestamps(self):
        print("\n" + "="*80)
        print(" 🎙️ Starting Task 2: Word-level Timestamps using Stable Whisper")
        print("="*80)

        import stable_whisper

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
        print(f"🖥️ Using device: {device}")

        # Load stable-whisper model
        model = stable_whisper.load_model("large-v3", device=device)

        all_timestamps = []
        video_files = sorted([f for f in os.listdir(self.renders_dir) if f.startswith("scene_SC_") and f.endswith(".mp4")])

        for i, filename in enumerate(video_files):
            video_path = os.path.join(self.renders_dir, filename)
            scene_text = scenes_text[i] if i < len(scenes_text) else None

            print(f"\n🔍 Processing timestamps for {filename}...")
            detected_lang = self._detect_language_from_text(scene_text)
            if detected_lang:
                print(f"📝 Language context: {detected_lang}")

            # Perform alignment with story.txt content for exact word matching
            # We use the ground truth text from story.txt and let whisper find the timings
            print(f"🎬 Aligning script with audio for {filename}...")

            # Use detected language to help alignment
            # Stable Whisper's align method works best when providing the exact script
            try:
                # We prioritize the provided script text for alignment
                if scene_text:
                    result = model.align(video_path, scene_text, language=detected_lang)
                else:
                    # Fallback to transcription if scene text is missing
                    result = model.transcribe(video_path, language=detected_lang, regroup=True)
            except Exception as e:
                print(f"⚠️ Alignment failed: {e}. Falling back to transcription.")
                result = model.transcribe(video_path, language=detected_lang, regroup=True)

            scene_label = f"SCENE_{i+1:02d}"
            for segment in result.segments:
                for word_info in segment.words:
                    s_sec, e_sec = word_info.start, word_info.end
                    s_f, e_f = int(round(s_sec * 30)), int(round(e_sec * 30))
                    word = word_info.word.strip()
                    # Format: SCENE_XX: [Original: 0.12s - 0.50s] -> [30fps: 4f - 15f] "Word"
                    all_timestamps.append(f"{scene_label}: [Original: {s_sec:.2f}s - {e_sec:.2f}s] -> [30fps: {s_f}f - {e_f}f] \"{word}\"")

            print(f"✅ Timestamps generated for {filename}")

        output_file = os.path.join(self.manifests_dir, "timestamp.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(all_timestamps))
        print(f"\n📂 Timestamps saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Counterism Studio V4 Video Processor")
    parser.add_argument("--base-dir", default="/content/drive/MyDrive/Counterism_Studio_V4", help="Base directory in Google Drive")
    args = parser.parse_args()

    processor = VideoProcessor(args.base_dir)
    processor.task1_fps_update()
    processor.task2_timestamps()

if __name__ == "__main__":
    main()
