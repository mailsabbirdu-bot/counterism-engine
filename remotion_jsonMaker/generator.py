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

    def load_guidelines(self, local_guideline_path: str, local_prompt_path: str, drive_prompt_path: str) -> str:
        guidelines = ""
        for path in [local_guideline_path, local_prompt_path, drive_prompt_path]:
            if path and os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f: guidelines += f"\n--- {os.path.basename(path)} ---\n{f.read()}\n"
        return guidelines

    def probe_video_duration_and_fps(self, video_path: str):
        try:
            # Reliable JSON-based probe
            cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration,avg_frame_rate", "-of", "json", video_path]
            output = subprocess.check_output(cmd).decode("utf-8")
            data = json.loads(output)
            streams = data.get('streams', [])
            stream = streams[0] if streams else {}

            # Duration can be in stream or format
            duration_sec = float(stream.get('duration', data.get('format', {}).get('duration', 0)))

            fps_raw = stream.get('avg_frame_rate', '30/1')
            if '/' in fps_raw:
                num, den = fps_raw.split('/')
                native_fps = float(num) / float(den) if float(den) != 0 else 30.0
            else:
                native_fps = float(fps_raw)

            # Target is always 30.0 for our rendering engine
            return duration_sec, 30.0
        except Exception as e:
            print(f"⚠️ Error probing video {video_path}: {e}")
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
        # Use absolute path to ensure accuracy
        abs_public = os.path.abspath(public_dir)
        fonts_dir = os.path.join(abs_public, "fonts")
        bangla_fonts = []
        english_fonts = []

        print(f"📂 Scanning for fonts in: {fonts_dir}")

        # Categorization keywords
        BANGLA_KEYWORDS = ['solaiman', 'kalpurush', 'nikosh', 'hind', 'siliguri', 'adorsho', 'sutonny', 'shonar', 'vrinda', 'bangla', 'liyakats', 'anshu', 'charukola', 'galada', 'mina', 'mukti', 'atreyee', 'benisen', 'bengali', 'shishir', 'shorif', 'maharaj']

        if os.path.exists(fonts_dir):
            for root, dirs, files in os.walk(fonts_dir, followlinks=True):
                for file in files:
                    if file.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
                        name = os.path.splitext(file)[0]
                        # Remove common weight/style suffixes for cleaner names in prompt
                        clean_name = re.sub(r'-(Regular|Bold|Italic|Light|Medium|Thin|SemiBold|ExtraBold|Black)$', '', name, flags=re.IGNORECASE)
                        if any(kw in clean_name.lower() for kw in BANGLA_KEYWORDS):
                            bangla_fonts.append(clean_name)
                        else:
                            english_fonts.append(clean_name)

        bangla_str = ", ".join(sorted(list(set(bangla_fonts))))
        english_str = ", ".join(sorted(list(set(english_fonts))))

        print(f"🔍 Font Detection: Found {len(bangla_fonts)} Bangla fonts: {bangla_fonts[:5]}...")
        print(f"🔍 Font Detection: Found {len(english_fonts)} English fonts: {english_fonts[:5]}...")
        return f"BANGLA FONTS: [{bangla_str}] | ENGLISH FONTS: [{english_str}]"

    def finalize_json_durations(self, data: Dict[str, Any], public_dir: str = "../public") -> Dict[str, Any]:
        if not data: return data
        if 'audio_sfx_manifest' not in data: data['audio_sfx_manifest'] = []
        if not data.get('scenes'): return data
        data['global_settings'] = { "width": 1920, "height": 1080, "fps": 30 }

        # Professional sizes with higher safety margin
        TYPE_SIZES = {
            'text': (1200, 300),
            'chart': (1300, 750),
            'ui_panel': (750, 600),
            'data_indicator': (600, 500),
            'media': (1000, 800),
            'image': (1000, 800),
            'video': (1000, 800)
        }

        # Logical sectors (Safe Zones)
        SECTORS = {
            "TOP_LEFT": {"x": 480, "y": 270},
            "TOP_RIGHT": {"x": 1440, "y": 270},
            "BOTTOM_LEFT": {"x": 480, "y": 810},
            "BOTTOM_RIGHT": {"x": 1440, "y": 810},
            "CENTER_FOCAL": {"x": 960, "y": 540},
            "MID_LEFT": {"x": 480, "y": 540},
            "MID_RIGHT": {"x": 1440, "y": 540}
        }

        audio_dir = os.path.join(public_dir, "renders/audios")
        in_files = []
        out_files = []

        if os.path.exists(audio_dir):
            all_files = os.listdir(audio_dir)
            in_files = sorted([f for f in all_files if f.lower().startswith("in_") and f.lower().endswith(('.mp3', '.wav', '.m4a'))])
            out_files = sorted([f for f in all_files if f.lower().startswith("out_") and f.lower().endswith(('.mp3', '.wav', '.m4a'))])

        print(f"🎵 Audio Detection: Found {len(in_files)} entrance sounds: {in_files[:5]}...")
        print(f"🎵 Audio Detection: Found {len(out_files)} exit sounds: {out_files[:5]}...")

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
                    w, h = TYPE_SIZES.get(ov_type, (800, 800))
                    if ov_type == 'chart':
                        w = ov.get('width', 1000) + 300
                        h = ov.get('height', 650) + 300

                    # 1. Professional Slot Alignment & De-confliction
                    slot_name = ov.get('slot', '')

                    # Force Text and Charts into opposing quadrants if they overlap in time
                    if ov_type == 'chart':
                        # Charts prefer mid/right slots for better data visibility
                        if not slot_name or slot_name not in ["TOP_RIGHT", "BOTTOM_RIGHT", "MID_RIGHT"]:
                             slot_name = ["TOP_RIGHT", "BOTTOM_RIGHT", "MID_RIGHT"][i % 3]
                    elif ov_type == 'text':
                        # Text prefers left slots to avoid blocking chart data
                        if not slot_name or slot_name not in ["TOP_LEFT", "BOTTOM_LEFT", "MID_LEFT"]:
                             slot_name = ["TOP_LEFT", "BOTTOM_LEFT", "MID_LEFT"][i % 3]

                    if slot_name in SECTORS:
                        ov['position'] = {"x": SECTORS[slot_name]["x"], "y": SECTORS[slot_name]["y"]}
                    elif not ov.get('position'):
                         keys = list(SECTORS.keys())
                         selected = keys[i % len(keys)]
                         ov['position'] = {"x": SECTORS[selected]["x"], "y": SECTORS[selected]["y"]}

                    # 2. Collision Nudging (AABB - Axis-Aligned Bounding Box)
                    for attempt in range(5): # Multiple nudges if needed
                        collision_found = False
                        for prev_ov, prev_w, prev_h in placed_overlays:
                            start1, end1 = ov.get('start', 0), ov.get('start', 0) + ov.get('duration', 60)
                            start2, end2 = prev_ov.get('start', 0), prev_ov.get('start', 0) + prev_ov.get('duration', 60)

                            if max(start1, start2) < min(end1, end2):
                                x1, y1 = ov['position']['x'], ov['position']['y']
                                x2, y2 = prev_ov['position']['x'], prev_ov['position']['y']

                                # Check for AABB overlap
                                if abs(x1 - x2) < (w + prev_w) / 2 + 50 and abs(y1 - y2) < (h + prev_h) / 2 + 50:
                                    collision_found = True
                                    # Nudge vertically
                                    if y1 <= y2: ov['position']['y'] = y2 - (h + prev_h) / 2 - 80
                                    else: ov['position']['y'] = y2 + (h + prev_h) / 2 + 80

                                    # If still overlapping, nudge horizontally
                                    if abs(ov['position']['y'] - y2) < (h + prev_h) / 2 + 20:
                                         if x1 <= x2: ov['position']['x'] = x2 - (w + prev_w) / 2 - 80
                                         else: ov['position']['x'] = x2 + (w + prev_w) / 2 + 80
                        if not collision_found: break

                    # 3. Final Rigid Canvas Safety Clamping (150px safety zone)
                    margin = 150
                    # For center-anchored: center must be between (margin + width/2) and (1920 - margin - width/2)
                    x_min, x_max = margin + w/2, 1920 - margin - w/2
                    y_min, y_max = margin + h/2, 1080 - margin - h/2

                    # If component is somehow larger than the safe zone, center it
                    if x_min > x_max: x_min = x_max = 960
                    if y_min > y_max: y_min = y_max = 540

                    ov['position']['x'] = max(x_min, min(x_max, int(ov['position'].get('x', 960))))
                    ov['position']['y'] = max(y_min, min(y_max, int(ov['position'].get('y', 540))))

                    placed_overlays.append((ov, w, h))

                    # Timing Safety & Cinematic Pacing
                    min_duration = 120 if ov_type in ['chart', 'ui_panel', 'data_indicator'] else 60
                    if ov.get('start', 0) >= scene_duration:
                        ov['start'] = max(0, scene_duration - min_duration)

                    if ov.get('duration', 0) < min_duration:
                        ov['duration'] = min_duration

                    if ov.get('start') + ov.get('duration') > scene_duration:
                        # Try to shift start back if possible, otherwise truncate
                        if scene_duration >= min_duration:
                            ov['start'] = max(0, scene_duration - ov['duration'])
                            ov['duration'] = scene_duration - ov['start']
                        else:
                            ov['duration'] = scene_duration - ov['start']

                    # Subtle local SFX (Volume 0.04) - Attached to each overlay
                    if in_files:
                        sfx_manifest.append({ "scene_id": scene['scene_id'], "file": in_files[in_ptr % len(in_files)], "start": ov['start'], "end": ov['start'] + 20, "volume": 0.04 })
                        in_ptr += 1
                    if out_files:
                        sfx_manifest.append({ "scene_id": scene['scene_id'], "file": out_files[out_ptr % len(out_files)], "start": ov['start'] + ov['duration'] - 10, "end": ov['start'] + ov['duration'], "volume": 0.04 })
                        out_ptr += 1

            # 4. Camera Shot Normalization (Resting Time)
            if scene.get('camera') and scene['camera'].get('shots'):
                for shot in scene['camera']['shots']:
                    # Enforce MOVLESS RESTING (duration - inDuration >= 90)
                    target_resting = 90
                    if shot.get('duration', 0) < target_resting + 15:
                        shot['duration'] = max(shot.get('duration', 0), target_resting + 15)

                    max_in = max(15, shot['duration'] - target_resting)
                    shot['inDuration'] = min(shot.get('inDuration', 30), max_in)

        data['audio_sfx_manifest'] = sfx_manifest
        print(f"✅ Finalization: Processed {len(data['scenes'])} scenes, {len(sfx_manifest)} SFX triggers mapped.")
        return data

    def generate_word_timestamps(self, story: str, public_dir: str = "../public") -> str:
        print("🎙️  Generating precise word-level timestamps (30fps normalization)...")
        scenes = re.split(r'দৃশ্য\s+[0-9০-৯]+', story)
        scene_texts = [s.strip() for s in scenes if s.strip()]
        full_ts_prompt = "You are a Voiceover Alignment Expert. Generate EXACT word-level timestamps in FRAMES for a 30fps project.\n\n"

        scene_durations = []
        for i, scene_text in enumerate(scene_texts):
            scene_num = i + 1
            vpath = f"renders/scene_SC_{scene_num:02d}.mp4"
            duration_sec = 6.0
            abs_vpath = os.path.join(public_dir, vpath)
            if os.path.exists(abs_vpath):
                duration_sec, _ = self.probe_video_duration_and_fps(abs_vpath)
            total_frames = int(math.ceil(duration_sec * 30))
            scene_durations.append(total_frames)
            full_ts_prompt += f"--- SCENE {scene_num:02d} (Duration: {total_frames} frames) ---\nVOICEOVER: {scene_text}\n\n"

        full_ts_prompt += "INSTRUCTIONS: Format: SCENE_XX: [Frame Start - Frame End] \"Word\". Ensure 30fps mapping. ALL timestamps MUST be within the [0, Duration] range for each scene. Return ONLY timestamps.\n"
        return self._interact_with_gemini(full_ts_prompt), scene_durations

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
                stop_btn = "button[aria-label*='Stop generating']"

                for i in range(300):
                    time.sleep(1.5)
                    if get_msg_count() <= initial_count: continue

                    # Speed Optimization: If 'Stop generating' button is gone, the response is likely done.
                    is_generating = page.is_visible(stop_btn, timeout=500)

                    current_text = ""
                    for sel in response_selectors:
                        msgs = page.query_selector_all(sel)
                        if msgs:
                            current_text = msgs[-1].inner_text()
                            break

                    if current_text and current_text == last_text:
                        stable_count += 1
                        # If stable and not generating, we can exit much faster
                        if not is_generating and stable_count >= 2:
                             print(f"✨ Gemini response finished ({len(current_text)} chars).")
                             return current_text
                        if stable_count >= 5:
                             print(f"✨ Gemini response stabilized ({len(current_text)} chars).")
                             return current_text
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

    def generate(self, story: str, guidelines: str, prompt_output_path: str = None, timestamp_context: str = None, scene_durations: List[int] = None) -> Dict[str, Any]:
        story = self.adjust_durations_in_text(story)
        guidelines = self.adjust_durations_in_text(guidelines)
        local_fonts = self.get_local_fonts()

        duration_context = ""
        if scene_durations:
             duration_context = "SCENE DURATION LIMITS (30fps Frames):\n"
             for i, d in enumerate(scene_durations):
                  duration_context += f"SCENE {i+1:02d}: {d} frames\n"

        full_prompt = (
            "You are a world-class Cinematic Motion Graphics Director. Your mission is to generate an ULTRA MODERN, TOP-NOTCH, high-fidelity JSON manifest.\n\n"
            "STYLE: High-end sci-fi documentary interface. Think 'Minority Report' meets modern data journalism. Use sleek glassmorphism (ui_panel variant: glass), vibrant technical accents (shape/graph), and high-contrast typography.\n\n"
            "CRITICAL CINEMATIC RULES:\n"
            "1. PROFESSIONAL BALANCED LAYOUT: All overlays MUST use the 'slot' property. Never cluster elements. If a chart is in TOP_RIGHT, text must be in BOTTOM_LEFT or MID_LEFT.\n"
            "2. CINEMATIC PACING (MOVLESS RESTING): This is non-negotiable. Every focal element must have 15f intro, 15f outro, and at least 90-120f of COMPLETELY STATIC RESTING time (no camera zoom/pan, no element movement) to ensure viewer focus.\n"
            "3. AUDIO-VISUAL SYNC: Use the PRECISE word-level timestamps provided. Overlays must appear and disappear EXACTLY with the spoken narrative.\n"
            "4. NO VISUAL CLUTTER: Text content MUST be concise (2-3 words max per overlay). For charts, limit data to a MAXIMUM of 5 points. Do not block background video details.\n"
            "5. FONT ACCURACY (STRICT): For Bengali content, you MUST select a font from the BANGLA FONTS list provided. For English content, you MUST select from the ENGLISH FONTS list. DO NOT use generic font names like 'Inter' or 'Arial' unless they are in the detected list.\n"
            "6. MANDATORY AUDIO & VIDEO: EVERY scene MUST have 'background_type': 'video', 'video_path': 'renders/scene_SC_XX.mp4', and 'audio_enabled': true. This ensures the background video audio is preserved.\n"
            "7. CAMERA WORK: Use 'shots' for every focal overlay. Movements must be professional (slow_push, slow_pull, or dramatic_reveal). Ensure 'inDuration' allows for the required resting time.\n"
            "8. JSON CONSTRAINTS: Be extremely concise. Avoid deep nesting or excessive decorative elements. Keep data arrays short. Ensure NO control characters are present in the text content. **OUTPUT RAW MINIFIED JSON ONLY. DO NOT USE NEWLINES OR INDENTATION.**\n\n"
            f"DETECTED LOCAL FONTS (Categorized): {local_fonts}\n\n"
            f"SYSTEM GUIDELINES (V4 Schema):\n{guidelines}\n\n"
            f"STORY NARRATIVE:\n{story}\n\n"
            f"{duration_context}\n"
            f"PRECISE WORD TIMESTAMPS (FOR SYNCING):\n{timestamp_context or 'No timestamps provided. Estimate based on 30fps.'}\n\n"
            "TASK: Create the complete master blueprint in raw JSON. Ensure all IDs are unique and targeted correctly by the camera."
        )
        if prompt_output_path:
            with open(prompt_output_path, 'w', encoding='utf-8') as f: f.write(full_prompt)
        raw_output = self._interact_with_gemini(full_prompt)
        print(f"📊 Raw Gemini output length: {len(raw_output)} chars.")
        try:
            # 1. Look for markdown code blocks first
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_output, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 2. Fallback to finding first { and last }
                start_idx, end_idx = raw_output.find('{'), raw_output.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_str = raw_output[start_idx:end_idx+1]
                else:
                    # Try to find a partial JSON if it was truncated
                    start_idx = raw_output.find('{')
                    if start_idx != -1:
                        json_str = raw_output[start_idx:]
                    else:
                        print("❌ Could not find any JSON-like structures in Gemini response.")
                        return {}

            # Pre-cleanup: Remove control characters except for standard whitespace
            json_str = "".join(ch for ch in json_str if ch.isprintable() or ch in "\n\r\t")

            # Cleanup comments and common syntax issues
            json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
            json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)

            def repair_json(s):
                s = s.strip()
                stack = []
                in_string = False
                escaped = False

                for char in s:
                    if char == '"' and not escaped:
                        in_string = not in_string
                    if in_string:
                        if char == '\\': escaped = not escaped
                        else: escaped = False
                        continue

                    if char == '{': stack.append('}')
                    elif char == '[': stack.append(']')
                    elif char == '}':
                        if stack and stack[-1] == '}': stack.pop()
                    elif char == ']':
                        if stack and stack[-1] == ']': stack.pop()

                # If we're inside a string at the end, close it
                if in_string:
                    s += '"'

                if stack:
                    s = s.rstrip()
                    # Remove trailing partial key/values
                    # A valid value ends with " or digit or boolean or null or closure
                    while s and s[-1] not in '"0123456789truefalsenull}]':
                        s = s[:-1].rstrip()

                    # If we ended up with a partial key like "key", remove it too
                    if s.endswith('"'):
                         # Find the start of this possible partial key
                         parts = s.rsplit('"', 2)
                         if len(parts) >= 2:
                              # If there's no colon after the second-to-last quote, it's a partial key
                              # But checking this reliably is hard without a full parser.
                              # Just ensure we don't end with a comma.
                              pass

                    if s.endswith(','):
                        s = s[:-1].rstrip()

                    # One more pass to ensure we don't have a partial key at the end
                    # If the last character is a quote, and the one before the previous quote was a comma or brace
                    # it means we have something like ..., "partial_key"
                    if s.endswith('"'):
                        last_quote = s.rfind('"', 0, -1)
                        if last_quote != -1:
                            before_quote = s[:last_quote].rstrip()
                            if not before_quote or before_quote.endswith(',') or before_quote.endswith('{'):
                                s = before_quote

                    if s.endswith(','):
                        s = s[:-1].rstrip()

                    s += "".join(reversed(stack))
                return s

            try:
                # Use strict=False to handle unescaped control characters in strings
                return json.loads(json_str, strict=False)
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON primary parse failed: {e}. Attempting repair...")

                # Try simple trailing comma cleanup
                cleaned = re.sub(r',\s*\}', '}', json_str)
                cleaned = re.sub(r',\s*\]', ']', cleaned)

                try:
                    return json.loads(cleaned, strict=False)
                except:
                    # Final attempt: full structural repair
                    repaired = repair_json(cleaned)
                    try:
                        return json.loads(repaired, strict=False)
                    except Exception as final_e:
                        print(f"❌ JSON repair failed: {final_e}")
                        print(f"--- FAILED JSON START ---\n{json_str[:800]}\n--- FAILED JSON END ---")
                        return {}
        except Exception as e:
            print(f"❌ Fatal error during JSON extraction: {e}")
            return {}

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
        scene_durations = None
        if args.timestamp_output:
            if os.path.exists(args.timestamp_output): os.remove(args.timestamp_output)
            ts_content, scene_durations = maker.generate_word_timestamps(story)
            if not ts_content or len(ts_content) < 50:
                 ts_content, scene_durations = maker.generate_word_timestamps(story)
            with open(args.timestamp_output, 'w', encoding='utf-8') as f: f.write(ts_content)
        render_json = maker.generate(story, guidelines, args.prompt_output, ts_content, scene_durations)
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
