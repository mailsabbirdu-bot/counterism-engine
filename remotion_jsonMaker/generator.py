import os
import json
import argparse
import re
import time
import subprocess
import shutil
import math
from typing import Dict, Any, List
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
        if self.page: return
        self.playwright = sync_playwright().start()
        print("🚀 Launching persistent browser...")
        args = ["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        if self.user_data_dir:
            self.context = self.playwright.chromium.launch_persistent_context(self.user_data_dir, headless=self.headless, args=args)
        else:
            self.browser = self.playwright.chromium.launch(headless=self.headless, args=args)
            self.context = self.browser.new_context()
        self.page = self.context.new_page()
        playwright_stealth.Stealth().apply_stealth_sync(self.page)
        print("🌐 Navigating to Gemini...")
        self.page.goto("https://gemini.google.com/app", wait_until="networkidle", timeout=60000)

    def stop_browser(self):
        if self.context: self.context.close()
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()
        self.page = None

    def probe_video_duration_and_fps(self, video_path: str):
        try:
            # Precise probe for 30fps target
            cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path]
            output = subprocess.check_output(cmd).decode("utf-8").strip()
            duration_sec = float(output) if output else 0.0
            return duration_sec, 30.0
        except Exception as e:
            print(f"⚠️ Error probing video: {e}")
            return 0.0, 30.0

    def adjust_durations_in_text(self, text: str, public_dir: str = "../public") -> str:
        def replacement_logic(match):
            block = match.group(0)
            vpath_match = re.search(r'"video_path":\s*"([^"]+)"', block)
            if vpath_match:
                rel_vpath = vpath_match.group(1)
                abs_vpath = os.path.join(public_dir, rel_vpath)
                if os.path.exists(abs_vpath):
                    duration_sec, _ = self.probe_video_duration_and_fps(abs_vpath)
                    if duration_sec > 0:
                        new_duration = int(math.ceil(duration_sec * 30))
                        return re.sub(r'"duration_in_frames"\s*:\s*\d+', f'"duration_in_frames": {new_duration}', block)
            return block
        pattern1 = r'("video_path":\s*"[^"]+"(?:(?!"video_path"|"duration_in_frames").){0,300}?"duration_in_frames"\s*:\s*\d+)'
        text = re.sub(pattern1, replacement_logic, text, flags=re.DOTALL)
        return text

    def get_local_fonts(self, public_dir: str = "../public") -> str:
        fonts_dir = os.path.join(public_dir, "fonts")
        font_files = []
        if os.path.exists(fonts_dir):
            for file in os.listdir(fonts_dir):
                if file.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
                    font_files.append(os.path.splitext(file)[0])
        return ", ".join(sorted(list(set(font_files))))

    def finalize_json_durations(self, data: Dict[str, Any], public_dir: str = "../public") -> Dict[str, Any]:
        if not data or not data.get('scenes'): return data
        data['global_settings'] = { "width": 1920, "height": 1080, "fps": 30 }

        # Stricter sizes to ensure visibility of background
        TYPE_SIZES = {
            'text': (1000, 250),
            'chart': (1100, 600),
            'ui_panel': (600, 500),
            'data_indicator': (500, 400),
            'media': (800, 600)
        }

        # Logical sectors (Safe Regions)
        SECTORS = {
            "TOP_LEFT": {"x": 480, "y": 270},
            "TOP_RIGHT": {"x": 1440, "y": 270},
            "BOTTOM_LEFT": {"x": 480, "y": 810},
            "BOTTOM_RIGHT": {"x": 1440, "y": 810},
            "MID_LEFT": {"x": 480, "y": 540},
            "MID_RIGHT": {"x": 1440, "y": 540}
        }

        audio_dir = os.path.join(public_dir, "renders/audios")
        in_files = sorted([f for f in os.listdir(audio_dir) if f.startswith("in_") and f.endswith(".mp3")]) if os.path.exists(audio_dir) else []
        out_files = sorted([f for f in os.listdir(audio_dir) if f.startswith("out_") and f.endswith(".mp3")]) if os.path.exists(audio_dir) else []

        sfx_manifest = []
        in_ptr, out_ptr = 0, 0

        for scene in data['scenes']:
            scene_duration = scene.get('duration_in_frames', 180)
            if scene.get('background_type') == 'video' and scene.get('video_path'):
                abs_vpath = os.path.join(public_dir, scene['video_path'])
                if os.path.exists(abs_vpath):
                    duration_sec, _ = self.probe_video_duration_and_fps(abs_vpath)
                    if duration_sec > 0:
                        scene_duration = int(math.ceil(duration_sec * 30))
                        scene['duration_in_frames'] = scene_duration

            placed_overlays = []
            if scene.get('overlays'):
                for i, ov in enumerate(scene['overlays']):
                    ov_type = ov.get('type', 'text')
                    w, h = TYPE_SIZES.get(ov_type, (600, 600))

                    # 1. Professional Slot Alignment
                    slot = ov.get('slot', '')
                    if slot in SECTORS:
                        ov['position'] = {"x": SECTORS[slot]["x"], "y": SECTORS[slot]["y"]}
                    elif not ov.get('position'):
                         keys = list(SECTORS.keys())
                         ov['position'] = {"x": SECTORS[keys[i % len(keys)]]["x"], "y": SECTORS[keys[i % len(keys)]]["y"]}

                    # 2. Collision & Overlap Prevention
                    for prev_ov, prev_w, prev_h in placed_overlays:
                        if abs(ov['position']['x'] - prev_ov['position']['x']) < (w + prev_w) / 2.2 and \
                           abs(ov['position']['y'] - prev_ov['position']['y']) < (h + prev_h) / 2.2:
                            ov['position']['y'] += 300 # Heavy nudge

                    # 3. Final Screen Clamping
                    margin = 150
                    ov['position']['x'] = max(margin + w/2, min(1920 - margin - w/2, int(ov['position'].get('x', 960))))
                    ov['position']['y'] = max(margin + h/2, min(1080 - margin - h/2, int(ov['position'].get('y', 540))))

                    # Timing Normalization
                    if ov.get('start', 0) >= scene_duration: ov['start'] = max(0, scene_duration - 60)
                    if ov.get('duration', 0) < 60: ov['duration'] = 60
                    if ov.get('start') + ov.get('duration') > scene_duration:
                        ov['duration'] = scene_duration - ov['start']

                    placed_overlays.append((ov, w, h))

                    # Subtle SFX
                    if in_files:
                        sfx_manifest.append({ "scene_id": scene['scene_id'], "file": in_files[in_ptr % len(in_files)], "start": ov['start'], "end": ov['start'] + 20, "volume": 0.12 })
                        in_ptr += 1
                    if out_files:
                        sfx_manifest.append({ "scene_id": scene['scene_id'], "file": out_files[out_ptr % len(out_files)], "start": ov['start'] + ov['duration'] - 10, "end": ov['start'] + ov['duration'], "volume": 0.12 })
                        out_ptr += 1

        data['audio_sfx_manifest'] = sfx_manifest
        return data

    def generate_word_timestamps(self, story: str, public_dir: str = "../public") -> str:
        print("🎙️  Generating precise word-level timestamps (30fps baseline)...")
        scenes = re.split(r'দৃশ্য\s+[0-9০-৯]+', story)
        scene_texts = [s.strip() for s in scenes if s.strip()]
        full_ts_prompt = "You are a Voiceover Alignment Expert. Generate word-level timestamps in FRAMES for a 30fps project.\n\n"
        for i, scene_text in enumerate(scene_texts):
            scene_num = i + 1
            vpath = f"renders/scene_SC_{scene_num:02d}.mp4"
            duration_sec = 6.0
            abs_vpath = os.path.join(public_dir, vpath)
            if os.path.exists(abs_vpath):
                duration_sec, _ = self.probe_video_duration_and_fps(abs_vpath)
            total_frames = int(math.ceil(duration_sec * 30))
            full_ts_prompt += f"--- SCENE {scene_num:02d} (Target Duration: {total_frames} frames) ---\nVOICEOVER: {scene_text}\n\n"
        full_ts_prompt += "INSTRUCTIONS: Format: SCENE_XX: [Frame Start - Frame End] \"Word\". Ensure 30fps mapping. Return ONLY timestamps.\n"
        return self._interact_with_gemini(full_ts_prompt)

    def _interact_with_gemini(self, prompt: str, retry_count: int = 2) -> str:
        for attempt in range(retry_count + 1):
            self.start_browser()
            page = self.page
            try:
                response_selectors = ["message-content", ".markdown.message-content", ".model-response-text", "[data-message-author-role='assistant']"]
                def get_msg_count():
                    for sel in response_selectors:
                        msgs = page.query_selector_all(sel)
                        if msgs: return len(msgs)
                    return 0

                initial_count = get_msg_count()
                print(f"   ...initial message count: {initial_count}")

                page.evaluate("""() => {
                    const selectors = ['button[aria-label="Accept all"]', 'button:has-text("Accept")', 'button:has-text("I agree")', '.cdk-overlay-container'];
                    selectors.forEach(s => {
                        try {
                            const elements = document.querySelectorAll(s);
                            elements.forEach(el => el.remove());
                        } catch(e) {}
                    });
                }""")

                input_selector = "div[contenteditable='true']"
                page.wait_for_selector(input_selector, timeout=30000)

                print(f"⌨️  Sending prompt to Gemini (Attempt {attempt+1})...")
                page.click(input_selector, force=True)
                time.sleep(1)
                page.fill(input_selector, prompt)
                time.sleep(1)
                page.keyboard.press("Enter")

                try:
                    btn = "button[aria-label*='Send message'], button[aria-label*='Submit']"
                    if page.is_visible(btn, timeout=2000): page.click(btn, force=True)
                except: pass

                print("⏳  Waiting for new message to appear...")
                last_text = ""
                stable_count = 0
                for i in range(250):
                    time.sleep(2)
                    if get_msg_count() <= initial_count: continue
                    current_text = ""
                    for sel in response_selectors:
                        msgs = page.query_selector_all(sel)
                        if msgs:
                            current_text = msgs[-1].inner_text()
                            break
                    if current_text and current_text == last_text:
                        stable_count += 1
                        if stable_count >= 8:
                            if len(current_text) > 100:
                                 print(f"✨ Gemini response received ({len(current_text)} chars).")
                                 return current_text
                            break
                    else:
                        stable_count = 0
                        last_text = current_text

                print("🔄  Reloading Gemini...")
                page.reload(wait_until="domcontentloaded")
                time.sleep(5)
            except Exception as e:
                print(f"⚠️ Error in Gemini interaction: {e}")
                page.reload(wait_until="domcontentloaded")
                time.sleep(5)
        return ""

    def generate(self, story: str, guidelines: str, prompt_output_path: str = None, timestamp_context: str = None) -> Dict[str, Any]:
        story = self.adjust_durations_in_text(story)
        guidelines = self.adjust_durations_in_text(guidelines)
        local_fonts = self.get_local_fonts()
        full_prompt = (
            "You are a world-class Motion Graphics Director. Generate an ULTRA MODERN cinematic JSON manifest.\n\n"
            "STYLE: Sci-fi interface. Professional Balanced Layout. Don't block the background video.\n\n"
            "CRITICAL RULES:\n"
            "1. AUDIO SYNC: Every focal overlay MUST start/end EXACTLY with the word-level timestamps provided.\n"
            "2. CINEMATIC PACING (RESTING): Every layer must have Intro (15f), RESTING (minimum 90-120f), and Outro (15f). RESTING IS MOVRELESS.\n"
            "3. PROFESSIONAL SLOTS: Assign 'slot' to: 'TOP_LEFT', 'TOP_RIGHT', 'BOTTOM_LEFT', 'BOTTOM_RIGHT', 'CENTER_FOCAL', 'MID_LEFT', 'MID_RIGHT'.\n"
            "4. NO OVERLAP: Use opposing quadrants (e.g. Chart: TOP_RIGHT, Text: BOTTOM_LEFT).\n"
            "5. CANVAS SAFETY: Elements must stay within 150px margin. Text content MUST BE 2-3 words max.\n"
            "6. FONTS: If text is Bengali, use the detected Bangla font. If English, use the English font from detected fonts.\n"
            "7. MANDATORY: 'background_type': 'video', 'audio_enabled': true, 'camera.shake.enabled': false.\n"
            f"8. DETECTED FONTS: {local_fonts}\n\n"
            f"SYSTEM GUIDELINES:\n{guidelines}\n\n"
            f"STORY REQUIREMENTS:\n{story}\n\n"
            f"WORD TIMESTAMPS (USE FOR SYNC):\n{timestamp_context or 'No timestamps.'}\n\n"
            "TASK: Generate complete JSON manifest. Return ONLY raw JSON."
        )
        if prompt_output_path:
            with open(prompt_output_path, 'w', encoding='utf-8') as f: f.write(full_prompt)
        raw_output = self._interact_with_gemini(full_prompt)
        try:
            start_idx, end_idx = raw_output.find('{'), raw_output.rfind('}')
            if start_idx != -1 and end_idx != -1:
                json_str = raw_output[start_idx:end_idx+1]
                json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
                json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
                try: return json.loads(json_str)
                except:
                    cleaned = re.sub(r',\s*\}', '}', json_str)
                    cleaned = re.sub(r',\s*\]', ']', cleaned)
                    return json.loads(cleaned)
            return {}
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
    if os.path.exists(args.output): os.remove(args.output)
    with open(args.story_file, 'r', encoding='utf-8') as f: story = f.read()
    maker = RemotionJsonMaker(user_data_dir=args.user_data_dir, headless=args.headless)
    guidelines = maker.load_guidelines("../guideline.md", "../guideline_prompt.txt", args.drive_prompt)
    try:
        ts_content = None
        if args.timestamp_output:
            if os.path.exists(args.timestamp_output): os.remove(args.timestamp_output)
            ts_content = maker.generate_word_timestamps(story)
            if not ts_content or len(ts_content) < 50:
                 ts_content = maker.generate_word_timestamps(story)
            with open(args.timestamp_output, 'w', encoding='utf-8') as f: f.write(ts_content)
        render_json = maker.generate(story, guidelines, args.prompt_output, ts_content)
        maker.stop_browser()
        if not render_json or 'scenes' not in render_json:
             print("❌ ERROR: Gemini failed to produce a valid manifest.")
             exit(1)
        render_json = maker.finalize_json_durations(render_json)

        output_dir = os.path.dirname(args.output)
        if not os.path.exists(output_dir): os.makedirs(output_dir, exist_ok=True)

        with open(args.output, 'w', encoding='utf-8') as f: json.dump(render_json, f, indent=2, ensure_ascii=False)
        print(f"✅ Master JSON created: {args.output} ({os.path.getsize(args.output)} bytes)")
        try: shutil.copy(args.output, "/content/remotion_render.json")
        except: pass

    except Exception as e:
        print(f"❌ Error in main: {e}")
        exit(1)
if __name__ == "__main__": main()
