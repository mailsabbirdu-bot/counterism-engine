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
        browser_args = ["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        if self.user_data_dir:
            self.context = self.playwright.chromium.launch_persistent_context(self.user_data_dir, headless=self.headless, args=browser_args)
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
            cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration,nb_frames,r_frame_rate", "-of", "json", video_path]
            output = subprocess.check_output(cmd).decode("utf-8")
            data = json.loads(output)
            if not data.get('streams'):
                cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", video_path]
                output = subprocess.check_output(cmd).decode("utf-8")
                data = json.loads(output)
                return float(data['format'].get('duration', 0)), 30.0
            stream = data['streams'][0]
            duration = float(stream.get('duration', 0))
            if duration == 0:
                cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", video_path]
                output = subprocess.check_output(cmd).decode("utf-8")
                data = json.loads(output)
                duration = float(data['format'].get('duration', 0))
            return duration, 30.0
        except Exception as e: return 0.0, 30.0

    def adjust_durations_in_text(self, text: str, public_dir: str = "../public") -> str:
        """Scans text for video_path and duration_in_frames and adjusts them."""
        def replacement_logic(match):
            block = match.group(0)
            vpath_match = re.search(r'"video_path":\s*"([^"]+)"', block)
            duration_match = re.search(r'"duration_in_frames"\s*:\s*(\d+)', block)
            if vpath_match:
                rel_vpath = vpath_match.group(1)
                abs_vpath = os.path.join(public_dir, rel_vpath)
                if os.path.exists(abs_vpath):
                    duration_sec, _ = self.probe_video_duration_and_fps(abs_vpath)
                    if duration_sec > 0:
                        new_duration = int(round(duration_sec * 30))
                        if duration_match:
                            return re.sub(r'"duration_in_frames"\s*:\s*\d+', f'"duration_in_frames": {new_duration}', block)
            return block
        pattern1 = r'("video_path":\s*"[^"]+"(?:(?!"video_path"|"duration_in_frames").){0,300}?"duration_in_frames"\s*:\s*\d+)'
        text = re.sub(pattern1, replacement_logic, text, flags=re.DOTALL)
        pattern2 = r'("duration_in_frames"\s*:\s*\d+(?:(?!"video_path"|"duration_in_frames").){0,300}?"video_path":\s*"[^"]+")'
        text = re.sub(pattern2, replacement_logic, text, flags=re.DOTALL)
        return text

    def get_local_fonts(self, public_dir: str = "../public") -> str:
        fonts_dir = os.path.join(public_dir, "fonts")
        potential_dirs = [fonts_dir, os.path.join(fonts_dir, "drive_fonts")]
        font_files = []
        for d in potential_dirs:
            if os.path.exists(d):
                for file in os.listdir(d):
                    if file.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
                        font_files.append(os.path.splitext(file)[0])
        return ", ".join(sorted(list(set(font_files)))) or "No local fonts detected."

    def load_guidelines(self, local_guideline_path: str, local_prompt_path: str, drive_prompt_path: str) -> str:
        guidelines = ""
        for path in [local_guideline_path, local_prompt_path, drive_prompt_path]:
            if path and os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    guidelines += f"\n--- {os.path.basename(path)} ---\n{f.read()}\n"
        return guidelines

    def finalize_json_durations(self, data: Dict[str, Any], public_dir: str = "../public") -> Dict[str, Any]:
        """Ensures frame-accurate duration and clamps overlay properties to safe zones."""
        if not data or not data.get('scenes'): return data
        data['global_settings'] = { "width": 1920, "height": 1080, "fps": 30 }
        for scene in data['scenes']:
            scene_duration = scene.get('duration_in_frames', 180) # Default to 6s
            if scene.get('background_type') == 'video' and scene.get('video_path'):
                abs_vpath = os.path.join(public_dir, scene['video_path'])
                if os.path.exists(abs_vpath):
                    duration_sec, _ = self.probe_video_duration_and_fps(abs_vpath)
                    if duration_sec > 0:
                        scene_duration = max(180, int(round(duration_sec * 30))) # Min 6s
                        scene['duration_in_frames'] = scene_duration
            if scene.get('overlays'):
                for ov in scene['overlays']:
                    if ov.get('position'):
                        ov['position']['x'] = max(250, min(1670, int(ov['position'].get('x', 960))))
                        ov['position']['y'] = max(200, min(880, int(ov['position'].get('y', 540))))
                    else: ov['position'] = {"x": 960, "y": 540}
                    if ov.get('start', 0) >= scene_duration:
                        ov['start'] = max(0, scene_duration - 60)
                    if ov.get('start', 0) + ov.get('duration', 60) > scene_duration:
                        ov['duration'] = scene_duration - ov.get('start', 0)
                    if ov.get('duration', 0) < 60: ov['duration'] = 60 # Min overlay stay
        return data

    def generate_word_timestamps(self, story: str, public_dir: str = "../public") -> str:
        """Parses story and estimates word-level timestamps via Gemini."""
        print("🎙️  Generating word-level timestamps...")
        scene_texts = [s.strip() for s in re.split(r'দৃশ্য\s+[0-9০-৯]+', story) if s.strip()]
        full_ts_prompt = "You are a Voiceover Alignment Assistant. Provide word-level timestamps in FRAMES for a 30fps project. MINIMUM scene duration is 180 frames.\n\n"
        for i, scene_text in enumerate(scene_texts):
            scene_num = i + 1
            vpath = f"renders/scene_SC_{scene_num:02d}.mp4"
            duration_sec = 6.0
            abs_vpath = os.path.join(public_dir, vpath)
            if os.path.exists(abs_vpath):
                duration_sec, _ = self.probe_video_duration_and_fps(abs_vpath)
            full_ts_prompt += f"--- SCENE {scene_num:02d} ({duration_sec}s / {int(round(duration_sec * 30))} frames) ---\nTEXT: {scene_text}\n\n"
        full_ts_prompt += "Format: SCENE_XX: [Frame X - Frame Y] Word, ...\nReturn ONLY the timestamps."
        return self._interact_with_gemini(full_ts_prompt)

    def _interact_with_gemini(self, prompt: str, retry_count: int = 2) -> str:
        """Helper method for Gemini interaction with retry and reload logic."""
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
                try:
                    btn = "button[aria-label*='Send message'], button[aria-label*='Submit']"
                    if page.is_visible(btn, timeout=2000): page.click(btn)
                except: pass
                print("⏳  Waiting for Gemini...")
                response_selectors = ["message-content", ".markdown.message-content", ".model-response-text", "[data-message-author-role='assistant']"]
                last_text = ""
                stable_count = 0
                for i in range(150):
                    time.sleep(2)
                    current_text = ""
                    for sel in response_selectors:
                        msgs = page.query_selector_all(sel)
                        if msgs:
                            current_text = msgs[-1].inner_text()
                            break
                    if current_text and current_text == last_text:
                        stable_count += 1
                        if stable_count >= 5:
                            print(f"✅  Received ({len(current_text)} chars).")
                            if len(current_text) > 100: return current_text
                            break
                    else:
                        stable_count = 0
                        last_text = current_text
                print("🔄  Reloading Gemini...")
                page.reload(wait_until="networkidle")
                time.sleep(5)
            except Exception as e:
                print(f"⚠️ Error: {e}")
                page.reload(wait_until="networkidle")
        return ""

    def generate(self, story: str, guidelines: str, prompt_output_path: str = None, timestamp_context: str = None) -> Dict[str, Any]:
        story = self.adjust_durations_in_text(story)
        guidelines = self.adjust_durations_in_text(guidelines)
        local_fonts = self.get_local_fonts()
        full_prompt = (
            "You are a world-class Motion Graphics Director. Generate an ULTRA MODERN cinematic JSON manifest.\n\n"
            "CRITICAL TIMING & CANVAS RULES:\n"
            "1. TIMING: SCENE_DURATION MUST be at least 180 frames (6s). Visuals MUST enter and exit within these bounds, synced with word-level timestamps.\n"
            "2. CAMERA & CANVAS: Center is {x: 960, y: 540}. All overlays MUST be clustered between X: [250, 1670] and Y: [200, 880]. "
            "IMPORTANT: When the camera zooms in (zoom > 1.2), keep overlays closer to the center (x: 960, y: 540) to prevent them being pushed off-canvas.\n"
            "3. PROFESSIONAL CINEMATOGRAPHY: Use 'slow_push' or 'ken_burns'. Shot 'inDuration' 30-45 frames. Minimum 60 frames of resting time.\n"
            "4. MANDATORY: 'background_type': 'video', 'audio_enabled': true, 'camera.shake.enabled': false.\n"
            "5. SCRIPTS: For Bengali, ALWAYS use 'splitMode': 'word'.\n"
            f"6. DETECTED FONTS: {local_fonts}\n\n"
            f"SYSTEM GUIDELINES:\n{guidelines}\n\n"
            f"STORY:\n{story}\n\n"
            f"TIMESTAMPS:\n{timestamp_context or 'No timestamps.'}\n\n"
            "TASK: Generate complete JSON manifest. Return ONLY raw JSON."
        )
        if prompt_output_path:
            with open(prompt_output_path, 'w', encoding='utf-8') as f: f.write(full_prompt)
        raw_output = self._interact_with_gemini(full_prompt)
        try:
            start_idx, end_idx = raw_output.find('{'), raw_output.rfind('}')
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
        except: return {}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--story-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timestamp-output")
    parser.add_argument("--prompt-output")
    parser.add_argument("--user-data-dir")
    parser.add_argument("--no-headless", action="store_false", dest="headless")
    parser.add_argument("--drive-prompt")
    parser.set_defaults(headless=True)
    args = parser.parse_args()
    if not os.path.exists(args.story_file): exit(1)
    with open(args.story_file, 'r', encoding='utf-8') as f: story = f.read()
    maker = RemotionJsonMaker(user_data_dir=args.user_data_dir, headless=args.headless)
    guidelines = maker.load_guidelines("../guideline.md", "../guideline_prompt.txt", args.drive_prompt)
    try:
        ts_content = None
        if args.timestamp_output:
            ts_content = maker.generate_word_timestamps(story)
            with open(args.timestamp_output, 'w', encoding='utf-8') as f: f.write(ts_content)
        render_json = maker.generate(story, guidelines, args.prompt_output, ts_content)
        maker.stop_browser()
        render_json = maker.finalize_json_durations(render_json)
        sfx_path = os.path.join(os.path.dirname(args.output), "../renders/audios/timestamp_audio.txt")
        if os.path.exists(sfx_path):
            with open(sfx_path, 'r', encoding='utf-8') as sf:
                render_json['audio_sfx_manifest'] = json.load(sf)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(render_json, f, indent=2, ensure_ascii=False)
        print(f"✅ Master JSON created: {args.output}")
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

if __name__ == "__main__": main()
