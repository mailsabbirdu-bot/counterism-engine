import os
import sys
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
    def __init__(self, user_data_dir: str = None, headless: bool = True, manual: bool = False):
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.manual = manual
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.fps_cache = {}
        self.bangla_fonts = []
        self.english_fonts = []
        self.in_files = []
        self.out_files = []
        self.camera_files = []
        self.narration_files = []
        self.video_files = []
        self.raw_timestamps = ""
        self.story_scenes = {}

    def load_fps_update(self, filepath: str):
        if not filepath or not os.path.exists(filepath):
            print(f"⚠️ FPS update file not found: {filepath}")
            return

        print(f"📂 Loading FPS data from: {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = re.finditer(r'(scene_SC_\d+\.mp4).*?30fps Frames:\s*(\d+)', content)
                count = 0
                for match in matches:
                    filename = match.group(1)
                    frames = int(match.group(2))
                    self.fps_cache[filename] = frames
                    print(f"   🎬 {filename} -> {frames} frames")
                    count += 1
            print(f"✅ Successfully cached {count} durations.")
        except Exception as e:
            print(f"⚠️ Error loading FPS update file: {e}")

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
        try:
            self.page.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"⚠️ Gemini loading warning: {e}")

    def stop_browser(self):
        if self.context: self.context.close()
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()
        self.page = None

    def scan_assets(self, public_dir: str = "../public"):
        abs_public = os.path.abspath(public_dir)
        fonts_dir = os.path.join(abs_public, "fonts")
        self.bangla_fonts = []
        self.english_fonts = []
        BANGLA_KEYWORDS = ['solaiman', 'kalpurush', 'nikosh', 'hind', 'siliguri', 'adorsho', 'sutonny', 'shonar', 'vrinda', 'bangla', 'liyakats', 'anshu', 'charukola', 'galada', 'mina', 'mukti', 'atreyee', 'benisen', 'bengali', 'shishir', 'shorif', 'maharaj', '_bangla']

        if os.path.exists(fonts_dir):
            for root, dirs, files in os.walk(fonts_dir, followlinks=True):
                for file in files:
                    if file.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
                        name = os.path.splitext(file)[0]
                        clean_name = re.sub(r'-(Regular|Bold|Italic|Light|Medium|Thin|SemiBold|ExtraBold|Black)$', '', name, flags=re.IGNORECASE)
                        if any(kw in clean_name.lower() for kw in BANGLA_KEYWORDS): self.bangla_fonts.append(clean_name)
                        else: self.english_fonts.append(clean_name)
        self.bangla_fonts = sorted(list(set(self.bangla_fonts)))
        self.english_fonts = sorted(list(set(self.english_fonts)))

        audio_dir = os.path.join(abs_public, "renders/audios")
        self.in_files, self.out_files, self.camera_files, self.narration_files = [], [], [], []
        if os.path.exists(audio_dir):
            all_f = os.listdir(audio_dir)
            self.in_files = sorted([f for f in all_f if re.match(r'^(in|intro|enter)', f, re.I)])
            self.out_files = sorted([f for f in all_f if re.match(r'^(out|outro|exit)', f, re.I)])
            self.camera_files = sorted([f for f in all_f if re.match(r'^camera', f, re.I)])
            self.narration_files = sorted([f for f in all_f if re.match(r'^SC_\d+', f, re.I)])

        video_dir = os.path.join(abs_public, "renders")
        self.video_files = sorted([f for f in os.listdir(video_dir) if f.lower().endswith('.mp4')]) if os.path.exists(video_dir) else []

    def finalize_json_durations(self, data: Dict[str, Any], public_dir: str = "../public") -> Dict[str, Any]:
        """Hardens layout, timing, camera, and assets with Geometry-Aware Logic and Adaptive Scaling."""
        if not data or not data.get('scenes'): return data

        abs_public = os.path.abspath(public_dir)
        print(f"🛠️ HARDENING ENGINE: Resolving spatial collisions and cinematic timing...")

        # Studio V4 Hardened Sizes (Synced with QA Logic)
        TYPE_SIZES = {
            'text': (800, 200), 'chart': (1000, 600), 'shadcn_chart': (1000, 600),
            'ui_panel': (800, 600), 'data_indicator': (500, 450), 'shadcn_indicator': (500, 450),
            'svg': (400, 400), 'kpi': (450, 400), 'timeline': (1200, 300),
            'hub_network': (900, 900), 'flow_diagram': (1000, 450), 'process': (1000, 450),
            'media': (900, 700), 'image': (900, 700), 'video': (900, 700),
            'label': (300, 100), 'callout': (400, 200), 'composition': (1200, 800), 'groups': (1200, 800),
            'graph': (1000, 700), 'shape': (600, 600)
        }

        # Hard Constraints (Synced with QA MIN_CONSTRAINTS)
        MIN_FONT_SIZE = 40
        MIN_CHART_W, MIN_CHART_H = 300, 200
        MIN_SVG_W, MIN_SVG_H = 100, 100
        MIN_SPACING = 30

        LAYOUT_PRESETS = ["SPLIT_SCREEN", "RULE_OF_THIRDS", "HERO_FOCAL", "TOP_TITLE_LOWER_VIS"]
        MODERN_COLORS = ["#00F5FF", "#FF3E6C", "#00FFAB", "#ADFF2F", "#FFD700", "#7B68EE", "#FF8C00"]
        VALID_TEXT_ANIMS = ["glow_pulse", "neon_flicker", "glitch_pop", "bounce_pop", "word_by_word", "slide_up", "typewriter"]

        # Ultra-High End 9-Sector Anchors (1920x1080)
        # Studio V4 Hardened Cinematic Anchors
        ANCHORS = {
            "L_TOP": (550, 320), "C_TOP": (960, 320), "R_TOP": (1370, 320),
            "L_MID": (550, 540), "C_MID": (960, 540), "R_MID": (1370, 540),
            "L_BOT": (550, 760), "C_BOT": (960, 760), "R_BOT": (1370, 760)
        }

        # Hard boundaries for strict clamping (QA 150px safe zone)
        CLAMP_MIN_X, CLAMP_MAX_X = 150, 1770
        CLAMP_MIN_Y, CLAMP_MAX_Y = 150, 930

        PRIORITY = {
            'text': 100,
            'data_indicator': 80, 'kpi': 80, 'shadcn_indicator': 80,
            'chart': 70, 'shadcn_chart': 70,
            'ui_panel': 60,
            'svg': 20,
            'graph': 20,
            'shape': 20
        }

        sfx_manifest = []
        in_ptr, out_ptr, cam_ptr = 0, 0, 0

        for scene_idx, scene in enumerate(data['scenes']):
            s_id = scene.get('scene_id', f"SCENE_{scene_idx+1}")
            print(f"   🎬 Processing: {s_id}")

            if 'duration' in scene and 'duration_in_frames' not in scene: scene['duration_in_frames'] = scene['duration']
            raw_dur = scene.get('duration_in_frames', 180)
            scene_duration = int(raw_dur * 30) if (isinstance(raw_dur, (float, int)) and raw_dur < 60) else int(raw_dur)

            id_num_match = re.search(r'(\d+)', s_id)
            id_num = int(id_num_match.group(1)) if id_num_match else (scene_idx + 1)

            if not scene.get('background_type'): scene['background_type'] = 'video'
            if scene['background_type'] == 'video':
                if not scene.get('video_path'):
                    vname = f"scene_SC_{id_num:02d}.mp4"
                    if vname in self.video_files: scene['video_path'] = f"renders/{vname}"
                    else: scene['background_type'] = 'procedural'
                elif not str(scene['video_path']).startswith('renders/'):
                    scene['video_path'] = f"renders/{os.path.basename(scene['video_path'])}"
            if scene['background_type'] == 'procedural':
                if not scene.get('procedural_config') or not isinstance(scene.get('procedural_config'), dict):
                    scene['procedural_config'] = {"variant": "neon_grid"}
                scene['video_path'] = None

            filename = os.path.basename(str(scene.get('video_path', '')))
            if filename in self.fps_cache: scene_duration = self.fps_cache[filename]
            scene['duration_in_frames'] = scene_duration

            # Preserve AI audio intent, default to True if not specified
            if 'audio_enabled' not in scene:
                scene['audio_enabled'] = True

            pattern = f"SC_{id_num:02d}".lower()
            narration_file = next((f for f in self.narration_files if pattern in f.lower()), None)
            if narration_file:
                sfx_manifest.append({"scene_id": s_id, "file": narration_file, "start": 0, "end": scene_duration, "volume": 1.0})

            if not scene.get('overlays'):
                for k in ['elements', 'layers', 'visuals']:
                    if scene.get(k) and isinstance(scene[k], list): scene['overlays'] = scene[k]; break
            if not scene.get('overlays'): scene['overlays'] = []

            valid_overlays = []
            text_count, focal_count = 0, 0
            is_scene_bangla = self._is_bangla(self.story_scenes.get(s_id, ""))

            raw_overlays = scene['overlays'] if isinstance(scene['overlays'], list) else [scene['overlays']]
            processed_raw = []

            # Progressive Information Staging: Semantic pass
            for ov in raw_overlays:
                processed_raw.append(ov)

            for ov in processed_raw:
                o_type = str(ov.get('type', 'text')).lower()
                if 'chart_type' in ov: o_type = 'shadcn_chart'
                if 'indicator_type' in ov: o_type = 'shadcn_indicator'

                if o_type == 'text':
                    text_count += 1
                    content = str(ov.get('content', ov.get('text', ''))).strip()
                    if not content:
                        story_text = self.story_scenes.get(s_id, "")
                        content = " ".join(story_text.split()[:6]) if story_text else "STUDIO V4"
                    ov['content'] = content
                    ov['type'] = 'text'
                else:
                    focal_count += 1

                if not ov.get('id'): ov['id'] = f"ov_{id_num}_{len(valid_overlays)+1}"

                ai_font = ov.get('font')
                all_scanned_fonts = self.bangla_fonts + self.english_fonts

                if ai_font and ai_font in all_scanned_fonts:
                    pass # Keep AI font
                elif (self._is_bangla(str(ov.get('content', ''))) or is_scene_bangla) and self.bangla_fonts:
                    ov['font'] = "Sohid_bangla" if "Sohid_bangla" in self.bangla_fonts else self.bangla_fonts[0]
                elif not ov.get('font') or ov.get('font') not in all_scanned_fonts:
                    ov['font'] = self.english_fonts[0] if self.english_fonts else "Arial"

                if ov['type'] == 'text':
                    if not ov.get('hero_config'):
                        hero = self._get_scene_hero_word(s_id, ov['content'], scene_duration)
                        if not hero: hero = self._get_fallback_hero(ov['content'])
                        if hero:
                            ov['hero_config'] = {"word": hero['word'], "start": hero['start'], "color": MODERN_COLORS[(scene_idx + 2) % len(MODERN_COLORS)], "animation": VALID_TEXT_ANIMS[scene_idx % len(VALID_TEXT_ANIMS)]}

                    ov['color'] = MODERN_COLORS[scene_idx % len(MODERN_COLORS)]
                    ov['fontSize'] = ov.get('fontSize', "120px")
                valid_overlays.append(ov)

            # Spatial and timing pass with Priority-Based Iterative Resolution
            # Sort valid_overlays by priority (Descending)
            valid_overlays.sort(key=lambda o: PRIORITY.get(str(o.get('type')).lower(), 0), reverse=True)

            placed_boxes = []
            # Calculate dynamic stagger to ensure all elements fit in time
            stagger_step = min(30, max(10, scene_duration // (len(valid_overlays) + 2)))

            for i, ov in enumerate(valid_overlays):
                o_type = str(ov.get('type', 'text')).lower()
                ov['start'] = 15 + i * stagger_step
                ov['duration'] = max(30, scene_duration - ov['start'])

                base_w, base_h = TYPE_SIZES.get(o_type, (600, 400))
                fs = 120
                if o_type == 'text':
                    fs_match = re.search(r'\d+', str(ov.get('fontSize', '120')))
                    fs = int(fs_match.group()) if fs_match else 120

                # Use AI position as starting anchor
                pos = ov.get('position', {})
                ax, ay = int(pos.get('x', 960)), int(pos.get('y', 540))

                found = False
                best_pos = (ax, ay)
                final_w, final_h = base_w, base_h

                print(f"     🔍 Placing {ov['id']} ({o_type}) starting at ({ax}, {ay})...")
                for scale_step in range(7):
                    scale = 1.0 - (scale_step * 0.15)

                    # Protect Hero and Locked elements from downscaling
                    if ov.get('importance') == 'hero' or ov.get('locked') is True:
                        scale = 1.0

                    if o_type == 'text':
                        curr_fs = max(MIN_FONT_SIZE, int(fs * scale))
                        # Improved width calculation for multi-line text
                        lines = ov['content'].split('\n')
                        max_line_len = max(len(line) for line in lines) if lines else 0
                        w = min(1600, max_line_len * curr_fs * 0.8)
                        h = curr_fs * 1.2 * len(lines)
                    else:
                        w = max(MIN_CHART_W if 'chart' in o_type else MIN_SVG_W, base_w * scale)
                        h = max(MIN_CHART_H if 'chart' in o_type else MIN_SVG_H, base_h * scale)

                    for step in range(0, 60): # Spiral search from AI position
                        radius = step * 20 # Smaller step size for better precision
                        # Prioritize horizontal and vertical axes to maintain intentional split-screen/rule-of-thirds
                        angles = [0, 180, 90, 270, 45, 135, 225, 315] if radius > 0 else [0]
                        for angle in angles:
                            rad = math.radians(angle)
                            cx, cy = ax + radius * math.cos(rad), ay + radius * math.sin(rad)

                            l, t, r, b = cx-w/2, cy-h/2, cx+w/2, cy+h/2

                            # Clamping to frame + safe zone
                            if l < CLAMP_MIN_X or r > CLAMP_MAX_X or t < CLAMP_MIN_Y or b > CLAMP_MAX_Y: continue

                            collision = False
                            for p_id, p_l, p_t, p_r, p_b, p_s, p_e, p_type in placed_boxes:
                                if max(ov['start'], p_s) < min(ov['start']+ov['duration'], p_e):
                                    # Allow intentional background layering (Hero/KPI/Chart can overlap Graph/Shape)
                                    if (o_type in ['graph', 'shape'] or p_type in ['graph', 'shape']):
                                        continue

                                    gap = MIN_SPACING
                                    if not (r + gap < p_l or l - gap > p_r or b + gap < p_t or t - gap > p_b):
                                        collision = True; break
                            if not collision:
                                best_pos, found = (cx, cy), True
                                if scale < 1.0:
                                    print(f"   📉 Scaling down {ov['id']} to {int(scale*100)}% to fit.")
                                    if o_type == 'text': ov['fontSize'] = f"{int(curr_fs)}px"
                                    else:
                                        ov['width'] = int(w)
                                        ov['height'] = int(h)
                                if radius > 0: print(f"   🔧 Nudging {ov['id']} to ({int(cx)}, {int(cy)}) to resolve collision.")

                                final_w = w if o_type != 'text' else min(1600, len(ov['content']) * int(curr_fs) * 0.7)
                                final_h = h if o_type != 'text' else int(curr_fs) * 1.5
                                break
                        if found: break
                    if found: break

                ov['position'] = {"x": int(best_pos[0]), "y": int(best_pos[1])}

                # High-End Synchronization: Clamp hero start to follow overlay entry
                if ov.get('hero_config'):
                    h_start = ov['hero_config'].get('start', 0)
                    ov['hero_config']['start'] = max(ov['start'] + 10, h_start)

                placed_boxes.append((ov['id'], best_pos[0]-final_w/2, best_pos[1]-final_h/2, best_pos[0]+final_w/2, best_pos[1]+final_h/2, ov['start'], ov['start']+ov['duration'], o_type))

            scene['overlays'] = valid_overlays

            # Camera logic: Preserve AI intent if valid, else fallback
            valid_ids = [o['id'] for o in valid_overlays]
            ai_camera = scene.get('camera', {})
            ai_shots = ai_camera.get('shots', [])

            camera_valid = False
            if ai_shots and isinstance(ai_shots, list):
                # Validate that all shots have valid targetIds
                if all(isinstance(shot, dict) and shot.get('targetId') in valid_ids for shot in ai_shots):
                    camera_valid = True

            if not camera_valid:
                print(f"   🎥 Generating fallback camera for {s_id}")
                CAM_STYLES = ["cinematic_drift", "slow_push", "pan_right", "orbit", "rack_focus", "dramatic_reveal"]

                # Sort valid overlays by priority for fallback target selection
                priority_targets = sorted(valid_overlays, key=lambda o: PRIORITY.get(str(o.get('type')).lower(), 0), reverse=True)
                target_ids = [o['id'] for o in priority_targets]

                if target_ids:
                    if len(target_ids) >= 2:
                        scene['camera'] = {"enabled": True, "shots": [
                            {"targetId": target_ids[0], "startFrame": 0, "duration": scene_duration//2, "style": CAM_STYLES[scene_idx % len(CAM_STYLES)], "zoom": 1.1, "inDuration": 15},
                            {"targetId": target_ids[1], "startFrame": scene_duration//2, "duration": scene_duration - (scene_duration//2), "style": CAM_STYLES[(scene_idx + 1) % len(CAM_STYLES)], "zoom": 1.2, "inDuration": 30}
                        ]}
                    else:
                        scene['camera'] = {"enabled": True, "shots": [{"targetId": target_ids[0], "startFrame": 0, "duration": scene_duration, "style": "slow_push", "zoom": 1.15, "inDuration": 20}]}
            else:
                print(f"   🎥 Preserving AI Camera for {s_id}")
                # Strictly preserve AI shots and styles
                scene['camera']['enabled'] = True
                # Ensure all preserved shots have essential defaults if missing
                for shot in scene['camera'].get('shots', []):
                    if 'style' not in shot: shot['style'] = 'slow_push'
                    if 'zoom' not in shot: shot['zoom'] = 1.15
                    if 'inDuration' not in shot: shot['inDuration'] = 20

            # SFX (Perfectly Aligned with Overlay Entry)
            for i, ov in enumerate(valid_overlays):
                if self.in_files:
                    sfx_manifest.append({"scene_id": s_id, "file": self.in_files[(in_ptr+i)%len(self.in_files)], "start": ov['start'], "end": ov['start']+30, "volume": 0.05})
            in_ptr += len(valid_overlays)

        data['audio_sfx_manifest'] = sfx_manifest
        return data

    def _get_scene_hero_word(self, scene_id: str, overlay_content: str, scene_duration: int = 180):
        if not self.raw_timestamps or not overlay_content: return None
        matches = re.findall(fr'{scene_id}:.*?\[30fps:\s*(\d+)f\s*-\s*\d+f\]\s*"(.*?)"', self.raw_timestamps)
        if not matches: return None
        content_words = re.sub(r'[.।]', '', overlay_content).split()
        candidates = [{"word": w, "start": int(f)} for f, w in matches if re.sub(r'[.।]', '', w) in content_words]
        if not candidates: return None
        hero = max(candidates, key=lambda x: len(x['word']))
        hero['start'] = max(30, min(hero['start'], scene_duration - 60))
        return hero

    def _get_fallback_hero(self, overlay_content: str):
        words = re.sub(r'[.।]', '', str(overlay_content)).split()
        return {"word": max(words, key=len), "start": 45} if words else None

    def _interact_with_gemini(self, prompt: str) -> str:
        if self.manual:
            try:
                from google.colab import output
                import uuid
                u_id = uuid.uuid4().hex[:8]
                safe_prompt = json.dumps(prompt)
                js_code = f"""
                    (async () => {{
                        const u_id = "{u_id}";
                        const container = document.createElement('div');
                        container.style = "background: #111; color: #fff; padding: 20px; border-radius: 12px; border: 2px solid #4CAF50; font-family: monospace; max-width: 800px; margin: 20px auto;";
                        container.innerHTML = `
                            <h3 style="color: #4CAF50; margin-top: 0;">🎬 Studio V4 Pipeline</h3>
                            <button id="copy-${{u_id}}" style="background: #4CAF50; color: #000; border: none; padding: 10px; border-radius: 4px; cursor: pointer; font-weight: bold; width: 100%;">📋 COPY PROMPT</button>
                            <textarea id="paste-${{u_id}}" style="width: 100%; height: 200px; background: #000; color: #00FFAB; border: 1px solid #333; margin-top: 15px; padding: 10px;" placeholder="Paste JSON here..."></textarea>
                            <button id="submit-${{u_id}}" style="background: #2196F3; color: #fff; border: none; padding: 12px; border-radius: 4px; cursor: pointer; font-weight: bold; width: 100%; margin-top: 10px;">🚀 SUBMIT</button>
                        `;
                        document.body.appendChild(container);
                        document.getElementById('copy-'+u_id).onclick = () => {{ navigator.clipboard.writeText({safe_prompt}); document.getElementById('copy-'+u_id).innerText = "COPIED!"; }};
                        return new Promise((resolve) => {{
                            document.getElementById('submit-'+u_id).onclick = () => {{ const val = document.getElementById('paste-'+u_id).value; container.remove(); resolve(val); }};
                        }});
                    }})();
                """
                return output.eval_js(js_code)
            except: return input("Paste Gemini JSON: ")
        return ""

    def _to_eng_digit(self, s: str) -> str:
        return s.translate(str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789'))

    def _compact_timestamps(self, ts_content: str) -> str:
        self.raw_timestamps = ts_content
        if not ts_content: return ""
        matches = re.findall(r'(SCENE_\d+):.*?\[30fps:\s*(\d+)f\s*-\s*\d+f\]\s*"(.*?)"', ts_content)
        return " | ".join([f"{m[0]}:{m[1]}f \"{m[2]}\"" for m in matches])

    def _get_word_timestamp(self, scene_id: str, search_text: str) -> int:
        if not self.raw_timestamps or not search_text: return -1
        words = [re.sub(r'[^\w\u0980-\u09FF]', '', w).lower() for w in str(search_text).split() if len(w) > 1]
        if not words: return -1
        matches = re.findall(fr'{scene_id}:(?:.*?\[30fps:\s*)?(\d+)f\s*(?:-\s*\d+f\]\s*)?"(.*?)"', self.raw_timestamps)
        for f, w in matches:
            wc = re.sub(r'[^\w\u0980-\u09FF]', '', w).lower()
            if wc == words[0] or (len(wc) > 3 and wc in words[0]): return int(f)
        return -1

    def _is_bangla(self, text: str) -> bool:
        return any('\u0980' <= c <= '\u09FF' for c in str(text))

    def generate(self, story: str, prompt_output_path: str = None, timestamp_context: str = None, scene_durations: List[int] = None, drive_prompt_path: str = None) -> Dict[str, Any]:
        pattern = r'(?:Scene|দৃশ্য)\s+[0-9০-৯]+[:\s]*'
        story_parts = [p.strip().lstrip(':').strip() for p in re.split(pattern, story) if p.strip()]
        for i, n in enumerate(story_parts, 1): self.story_scenes[f"SCENE_{i:02d}"] = n

        compact_ts = self._compact_timestamps(timestamp_context)
        duration_context = ", ".join([f"SCENE_{i+1:02d}:{d}f" for i, d in enumerate(scene_durations)]) if scene_durations else ""

        drive_guideline = ""
        if drive_prompt_path and os.path.exists(drive_prompt_path):
            try:
                with open(drive_prompt_path, 'r', encoding='utf-8') as f:
                    drive_guideline = f"\n--- DIRECTOR'S GUIDELINES ---\n{f.read()}\n"
            except: pass

        full_prompt = (
            f"TASK: GENERATE AN EXPERT DOCUMENTARY MOTION GRAPHICS MANIFEST FOR {len(self.story_scenes)} SCENES.\n"
            f"STORY: {story}\nTIMESTAMPS: {compact_ts}\nDURATIONS: {duration_context}\n"
            f"{drive_guideline}"
            "SYSTEM: WORLD-CLASS MOTION GRAPHICS DIRECTOR PERSONA MANDATORY.\n"
            "DIRECTOR'S RULES (STRICT COMPLIANCE REQUIRED):\n"
            "1. ELIMINATE COLLISIONS: Absolutely NO center-stacking (960, 540) or (960, 700). Use 9-Sector Layout (L/C/R x T/M/B).\n"
            "2. CINEMATIC COMPOSITIONS: Vary layouts across scenes: Split-Screen (L Title / R Chart), Rule of Thirds (L-TOP Title / R-BOT Diagram), Hero Focal (Large Hub center-right).\n"
            "3. PROGRESSIVE INFORMATION STAGING (Wave Reveal): Wave 1 (15f): Title. Wave 2 (45f): Primary Graphic. Wave 3 (75f): Details/Connectors.\n"
            "4. CAMERA INTELLIGENCE: Every shot MUST have a 'targetId'. Rotate shots: rack_focus, cinematic_drift, pan_right, orbit.\n"
            "5. DATA INTEGRITY: Use ACTUAL NUMBERS from story. If text says '20 million', KPI must show '20M'.\n"
            "6. TYPOGRAPHIC HIERARCHY: Content 3-5 words max. Every text overlay MUST have 'hero_config' highlighting a keyword.\n"
            "7. INFOGRAPHIC SYSTEMS: Procedural scenes MUST be connected systems. Use 'infographic_lines' to link separated elements.\n"
            "OUTPUT RAW JSON BLOCK ONLY. NO PREAMBLE. NO CHATTER."
        )
        if prompt_output_path:
            with open(prompt_output_path, 'w', encoding='utf-8') as f: f.write(full_prompt)

        raw_output = self._interact_with_gemini(full_prompt)
        print(f"   📊 AI Response Received ({len(raw_output)} chars).")
        try:
            # Find the largest JSON block
            blocks = re.findall(r'\{.*\}', raw_output, re.DOTALL)
            if blocks:
                json_str = max(blocks, key=len)
                data = json.loads(json_str, strict=False)
                print(f"   ✅ Successfully extracted {len(data.get('scenes', []))} scenes from AI response.")
                return data
            else:
                print("   ❌ CRITICAL: No JSON block found in AI response. Check Gemini output.")
                return {}
        except Exception as e:
            print(f"   ❌ JSON Parsing Error: {e}")
            return {}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--story-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timestamp-file")
    parser.add_argument("--fps-update-file")
    parser.add_argument("--prompt-output")
    parser.add_argument("--drive-prompt")
    parser.add_argument("--user-data-dir")
    parser.add_argument("--public-dir", default="../public")
    parser.add_argument("--manual", action="store_true")
    args = parser.parse_args()

    maker = RemotionJsonMaker(user_data_dir=args.user_data_dir, manual=args.manual)
    if args.fps_update_file: maker.load_fps_update(args.fps_update_file)
    maker.scan_assets(args.public_dir)

    if os.path.exists(args.story_file):
        with open(args.story_file, 'r', encoding='utf-8') as f: story = f.read()
    else: story = ""

    ts_content = open(args.timestamp_file, 'r', encoding='utf-8').read() if args.timestamp_file and os.path.exists(args.timestamp_file) else None

    scene_durations = []
    if maker.fps_cache:
        for i in range(1, 100):
            vname = f"scene_SC_{i:02d}.mp4"
            if vname in maker.fps_cache: scene_durations.append(maker.fps_cache[vname])
            else: break

    print("🚀 Stage 1: AI Prompting...")
    render_json = maker.generate(story, args.prompt_output, ts_content, scene_durations, drive_prompt_path=args.drive_prompt)

    print("🚀 Stage 2: Hardening & Layout Optimization...")
    render_json = maker.finalize_json_durations(render_json, public_dir=args.public_dir)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(render_json, f, indent=2, ensure_ascii=False)
    print(f"✅ Final Manifest: {args.output}")

    print("🚀 Stage 3: Professional QA...")
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from scripts.test_manifest_quality import test_manifest_quality
        test_manifest_quality(args.output, args.public_dir)
    except Exception as e:
        print(f"⚠️ QA Error: {e}")

if __name__ == "__main__": main()
