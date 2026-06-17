import os
import json
import argparse
import re
import time
import subprocess
import shutil
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
        return ", ".join(sorted(list(set(font_files))))

    def load_guidelines(self, local_guideline_path: str, local_prompt_path: str, drive_prompt_path: str) -> str:
        guidelines = ""
        for path in [local_guideline_path, local_prompt_path, drive_prompt_path]:
            if path and os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f: guidelines += f"\n--- {os.path.basename(path)} ---\n{f.read()}\n"
        return guidelines

    def finalize_json_durations(self, data: Dict[str, Any], public_dir: str = "../public") -> Dict[str, Any]:
        if not data or not data.get('scenes'): return data
        data['global_settings'] = { "width": 1920, "height": 1080, "fps": 30 }

        # Professional sizes with higher safety margin
        TYPE_SIZES = {
            'text': (1400, 400),
            'chart': (1550, 900),
            'ui_panel': (900, 750),
            'data_indicator': (800, 650),
            'media': (1000, 750),
            'image': (1000, 750),
            'video': (1000, 750)
        }

        # Logical layout slots (Safe Zones)
        SLOTS = {
            "TOP_LEFT": {"x": 480, "y": 270},
            "TOP_RIGHT": {"x": 1440, "y": 270},
            "BOTTOM_LEFT": {"x": 480, "y": 810},
            "BOTTOM_RIGHT": {"x": 1440, "y": 810},
            "CENTER_FOCAL": {"x": 960, "y": 540},
            "MID_LEFT": {"x": 480, "y": 540},
            "MID_RIGHT": {"x": 1440, "y": 540}
        }

        # SFX Mapping - Be extremely robust with pathing
        search_dirs = [
            os.path.join(public_dir, "renders/audios"),
            "/content/engine/public/renders/audios",
            "/content/drive/MyDrive/Counterism_Studio_V4/renders/audios",
            "/content/drive/MyDrive/Counterism_Studio_V4/render/audio"
        ]

        in_files, out_files = [], []
        for audio_dir in search_dirs:
            if os.path.exists(audio_dir):
                print(f"📡 Scanning SFX in {audio_dir}...")
                try:
                    all_files = os.listdir(audio_dir)
                    found_in = sorted([f for f in all_files if f.lower().startswith("in_") and (f.lower().endswith(".mp3") or f.lower().endswith(".wav") or f.lower().endswith(".m4a"))])
                    found_out = sorted([f for f in all_files if f.lower().startswith("out_") and (f.lower().endswith(".mp3") or f.lower().endswith(".wav") or f.lower().endswith(".m4a"))])
                    if found_in: in_files = found_in
                    if found_out: out_files = found_out
                    if in_files and out_files: break
                except: pass

        print(f"   Result: {len(in_files)} entrance and {len(out_files)} exit sounds available.")

        sfx_manifest = []
        in_ptr, out_ptr = 0, 0

        for scene in data['scenes']:
            scene_duration = scene.get('duration_in_frames', 180)
            if scene.get('background_type') == 'video' and scene.get('video_path'):
                abs_vpath = os.path.join(public_dir, scene['video_path'])
                if os.path.exists(abs_vpath):
                    duration_sec, _ = self.probe_video_duration_and_fps(abs_vpath)
                    if duration_sec > 0:
                        scene_duration = int(round(duration_sec * 30))
                        scene['duration_in_frames'] = scene_duration

            placed_overlays = []
            if scene.get('overlays'):
                for i, ov in enumerate(scene['overlays']):
                    ov_type = ov.get('type', 'text')
                    w, h = TYPE_SIZES.get(ov_type, (800, 800))
                    if ov_type == 'chart':
                        w = ov.get('width', 1000) + 300
                        h = ov.get('height', 650) + 300

                    # 1. Slot Assignment (Mapping slot names to coordinates)
                    slot_name = ov.get('slot', '')
                    if slot_name in SLOTS:
                        ov['position'] = {"x": SLOTS[slot_name]["x"], "y": SLOTS[slot_name]["y"]}
                    elif not ov.get('position'):
                         # Intelligent default: Use index-based sector fallback
                         keys = list(SLOTS.keys())
                         selected = keys[i % len(keys)]
                         ov['position'] = {"x": SLOTS[selected]["x"], "y": SLOTS[selected]["y"]}

                    # 2. Collision Nudging
                    for prev_ov, prev_w, prev_h in placed_overlays:
                        start1, end1 = ov.get('start', 0), ov.get('start', 0) + ov.get('duration', 60)
                        start2, end2 = prev_ov.get('start', 0), prev_ov.get('start', 0) + prev_ov.get('duration', 60)

                        if max(start1, start2) < min(end1, end2):
                            x1, y1 = ov['position']['x'], ov['position']['y']
                            x2, y2 = prev_ov['position']['x'], prev_ov['position']['y']
                            if abs(x1 - x2) < (w + prev_w) / 2 and abs(y1 - y2) < (h + prev_h) / 2:
                                if y1 <= y2: ov['position']['y'] = y2 - (h + prev_h) / 2 - 100
                                else: ov['position']['y'] = y2 + (h + prev_h) / 2 + 100

                    # 3. Final Margin Clamping
                    margin = 150
                    x_min, x_max = w/2 + margin, 1920 - w/2 - margin
                    y_min, y_max = h/2 + margin, 1080 - h/2 - margin
                    if x_min > x_max: x_min, x_max = 960, 960
                    if y_min > y_max: y_min, y_max = 540, 540

                    ov['position']['x'] = max(x_min, min(x_max, int(ov['position'].get('x', 960))))
                    ov['position']['y'] = max(y_min, min(y_max, int(ov['position'].get('y', 540))))

                    placed_overlays.append((ov, w, h))

                    if ov.get('start', 0) >= scene_duration: ov['start'] = max(0, scene_duration - 60)
                    if ov.get('start', 0) + ov.get('duration', 60) > scene_duration: ov['duration'] = scene_duration - ov.get('start', 0)
                    if ov.get('duration', 0) < 60: ov['duration'] = 60

                    # Assign local SFX
                    if in_files:
                        sfx_manifest.append({ "scene_id": scene['scene_id'], "file": in_files[in_ptr % len(in_files)], "start": ov['start'], "end": ov['start'] + 30, "volume": 0.25 })
                        in_ptr += 1
                    if out_files:
                        sfx_manifest.append({ "scene_id": scene['scene_id'], "file": out_files[out_ptr % len(out_files)], "start": ov['start'] + ov['duration'] - 15, "end": ov['start'] + ov['duration'], "volume": 0.25 })
                        out_ptr += 1

        data['audio_sfx_manifest'] = sfx_manifest
        return data

    def generate_word_timestamps(self, story: str, public_dir: str = "../public") -> str:
        print("🎙️  Generating precise word-level timestamps (30fps)...")
        scenes = re.split(r'দৃশ্য\s+[0-9০-৯]+', story)
        scene_texts = [s.strip() for s in scenes if s.strip()]
        full_ts_prompt = "You are a Voiceover Alignment Expert. Generate EXACT word-level timestamps in FRAMES for a 30fps project.\n\n"
        for i, scene_text in enumerate(scene_texts):
            scene_num = i + 1
            vpath = f"renders/scene_SC_{scene_num:02d}.mp4"
            duration_sec = 6.0
            abs_vpath = os.path.join(public_dir, vpath)
            if os.path.exists(abs_vpath):
                duration_sec, _ = self.probe_video_duration_and_fps(abs_vpath)
            total_frames = int(round(duration_sec * 30))
            full_ts_prompt += f"--- SCENE {scene_num:02d} (Duration: {total_frames} frames / {duration_sec}s) ---\nVOICEOVER: {scene_text}\n\n"
        full_ts_prompt += "INSTRUCTIONS: Format: SCENE_XX: [Frame Start - Frame End] \"Word\". Return ONLY timestamps.\n"
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
            "STYLE: Sci-fi interface aesthetic. Minimalist but high-tech. Balanced Quadrant Layout.\n\n"
            "CRITICAL RULES:\n"
            "1. AUDIO SYNC: Every focal overlay (Text, Chart, KPI) MUST start and end EXACTLY with the word-level timestamps provided. Sync visual entrance/exit to narrative pacing.\n"
            "2. PROFESSIONAL LAYOUT (SLOT-BASED): Elements must be assigned to one of these SLOTS: 'TOP_LEFT', 'TOP_RIGHT', 'BOTTOM_LEFT', 'BOTTOM_RIGHT', 'CENTER_FOCAL', 'MID_LEFT', 'MID_RIGHT'.\n"
            "   - If a Chart is in 'TOP_RIGHT', place Text in 'BOTTOM_LEFT'. Use opposing quadrants to balance the visual weight.\n"
            "3. OVERLAP PREVENTION: Assign different SLOTS to overlays that are visible at the same time.\n"
            "4. CANVAS SAFETY: All slots are already safe. Do not place elements randomly. Stay within the 150px safety margin.\n"
            "5. CINEMATOGRAPHY: Use 'slow_push' or 'ken_burns'. 45-60 frames of resting time per focus.\n"
            "6. TEXT CONCISION: 'text' content MUST BE STRICTLY 2-3 words maximum. Captures feelings only.\n"
            "7. MANDATORY: 'background_type': 'video', 'audio_enabled': true, 'camera.shake.enabled': false.\n"
            "8. SCRIPTS: For Bengali, ALWAYS use 'splitMode': 'word'.\n"
            f"9. DETECTED FONTS: {local_fonts}\n\n"
            f"SYSTEM GUIDELINES:\n{guidelines}\n\n"
            f"STORY REQUIREMENTS:\n{story}\n\n"
            f"PRECISE WORD TIMESTAMPS (USE THESE FOR SYNC):\n{timestamp_context or 'No timestamps.'}\n\n"
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

        # FINAL DRIVE PERSISTENCE FIX
        output_dir = os.path.dirname(args.output)
        if not os.path.exists(output_dir): os.makedirs(output_dir, exist_ok=True)

        with open(args.output, 'w', encoding='utf-8') as f: json.dump(render_json, f, indent=2, ensure_ascii=False)
        print(f"✅ Master JSON created: {args.output} ({os.path.getsize(args.output)} bytes)")

        # Redundant copy to content root for insurance
        try: shutil.copy(args.output, "/content/remotion_render.json")
        except: pass

    except Exception as e:
        print(f"❌ Error in main: {e}")
        exit(1)
if __name__ == "__main__": main()
