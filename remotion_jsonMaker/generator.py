import os
import json
import argparse
import re
import time
import subprocess
from typing import Dict, Any
from playwright.sync_api import sync_playwright
import playwright_stealth

class RemotionJsonMaker:
    def __init__(self, user_data_dir: str = None, headless: bool = True):
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start_browser(self):
        """Initializes a persistent browser session."""
        if self.page: return

        self.playwright = sync_playwright().start()
        print("🚀 Launching persistent browser...")
        browser_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage"
        ]

        if self.user_data_dir:
            self.context = self.playwright.chromium.launch_persistent_context(
                self.user_data_dir,
                headless=self.headless,
                args=browser_args
            )
        else:
            self.browser = self.playwright.chromium.launch(headless=self.headless, args=browser_args)
            self.context = self.browser.new_context()

        self.page = self.context.new_page()
        playwright_stealth.Stealth().apply_stealth_sync(self.page)
        print("🌐 Navigating to Gemini...")
        self.page.goto("https://gemini.google.com/app", wait_until="networkidle", timeout=60000)

    def stop_browser(self):
        """Closes the browser session."""
        if self.context: self.context.close()
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()
        self.page = None

    def probe_video_duration_and_fps(self, video_path: str):
        """Probes a video file for its duration and FPS using ffprobe."""
        try:
            cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=duration,nb_frames,r_frame_rate",
                "-of", "json", video_path
            ]
            output = subprocess.check_output(cmd).decode("utf-8")
            data = json.loads(output)
            if not data.get('streams'):
                # Fallback for some formats
                cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", video_path]
                output = subprocess.check_output(cmd).decode("utf-8")
                data = json.loads(output)
                return float(data['format'].get('duration', 0)), 30.0

            stream = data['streams'][0]
            duration = float(stream.get('duration', 0))
            if duration == 0:
                # Try format duration
                cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", video_path]
                output = subprocess.check_output(cmd).decode("utf-8")
                data = json.loads(output)
                duration = float(data['format'].get('duration', 0))

            fps_str = stream.get('r_frame_rate', '30/1')
            if '/' in fps_str:
                num, den = map(float, fps_str.split('/'))
                fps = num / den if den != 0 else 30.0
            else:
                fps = float(fps_str)

            return duration, fps
        except Exception as e:
            print(f"⚠️ Warning: Could not probe video stats for {video_path}: {e}")
            return 0.0, 30.0

    def adjust_durations_in_text(self, text: str, public_dir: str = "../public") -> str:
        """
        Scans text for video_path and duration_in_frames and adjusts them if
        the source video FPS is not 30. Uses strict boundary checks to avoid scene mismatch.
        """

        def replacement_logic(match):
            block = match.group(0)
            vpath_match = re.search(r'"video_path":\s*"([^"]+)"', block)
            duration_match = re.search(r'"duration_in_frames"\s*:\s*(\d+)', block)

            if vpath_match:
                rel_vpath = vpath_match.group(1)
                abs_vpath = os.path.join(public_dir, rel_vpath)

                if os.path.exists(abs_vpath):
                    duration_sec, fps = self.probe_video_duration_and_fps(abs_vpath)

                    if duration_sec > 0:
                        # Most accurate way to target 30fps: use real-world duration in seconds
                        new_duration = int(round(duration_sec * 30))

                        if duration_match:
                            orig_duration = int(duration_match.group(1))
                            if new_duration != orig_duration:
                                print(f"⚖️ Adjusting {rel_vpath}: {duration_sec}s ({fps}fps source) -> {new_duration}f (30fps target)")
                                return re.sub(r'"duration_in_frames"\s*:\s*\d+', f'"duration_in_frames": {new_duration}', block)
                        else:
                            # If duration wasn't in this specific match block but video_path was,
                            # we might need to be careful, but the regex patterns below pair them.
                            pass

            return block

        # Pattern 1: video_path ... duration_in_frames
        pattern1 = r'("video_path":\s*"[^"]+"(?:(?!"video_path"|"duration_in_frames").){0,300}?"duration_in_frames"\s*:\s*\d+)'
        text = re.sub(pattern1, replacement_logic, text, flags=re.DOTALL)

        # Pattern 2: duration_in_frames ... video_path
        pattern2 = r'("duration_in_frames"\s*:\s*\d+(?:(?!"video_path"|"duration_in_frames").){0,300}?"video_path":\s*"[^"]+")'
        text = re.sub(pattern2, replacement_logic, text, flags=re.DOTALL)

        return text

    def get_local_fonts(self, public_dir: str = "../public") -> str:
        """Scans the public/fonts directory and returns available font names."""
        fonts_dir = os.path.join(public_dir, "fonts")
        potential_dirs = [fonts_dir, os.path.join(fonts_dir, "drive_fonts")]

        font_files = []
        for d in potential_dirs:
            if os.path.exists(d):
                for file in os.listdir(d):
                    if file.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
                        name = os.path.splitext(file)[0]
                        font_files.append(name)

        if not font_files:
            return "No local fonts detected."

        return ", ".join(sorted(list(set(font_files))))

    def load_guidelines(self, local_guideline_path: str, local_prompt_path: str, drive_prompt_path: str) -> str:
        guidelines = ""
        if os.path.exists(local_guideline_path):
            with open(local_guideline_path, 'r', encoding='utf-8') as f:
                guidelines += f"\n--- ENGINE SYSTEM GUIDELINES ---\n{f.read()}\n"
        if os.path.exists(local_prompt_path):
            with open(local_prompt_path, 'r', encoding='utf-8') as f:
                guidelines += f"\n--- TECHNICAL SCHEMA & COMPONENTS ---\n{f.read()}\n"
        if drive_prompt_path and os.path.exists(drive_prompt_path):
            with open(drive_prompt_path, 'r', encoding='utf-8') as f:
                guidelines += f"\n--- STORY AND DURATION SPECIFICATIONS (DRIVE) ---\n{f.read()}\n"
        return guidelines

    def finalize_json_durations(self, data: Dict[str, Any], public_dir: str = "../public") -> Dict[str, Any]:
        """Ensures frame-accurate duration and clamps overlay properties."""
        if not data or not data.get('scenes'):
            return data

        for scene in data['scenes']:
            scene_duration = scene.get('duration_in_frames', 150)
            if scene.get('background_type') == 'video' and scene.get('video_path'):
                vpath = scene['video_path']
                abs_vpath = os.path.join(public_dir, vpath)
                if os.path.exists(abs_vpath):
                    duration_sec, fps = self.probe_video_duration_and_fps(abs_vpath)
                    if duration_sec > 0:
                        target_fps = data.get('global_settings', {}).get('fps', 30)
                        scene_duration = int(round(duration_sec * target_fps))
                        print(f"🎯 Finalizing {vpath}: {duration_sec}s -> {scene_duration}f")
                        scene['duration_in_frames'] = scene_duration

            if scene.get('overlays'):
                for ov in scene['overlays']:
                    if ov.get('position'):
                        ov['position']['x'] = max(200, min(1720, ov['position'].get('x', 960)))
                        ov['position']['y'] = max(150, min(930, ov['position'].get('y', 540)))

                    if ov.get('start', 0) >= scene_duration:
                        ov['start'] = max(0, scene_duration - 60)

                    if ov.get('start', 0) + ov.get('duration', 0) > scene_duration:
                        ov['duration'] = scene_duration - ov.get('start', 0)

                    if ov.get('duration', 0) < 30:
                        ov['duration'] = 30
        return data

    def generate_word_timestamps(self, story: str, public_dir: str = "../public") -> str:
        """Parses story and estimates word-level timestamps."""
        print("🎙️  Generating word-level timestamps via Gemini...")
        scene_markers = re.findall(r'দৃশ্য\s+[0-9০-৯]+', story)
        scene_texts = re.split(r'দৃশ্য\s+[0-9০-৯]+', story)
        scene_texts = [s.strip() for s in scene_texts if s.strip()]

        full_ts_prompt = (
            "You are a Voiceover Alignment Assistant. Provide word-level timestamps in FRAMES for a 30fps project. Start every scene from frame 0.\n\n"
        )
        for i, scene_text in enumerate(scene_texts):
            scene_num = i + 1
            vpath = f"renders/scene_SC_{scene_num:02d}.mp4"
            abs_vpath = os.path.join(public_dir, vpath)
            duration_sec = 6.0
            if os.path.exists(abs_vpath):
                duration_sec, _ = self.probe_video_duration_and_fps(abs_vpath)

            full_ts_prompt += (
                f"--- SCENE {scene_num:02d} ({duration_sec}s / {int(round(duration_sec * 30))} frames) ---\n"
                f"TEXT: {scene_text}\n\n"
            )
        full_ts_prompt += "Format: SCENE_XX: [Frame X - Frame Y] Word1, ...\nReturn ONLY the timestamps."
        return self._interact_with_gemini(full_ts_prompt)

    def _interact_with_gemini(self, prompt: str, retry_count: int = 2) -> str:
        """Helper method for raw Gemini browser interaction with retry logic."""
        for attempt in range(retry_count + 1):
            self.start_browser()
            page = self.page
            try:
                input_selector = "div[contenteditable='true']"
                page.wait_for_selector(input_selector, timeout=45000)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

                print(f"⌨️  Sending prompt to Gemini (Attempt {attempt+1}/{retry_count+1})...")
                page.click(input_selector)
                page.fill(input_selector, prompt)
                time.sleep(1)
                page.keyboard.press("Enter")

                # Fallback Send button
                try:
                    send_button = "button[aria-label*='Send message'], button[aria-label*='Submit']"
                    if page.is_visible(send_button, timeout=2000):
                        page.click(send_button)
                except: pass

                print("⏳  Waiting for Gemini to finish generating...")
                response_selectors = ["message-content", ".markdown.message-content", ".model-response-text", "div[class*='model-response']", "[data-message-author-role='assistant']"]

                last_text = ""
                stable_count = 0
                for i in range(150):
                    time.sleep(2)
                    current_text = ""
                    found_msg = False
                    for sel in response_selectors:
                        msgs = page.query_selector_all(sel)
                        if msgs:
                            current_text = msgs[-1].inner_text()
                            found_msg = True
                            break

                    if found_msg and len(current_text) > 0:
                        if current_text == last_text:
                            stable_count += 1
                            if stable_count >= 4:
                                print(f"✅  Generation complete ({len(current_text)} characters).")
                                if len(current_text) > 100: return current_text
                                break
                        else:
                            stable_count = 0
                            last_text = current_text
                    elif i > 45: break

                print("🔄  Reloading for retry...")
                page.reload(wait_until="networkidle")
                time.sleep(5)
            except Exception as e:
                print(f"⚠️ Error: {e}")
                if attempt < retry_count: page.reload(wait_until="networkidle")
                else: return f"Error: {e}"
        return "Error: Failed to extract valid response."

    def generate(self, story: str, guidelines: str, prompt_output_path: str = None, timestamp_context: str = None) -> Dict[str, Any]:
        print("⚖️ Adjusting durations in prompt...")
        story = self.adjust_durations_in_text(story)
        guidelines = self.adjust_durations_in_text(guidelines)
        local_fonts = self.get_local_fonts()

        full_prompt = (
            "You are a world-class Motion Graphics Director. Generate an ULTRA MODERN cinematic JSON manifest.\n\n"
            "CRITICAL TIMING & CANVAS RULES:\n"
            "1. Each scene's 'duration_in_frames' MUST exactly match the background video duration (approx 150-180 frames).\n"
            "2. Visual overlays MUST enter and exit within these bounds. Sync them with the provided word-level timestamps.\n"
            "3. CANVAS SAFETY: Position {x: 960, y: 540} is center. Content MUST stay within X: [200, 1720] and Y: [150, 930].\n\n"
            "4. PROFESSIONAL CINEMATOGRAPHY:\n"
            "   - Use 'slow_push' or 'ken_burns' presets.\n"
            "   - Shot 'inDuration' should be 30-45 frames. Ensure 45-60 frames of resting time.\n\n"
            "5. POLISH:\n"
            "   - MANDATORY VIDEO BACKGROUNDS: 'background_type': 'video'. Path: 'renders/scene_SC_##.mp4'.\n"
            "   - MANDATORY AUDIO: 'audio_enabled': true.\n"
            "   - SHAKE OFF: 'camera.shake.enabled': false.\n"
            "   - BENGALI: 'splitMode': 'word'. Use script-appropriate fonts.\n"
            f"   - DETECTED FONTS: {local_fonts}\n\n"
            f"SYSTEM GUIDELINES:\n{guidelines}\n\n"
            f"STORY REQUIREMENTS:\n{story}\n\n"
            f"WORD-LEVEL TIMESTAMPS:\n{timestamp_context or 'No timestamps.'}\n\n"
            "TASK: Generate the complete JSON manifest. Return ONLY raw JSON."
        )

        if prompt_output_path:
            os.makedirs(os.path.dirname(prompt_output_path), exist_ok=True)
            with open(prompt_output_path, 'w', encoding='utf-8') as f: f.write(full_prompt)

        raw_output = self._interact_with_gemini(full_prompt)
        print(f"✅ Response received ({len(raw_output)}).")

        try:
            start_idx = raw_output.find('{')
            end_idx = raw_output.rfind('}')
            if start_idx != -1 and end_idx != -1:
                json_str = raw_output[start_idx:end_idx+1]
                try: return json.loads(json_str)
                except:
                    cleaned = re.sub(r',\s*}', '}', json_str)
                    cleaned = re.sub(r',\s*\]', ']', cleaned)
                    cleaned = re.sub(r'//.*$', '', cleaned, flags=re.MULTILINE)
                    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
                    return json.loads(cleaned)
            return json.loads(raw_output.strip())
        except Exception as e:
            print(f"❌ Extraction error: {e}")
            return {}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--story", help="Story text")
    parser.add_argument("--story-file", help="Path to story text")
    parser.add_argument("--output", required=True, help="Manifest output path")
    parser.add_argument("--timestamp-output", help="Timestamp output path")
    parser.add_argument("--prompt-output", help="Prompt output path")
    parser.add_argument("--user-data-dir", help="Chrome data dir")
    parser.add_argument("--no-headless", action="store_false", dest="headless")
    parser.add_argument("--drive-prompt", help="Guideline prompt path")
    parser.set_defaults(headless=True)
    args = parser.parse_args()

    story = args.story
    if args.story_file and os.path.exists(args.story_file):
        with open(args.story_file, 'r', encoding='utf-8') as f: story = f.read()
    if not story: exit(1)

    maker = RemotionJsonMaker(user_data_dir=args.user_data_dir, headless=args.headless)
    guidelines = maker.load_guidelines("../guideline.md", "../guideline_prompt.txt", args.drive_prompt)

    try:
        ts_content = None
        if args.timestamp_output:
            ts_content = maker.generate_word_timestamps(story)
            os.makedirs(os.path.dirname(args.timestamp_output), exist_ok=True)
            with open(args.timestamp_output, 'w', encoding='utf-8') as f: f.write(ts_content)

        render_json = maker.generate(story, guidelines, args.prompt_output, ts_content)
        maker.stop_browser()
        render_json = maker.finalize_json_durations(render_json)

        sfx_manifest_path = os.path.join(os.path.dirname(args.output), "../renders/audios/timestamp_audio.txt")
        if os.path.exists(sfx_manifest_path):
            with open(sfx_manifest_path, 'r', encoding='utf-8') as sf:
                render_json['audio_sfx_manifest'] = json.load(sf)

        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(render_json, f, indent=2, ensure_ascii=False)
        print(f"✅ Master JSON created: {args.output}")
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
