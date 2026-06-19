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
        self.fps_cache = {}

    def load_fps_update(self, filepath: str):
        if not filepath or not os.path.exists(filepath):
            print(f"⚠️ FPS update file not found: {filepath}")
            return

        print(f"📂 Loading FPS data from: {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # Format: scene_SC_01.mp4 | Original FPS: 24.000 | Total Frames: 128 | 30fps Frames: 160
                matches = re.finditer(r'(scene_SC_\d+\.mp4).*?30fps Frames:\s*(\d+)', content)
                count = 0
                for match in matches:
                    filename = match.group(1)
                    frames = int(match.group(2))
                    self.fps_cache[filename] = frames
                    print(f"   🎬 {filename} -> {frames} frames")
                    count += 1
            print(f"✅ Successfully cached {count} durations from manifest.")
        except Exception as e:
            print(f"⚠️ Error loading FPS update file: {e}")

    def start_browser(self):
        if self.page: return
        self.playwright = sync_playwright().start()
        print("🚀 Launching persistent browser...")
        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--single-process",
            "--disable-extensions"
        ]
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

    def _get_ff_tool(self, tool: str) -> List[str]:
        if shutil.which(tool):
            return [tool]
        # Fallback for environments where ffmpeg/ffprobe is bundled with Remotion
        return ["npx", "remotion", tool]

    def probe_video_duration_and_fps(self, video_path: str):
        filename = os.path.basename(video_path)
        if filename in self.fps_cache:
            return float(self.fps_cache[filename]), 30.0

        try:
            # Get video info (exact logic from user request)
            cmd = self._get_ff_tool("ffprobe") + [
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate,avg_frame_rate,nb_frames,duration",
                "-of", "json",
                video_path
            ]
            output = subprocess.check_output(cmd).decode("utf-8")
            data = json.loads(output)

            if not data.get('streams'):
                print(f"⚠️ No streams found in {video_path}")
                return 0.0, 30.0

            stream = data['streams'][0]

            duration = float(stream.get("duration", 0))

            # Original FPS
            fps_str = stream.get("avg_frame_rate", "0/1")
            num, den = map(int, fps_str.split("/"))
            fps = num / den if den else 0

            # Total frames
            nb_frames = stream.get("nb_frames")
            if nb_frames is not None:
                total_frames = int(nb_frames)
            else:
                total_frames = int(round(duration * fps))

            # Frames after converting to 30 FPS (User formula: round(duration * 30))
            frames_at_30fps = int(round(duration * 30))

            # Return frames instead of seconds for the first parameter to satisfy the engine requirement
            return float(frames_at_30fps), 30.0
        except Exception as e:
            print(f"⚠️ Error probing video {video_path}: {e}")
            return 0.0, 30.0

    def adjust_durations_in_text(self, text: str, public_dir: str = "../public") -> str:
        def replacement_logic(match):
            block = match.group(0)
            vpath_match = re.search(r'"video_path":\s*"([^"]+)"', block)
            if vpath_match:
                rel_vpath = vpath_match.group(1)
                filename = os.path.basename(rel_vpath)
                if filename in self.fps_cache:
                    new_duration = int(self.fps_cache[filename])
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
        BANGLA_KEYWORDS = ['solaiman', 'kalpurush', 'nikosh', 'hind', 'siliguri', 'adorsho', 'sutonny', 'shonar', 'vrinda', 'bangla', 'liyakats', 'anshu', 'charukola', 'galada', 'mina', 'mukti', 'atreyee', 'benisen', 'bengali', 'shishir', 'shorif', 'maharaj', '_bangla']

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

        if 'project_name' not in data:
            data['project_name'] = "Counterism_Studio_V4_Automated_Render"

        data['global_settings'] = { "width": 1920, "height": 1080, "fps": 30 }

        abs_public = os.path.abspath(public_dir)
        print(f"🛠️ Finalizing durations using public dir: {abs_public}")

        # Calibrated base sizes for center-anchored overlays
        TYPE_SIZES = {
            'text': (600, 120),
            'chart': (1000, 600),
            'ui_panel': (700, 500),
            'data_indicator': (450, 400),
            'media': (900, 700),
            'image': (900, 700),
            'video': (900, 700)
        }

        # Rigid Minimalist Overlay Budget per Scene
        MAX_TEXT_PER_SCENE = 1
        MAX_FOCAL_PER_SCENE = 1 # Chart/UI/KPI

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

        audio_dir = os.path.abspath(os.path.join(public_dir, "renders/audios"))
        in_files = []
        out_files = []

        print(f"📂 Searching for SFX materials in: {audio_dir}")
        if os.path.exists(audio_dir):
            all_files = os.listdir(audio_dir)
            # More flexible detection: "in_1", "in1", "intro", "enter", etc.
            in_files = sorted([f for f in all_files if re.match(r'^(in[_\-]?\d*|intro|enter)', f, re.I) and f.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg'))])
            out_files = sorted([f for f in all_files if re.match(r'^(out[_\-]?\d*|outro|exit)', f, re.I) and f.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg'))])
            print(f"   🎵 Scanned {len(all_files)} total files in SFX folder.")
            print(f"   🎵 Detected {len(in_files)} entrance sounds: {in_files[:5]}...")
            print(f"   🎵 Detected {len(out_files)} exit sounds: {out_files[:5]}...")
        else:
            print(f"   ⚠️ SFX directory not found at resolved path: {audio_dir}")

        sfx_manifest = []
        in_ptr, out_ptr = 0, 0

        for scene_idx, scene in enumerate(data['scenes']):
            # 1. LLM Fix: Root Level Schema Alignment
            if 'duration' in scene and 'duration_in_frames' not in scene:
                scene['duration_in_frames'] = scene['duration']

            if 'elements' in scene and not scene.get('overlays'):
                scene['overlays'] = scene['elements']

            # LLM Repair: text_overlay / focal_element object patterns
            if not scene.get('overlays'):
                scene['overlays'] = []
                for k in ['text_overlay', 'focal_element', 'overlay']:
                    if k in scene and isinstance(scene[k], dict):
                        obj = scene[k]
                        if k == 'text_overlay': obj['type'] = 'text'
                        scene['overlays'].append(obj)

            if 'background' in scene and isinstance(scene['background'], dict):
                bg = scene['background']
                for k in ['background_type', 'video_path', 'audio_enabled']:
                    if k in bg and k not in scene: scene[k] = bg[k]

            # 2. Strict Background Enforcement
            scene['background_type'] = 'video'
            scene['audio_enabled'] = True
            if not scene.get('video_path'):
                scene['video_path'] = f"renders/scene_SC_{scene_idx+1:02d}.mp4"

            # 3. Authoritative Duration Resolution
            scene_duration = scene.get('duration_in_frames', 180)
            vpath = scene['video_path'].lstrip('/')
            filename = os.path.basename(vpath)
            if filename in self.fps_cache:
                scene_duration = self.fps_cache[filename]

            scene['duration_in_frames'] = scene_duration

            placed_overlays = []
            focal_ids = []

            text_count = 0
            focal_count = 0

            if scene.get('overlays'):
                # First Pass: Budgeting & Schema Alignment
                valid_overlays = []
                for ov in scene['overlays']:
                    # LLM Repair: Map start_frame/end_frame/end
                    if 'start_frame' in ov and 'start' not in ov: ov['start'] = ov['start_frame']

                    if 'duration' not in ov:
                        if 'end_frame' in ov: ov['duration'] = max(60, ov['end_frame'] - ov.get('start', 0))
                        elif 'end' in ov: ov['duration'] = max(60, ov['end'] - ov.get('start', 0))

                    # LLM Repair: ui -> ui_panel, text missing but key present
                    if ov.get('type') == 'ui': ov['type'] = 'ui_panel'
                    if not ov.get('type'):
                        if 'text' in ov or 'content' in ov: ov['type'] = 'text'
                        elif 'chart_type' in ov or 'kind' in ov: ov['type'] = 'chart'

                    ov_type = ov.get('type', 'text')
                    if ov_type == 'text':
                        if text_count >= MAX_TEXT_PER_SCENE: continue
                        text_count += 1
                        # LLM Repair: text -> content
                        if 'text' in ov and 'content' not in ov:
                            ov['content'] = ov['text']
                    elif ov_type in ['chart', 'ui_panel', 'data_indicator']:
                        if focal_count >= MAX_FOCAL_PER_SCENE: continue
                        focal_count += 1

                        # LLM Repair: kind -> indicator_type / chart_type
                        if 'kind' in ov:
                            if ov_type == 'chart' and 'chart_type' not in ov: ov['chart_type'] = ov['kind']
                            if (ov_type == 'ui_panel' or ov_type == 'data_indicator') and 'indicator_type' not in ov:
                                ov['indicator_type'] = ov['kind']

                    # Ensure start/duration exists
                    if 'start' not in ov: ov['start'] = 0
                    if 'duration' not in ov: ov['duration'] = max(120, scene_duration - ov['start'])

                    valid_overlays.append(ov)

                scene['overlays'] = valid_overlays

                for i, ov in enumerate(scene['overlays']):
                    # Ensure ID exists
                    if not ov.get('id'):
                        ov['id'] = f"OV_{scene_idx+1}_{i+1}_{ov.get('type', 'element').upper()}"

                    ov_type = ov.get('type', 'text')
                    if ov_type in ['text', 'chart', 'ui_panel', 'data_indicator']:
                        focal_ids.append(ov['id'])

                    ov_type = ov.get('type', 'text')
                    w, h = TYPE_SIZES.get(ov_type, (800, 800))

                    if ov_type == 'text':
                        # Dynamic Text Footprint Estimation (Viewer Safety Buffers)
                        content = ov.get('content') or ov.get('text', '')
                        lines = content.count('\n') + 1
                        fs_match = re.search(r'(\d+)', ov.get('fontSize', '64'))
                        fs = int(fs_match.group(1)) if fs_match else 64

                        # Bangla characters are wider/taller; scale box accordingly
                        is_bangla = any(ord(c) > 127 for c in content)
                        # Minimalist constraint often results in single lines; use safer width
                        w = min(1500, len(max(content.split('\n'), key=len)) * (fs * (1.0 if is_bangla else 0.8)))
                        h = lines * (fs * (1.8 if is_bangla else 1.5))

                    elif ov_type == 'chart':
                        w = ov.get('width', 1000) + 100
                        h = ov.get('height', 600) + 100

                    # 1. Professional Slot Alignment & De-confliction
                    # Force Text and Charts into opposing quadrants for Minimalist Balance
                    slot_name = ov.get('slot', ov.get('layout', ''))
                    if not isinstance(slot_name, str): slot_name = ''
                    slot_name = slot_name.upper()

                    if ov_type in ['chart', 'ui_panel', 'data_indicator']:
                        if "RIGHT" not in slot_name:
                             slot_name = ["TOP_RIGHT", "BOTTOM_RIGHT", "MID_RIGHT"][i % 3]
                    elif ov_type == 'text':
                        if "LEFT" not in slot_name:
                             slot_name = ["TOP_LEFT", "BOTTOM_LEFT", "MID_LEFT"][i % 3]

                    if slot_name in SECTORS:
                        ov['position'] = {"x": SECTORS[slot_name]["x"], "y": SECTORS[slot_name]["y"]}

                    # LLM Repair: position: "left" or missing position
                    pos = ov.get('position')
                    if not pos or isinstance(pos, str):
                         selected = "MID_LEFT" if ov_type == 'text' else "MID_RIGHT"
                         # Check if the string actually matches a slot or simple side
                         if isinstance(pos, str):
                             p_upper = pos.upper()
                             if p_upper == "LEFT": selected = "MID_LEFT"
                             elif p_upper == "RIGHT": selected = "MID_RIGHT"
                             elif p_upper == "CENTER": selected = "CENTER_FOCAL"
                             elif p_upper in SECTORS: selected = p_upper

                         ov['position'] = {"x": SECTORS[selected]["x"], "y": SECTORS[selected]["y"]}

                    # 2. Multi-Directional Collision Nudging (AABB Multi-Pass)
                    for attempt in range(15):
                        collision_found = False
                        for prev_ov, prev_w, prev_h in placed_overlays:
                            s1, e1 = ov.get('start', 0), ov.get('start', 0) + ov.get('duration', 60)
                            s2, e2 = prev_ov.get('start', 0), prev_ov.get('start', 0) + prev_ov.get('duration', 60)

                            if max(s1, s2) < min(e1, e2):
                                x1, y1 = ov['position']['x'], ov['position']['y']
                                x2, y2 = prev_ov['position']['x'], prev_ov['position']['y']

                                # Overlap check with 50px comfort buffer
                                if abs(x1 - x2) < (w + prev_w) / 2 + 50 and abs(y1 - y2) < (h + prev_h) / 2 + 50:
                                    collision_found = True

                                    # Nudge logic: try vertical first, then horizontal
                                    if abs(y1 - y2) < (h + prev_h) / 2:
                                        # Resolve vertically
                                        if y1 <= y2: ov['position']['y'] = y2 - (h + prev_h) / 2 - 60
                                        else: ov['position']['y'] = y2 + (h + prev_h) / 2 + 60

                                    # Secondary check: if vertical nudge pushed it off-screen, try horizontal
                                    if ov['position']['y'] < 200 or ov['position']['y'] > 880:
                                        ov['position']['y'] = y1 # reset y
                                        if x1 <= x2: ov['position']['x'] = x2 - (w + prev_w) / 2 - 80
                                        else: ov['position']['x'] = x2 + (w + prev_w) / 2 + 80

                                    print(f"   🔧 Nudging {ov['id']} to resolve overlap with {prev_ov['id']} -> New Pos: ({int(ov['position']['x'])}, {int(ov['position']['y'])})")
                        if not collision_found: break

                    # 3. Final Rigid Canvas Safety Clamping (150px safety zone)
                    margin = 150
                    x_min, x_max = margin + w/2, 1920 - margin - w/2
                    y_min, y_max = margin + h/2, 1080 - margin - h/2

                    if x_min > x_max: x_min = x_max = 960
                    if y_min > y_max: y_min = y_max = 540

                    ov['position']['x'] = max(x_min, min(x_max, int(ov.get('position', {}).get('x', 960))))
                    ov['position']['y'] = max(y_min, min(y_max, int(ov.get('position', {}).get('y', 540))))

                    placed_overlays.append((ov, w, h))

                    # 4. Cinematic Pacing (User Mandate)
                    # 15f intro, 15f outro, 90-120f resting
                    intro_frames = 15
                    outro_frames = 15
                    resting_frames = 90 # Min resting

                    target_total = intro_frames + resting_frames + outro_frames # 120f

                    start_f = ov.get('start', 0)
                    if start_f >= scene_duration - 30:
                        start_f = max(0, scene_duration - target_total)

                    # Ensure duration is at least enough for intro+resting+outro
                    duration_f = max(target_total, ov.get('duration', target_total))

                    if start_f + duration_f > scene_duration:
                        duration_f = scene_duration - start_f

                    ov['start'] = start_f
                    ov['duration'] = duration_f

                    # Cleanup hallucinated keys
                    for k in ['intro', 'outro', 'resting']:
                        if k in ov: del ov[k]

                    # Subtle local SFX (Volume 0.04) - Attached to each overlay
                    s_id = scene.get('scene_id', 'unknown')
                    if in_files:
                        sfx_manifest.append({ "scene_id": s_id, "file": in_files[in_ptr % len(in_files)], "start": ov['start'], "end": ov['start'] + 20, "volume": 0.04 })
                        in_ptr += 1
                    if out_files:
                        sfx_manifest.append({ "scene_id": s_id, "file": out_files[out_ptr % len(out_files)], "start": ov['start'] + ov['duration'] - 10, "end": ov['start'] + ov['duration'], "volume": 0.04 })
                        out_ptr += 1

            # 4. Camera Shot Normalization & Auto-Generation
            if not scene.get('camera'):
                scene['camera'] = {
                    "enabled": True,
                    "motionBlur": { "enabled": True, "intensity": 1.0 },
                    "shake": { "enabled": False, "intensity": 1.0 },
                    "shots": []
                }

            if not scene['camera'].get('motionBlur'):
                scene['camera']['motionBlur'] = { "enabled": True, "intensity": 1.0 }

            if not scene['camera'].get('shots') and focal_ids:
                # Auto-generate a basic shot sequence if Gemini missed it
                total_focal = len(focal_ids)
                shot_dur = scene_duration // total_focal
                for i, fid in enumerate(focal_ids):
                    scene['camera']['shots'].append({
                        "targetId": fid,
                        "startFrame": i * shot_dur,
                        "duration": shot_dur,
                        "zoom": 1.2,
                        "style": "slow_push",
                        "inDuration": 30
                    })

            if scene['camera'].get('shots'):
                for shot in scene['camera']['shots']:
                    # LLM Repair: target -> targetId, type -> style
                    if 'target' in shot and 'targetId' not in shot:
                        shot['targetId'] = shot['target']
                    if 'type' in shot and 'style' not in shot:
                        shot['style'] = shot['type']

                    # LLM Repair: start_frame / start / end_frame / end in shots
                    if 'start_frame' in shot and 'startFrame' not in shot: shot['startFrame'] = shot['start_frame']
                    if 'start' in shot and 'startFrame' not in shot: shot['startFrame'] = shot['start']

                    if 'duration' not in shot:
                        if 'end_frame' in shot: shot['duration'] = max(30, shot['end_frame'] - shot.get('startFrame', 0))
                        elif 'end' in shot: shot['duration'] = max(30, shot['end'] - shot.get('startFrame', 0))

                    # Enforce MOVLESS RESTING (duration - inDuration >= 60)
                    target_resting = 60
                    if shot.get('duration', 0) < target_resting + 15:
                        shot['duration'] = max(shot.get('duration', 0), target_resting + 15)

                    max_in = max(15, shot['duration'] - target_resting)
                    shot['inDuration'] = min(shot.get('inDuration', 30), max_in)

        data['audio_sfx_manifest'] = sfx_manifest
        print(f"✅ Finalization: Processed {len(data['scenes'])} scenes, {len(sfx_manifest)} SFX triggers mapped.")
        return data


    def _interact_with_gemini(self, prompt: str, retry_count: int = 2) -> str:
        for attempt in range(retry_count + 1):
            self.start_browser()
            page = self.page
            try:
                response_selectors = ["message-content", ".markdown.message-content", ".model-response-text", "[data-message-author-role='assistant']"]
                def get_msg_count():
                    for sel in response_selectors:
                        try:
                            msgs = page.query_selector_all(sel)
                            if msgs: return len(msgs)
                        except: pass
                    return 0

                initial_count = get_msg_count()

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
                page.keyboard.type(prompt, delay=0) # delay=0 for speed
                page.keyboard.press("Enter")

                try:
                    btn = "button[aria-label*='Send message'], button[aria-label*='Submit']"
                    if page.is_visible(btn, timeout=1000): page.click(btn, force=True)
                except: pass

                print("⏳  Waiting for Gemini JSON response...")
                last_text = ""
                stable_count = 0
                stop_btn = "button[aria-label*='Stop generating']"

                for i in range(600):
                    time.sleep(0.5) # Even faster polling
                    if get_msg_count() <= initial_count: continue

                    try: is_generating = page.locator(stop_btn).is_visible()
                    except: is_generating = False

                    current_text = ""
                    for sel in response_selectors:
                        msgs = page.query_selector_all(sel)
                        if msgs:
                            current_text = msgs[-1].inner_text()
                            break

                    if current_text and current_text == last_text:
                        stable_count += 1
                        # Aggressive early exit if we see the JSON closing brace and it's stable
                        if not is_generating and stable_count >= 3:
                             stripped = current_text.strip()
                             if stripped.endswith("}") or (stripped.endswith("```") and "{" in stripped):
                                 print(f"✨ Gemini response finished ({len(current_text)} chars).")
                                 return current_text

                        if stable_count >= 15:
                             print(f"✨ Gemini response stabilized ({len(current_text)} chars).")
                             return current_text
                    else:
                        stable_count = 0
                        last_text = current_text

                print("🔄  Reloading Gemini...")
                page.reload(wait_until="domcontentloaded")
                time.sleep(3)
            except Exception as e:
                print(f"⚠️ Error in Gemini interaction: {e}")
                try: page.reload(wait_until="domcontentloaded")
                except: pass
                time.sleep(3)
        return ""

    def _compact_timestamps(self, ts_content: str) -> str:
        if not ts_content: return ""
        compacted = []
        # SCENE_01: [Original: 0.00s - 0.98s] -> [30fps: 0f - 29f] "ঢাকা।"
        pattern = r'(SCENE_\d+):.*?\[30fps:\s*(\d+)f\s*-\s*\d+f\]\s*"(.*?)"'
        for line in ts_content.split('\n'):
            match = re.search(pattern, line)
            if match:
                compacted.append(f"{match.group(1)}:{match.group(2)}f \"{match.group(3)}\"")
        return " | ".join(compacted)

    def generate(self, story: str, guidelines: str, prompt_output_path: str = None, timestamp_context: str = None, scene_durations: List[int] = None) -> Dict[str, Any]:
        story = self.adjust_durations_in_text(story)
        local_fonts = self.get_local_fonts()
        compact_ts = self._compact_timestamps(timestamp_context)

        duration_context = "DURATIONS (30fps): " + ", ".join([f"SCENE_{i+1:02d}:{d}f" for i, d in enumerate(scene_durations)]) if scene_durations else ""

        print("\n📝 --- PROMPT CONTEXT ---")
        print(f"   ⏱️ {duration_context}")
        print(f"   🎙️ TIMESTAMPS: {compact_ts[:200]}..." if len(compact_ts) > 200 else f"   🎙️ TIMESTAMPS: {compact_ts}")

        # Condense guidelines for speed while keeping schema
        condensed_guidelines = re.sub(r'\n\s*\n', '\n', guidelines)
        condensed_guidelines = condensed_guidelines[:3000] # Cap to prevent token overflow

        # Single-scene reference to ground the LLM
        schema_ref = (
            '{"scenes":[{"scene_id":"SCENE_01","duration":150,"background_type":"video","video_path":"renders/scene_SC_01.mp4","audio_enabled":true,'
            '"overlays":[{"id":"txt_1","type":"text","content":"MINDSET","start":15,"duration":120,"position":{"x":480,"y":540}},'
            '{"id":"chart_1","type":"chart","chart_type":"bar","start":30,"duration":100,"position":{"x":1440,"y":540}}],'
            '"camera":{"enabled":true,"shots":[{"targetId":"chart_1","style":"slow_push","startFrame":30,"duration":100}]}}]}'
        )

        full_prompt = (
            "YOU ARE A REMOTION MASTER ENGINE. GENERATE RAW MINIFIED JSON ONLY. START '{' END '}'.\n"
            "CRITICAL SCHEMA RULES (NEVER BREAK THESE):\n"
            "- USE 'overlays' list. NEVER use 'elements' or 'text_overlay' objects.\n"
            "- USE 'content' for text strings. NEVER use 'text'.\n"
            "- USE 'chart_type' or 'indicator_type'. NEVER use 'kind'.\n"
            "- USE 'start' and 'duration' (integers). NEVER use 'start_frame' or 'end_frame'.\n"
            "- USE flat keys for background: 'background_type', 'video_path', 'audio_enabled'. NO 'background' object.\n"
            "DESIGN RULES:\n"
            "1. MINIMALISM: Max 1 text overlay + 1 focal element per scene. NEVER crowd the screen.\n"
            "2. TEXT: 3-4 words max. Capture 'vibe', NOT subtitles. Sync 'start' to the word's StartFrame from TIMESTAMPS.\n"
            "3. VIDEO: background_type: 'video' is MANDATORY. video_path must be 'renders/scene_SC_XX.mp4'.\n"
            "4. CAMERA: Every scene must have 'camera' with 'shots' targeting 'targetId'. Use 'style'.\n"
            f"REFERENCE_SCHEMA: {schema_ref}\n"
            f"FONTS: {local_fonts}\n"
            f"DURATIONS: {duration_context}\n"
            f"TIMESTAMPS: {compact_ts}\n"
            f"STORY: {story}\n"
            f"SCHEMA: {condensed_guidelines}\n"
            "TASK: Create a clean MASTER manifest. 100% strict schema adherence. Double-check all closing quotes."
        )
        if prompt_output_path:
            with open(prompt_output_path, 'w', encoding='utf-8') as f: f.write(full_prompt)
        raw_output = self._interact_with_gemini(full_prompt)
        print(f"📊 Raw Gemini output length: {len(raw_output)} chars.")
        if len(raw_output.strip()) < 50:
            print("❌ ERROR: Gemini returned an suspiciously short or empty response.")
            return {}

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
                # Pass 1: Fix "swallowed quotes" like "id":"val,"next"
                s = re.sub(r'":\s*"([^"]+),\s*"', r'":"\1","', s)
                s = re.sub(r'":\s*"([^"]+)\s*\}', r'":"\1"}', s)
                # Pass 2: Fix numeric artifacts in strings like "start": 30f
                s = re.sub(r'":\s*(\d+)[fs]\b', r'": \1', s)
                # Pass 3: Quotes after numbers or booleans (e.g., 214" or true")
                s = re.sub(r'(:[ ]*(\d+|true|false|null))"(\s*[,}\]])', r'\1\3', s)

                # Pass 4: Structural backtracking
                for i in range(len(s), 0, -1):
                    try:
                        chunk = s[:i].strip()
                        if not chunk: continue

                        # Fix unbalanced string quotes
                        if chunk.count('"') % 2 != 0: chunk += '"'

                        # Re-calculate stack for current state
                        stack = []
                        in_string = False
                        escaped = False
                        for char in chunk:
                            if char == '"' and not escaped: in_string = not in_string
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

                        candidate = chunk + "".join(reversed(stack))
                        candidate = re.sub(r',\s*([}\]])', r'\1', candidate)
                        return json.loads(candidate, strict=False)
                    except:
                        continue
                return None

            try:
                # Use strict=False to handle unescaped control characters
                return json.loads(json_str, strict=False)
            except Exception as e:
                print(f"⚠️ JSON primary parse failed. Attempting repair...")
                result = repair_json(json_str)
                if result:
                    return result
                print(f"❌ JSON repair failed.")
                return {}
        except Exception as e:
            print(f"❌ Fatal error during JSON extraction: {e}")
            return {}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--story-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timestamp-output") # Deprecated in favor of --timestamp-file
    parser.add_argument("--timestamp-file")
    parser.add_argument("--fps-update-file")
    parser.add_argument("--prompt-output")
    parser.add_argument("--user-data-dir")
    parser.add_argument("--no-headless", action="store_false", dest="headless")
    parser.add_argument("--drive-prompt")
    parser.add_argument("--public-dir", default="../public")
    parser.set_defaults(headless=True)
    args = parser.parse_args()
    if not os.path.exists(args.story_file): exit(1)
    if os.path.exists(args.output): os.remove(args.output)
    with open(args.story_file, 'r', encoding='utf-8') as f: story = f.read()
    maker = RemotionJsonMaker(user_data_dir=args.user_data_dir, headless=args.headless)

    if args.fps_update_file:
        maker.load_fps_update(args.fps_update_file)

    # Use absolute paths where possible
    abs_public = os.path.abspath(args.public_dir)
    guidelines = maker.load_guidelines(
        os.path.join(os.path.dirname(abs_public), "guideline.md"),
        os.path.join(os.path.dirname(abs_public), "guideline_prompt.txt"),
        args.drive_prompt
    )

    try:
        ts_content = None
        scene_durations = []

        # 1. Handle Scene Durations from fps_update_file
        if maker.fps_cache:
            for i in range(1, 100): # Scan up to 99 scenes
                vname = f"scene_SC_{i:02d}.mp4"
                if vname in maker.fps_cache:
                    scene_durations.append(maker.fps_cache[vname])
                else:
                    break

        # 2. Handle Word Timestamps
        if args.timestamp_file and os.path.exists(args.timestamp_file):
            print(f"📂 Loading external timestamps from: {args.timestamp_file}")
            with open(args.timestamp_file, 'r', encoding='utf-8') as f:
                ts_content = f.read()
        elif args.timestamp_output:
             print("⚠️ Warning: --timestamp-output is deprecated. Please provide --timestamp-file.")

        render_json = maker.generate(story, guidelines, args.prompt_output, ts_content, scene_durations)
        maker.stop_browser()

        if not render_json:
             print("❌ ERROR: Gemini failed to produce any JSON.")
             exit(1)

        if 'scenes' not in render_json or not render_json['scenes']:
             print("❌ ERROR: Generated JSON contains no scenes. Manifest is invalid.")
             print(f"DEBUG: Keys found in JSON: {list(render_json.keys())}")
             exit(1)

        render_json = maker.finalize_json_durations(render_json, public_dir=abs_public)
        output_dir = os.path.dirname(args.output)
        if not os.path.exists(output_dir): os.makedirs(output_dir, exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(render_json, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        print(f"✅ Master JSON created: {args.output} ({os.path.getsize(args.output)} bytes)")

        # Disclosure generation
        disclosure_path = os.path.join(os.path.dirname(args.output), "gemini_disclosure.txt")
        try:
            # We copy the local disclosure to the output manifest directory
            local_disclosure = os.path.join(os.path.dirname(__file__), "gemini_disclosure.txt")
            if os.path.exists(local_disclosure):
                shutil.copy(local_disclosure, disclosure_path)
                print(f"📄 Full Disclosure created at: {disclosure_path}")
        except Exception as de:
            print(f"⚠️ Could not create disclosure file: {de}")

        try: shutil.copy(args.output, "/content/remotion_render.json")
        except: pass
    except Exception as e:
        print(f"❌ Error in main: {e}")
        exit(1)
if __name__ == "__main__": main()
