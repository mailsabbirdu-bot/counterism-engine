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
        self.raw_timestamps = ""

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
        print("🌐 Navigating to Gemini (90s timeout)...")
        try:
            self.page.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=90000)
        except Exception as e:
            print(f"⚠️ Navigation timeout/error: {e}. Attempting to proceed anyway...")

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

    def scan_assets(self, public_dir: str = "../public"):
        abs_public = os.path.abspath(public_dir)

        # 1. Fonts
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
                        if any(kw in clean_name.lower() for kw in BANGLA_KEYWORDS):
                            self.bangla_fonts.append(clean_name)
                        else:
                            self.english_fonts.append(clean_name)
        self.bangla_fonts = sorted(list(set(self.bangla_fonts)))
        self.english_fonts = sorted(list(set(self.english_fonts)))
        print(f"🔍 Font Detection: Found {len(self.bangla_fonts)} Bangla fonts, {len(self.english_fonts)} English fonts.")

        # 2. SFX
        audio_dir = os.path.join(abs_public, "renders/audios")
        self.in_files = []
        self.out_files = []
        self.camera_files = []
        self.narration_files = []
        self.video_files = []
        if os.path.exists(audio_dir):
            all_files = os.listdir(audio_dir)
            self.in_files = sorted([f for f in all_files if re.match(r'^(in[_\-]?\d*|intro|enter)', f, re.I) and f.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg'))])
            self.out_files = sorted([f for f in all_files if re.match(r'^(out[_\-]?\d*|outro|exit)', f, re.I) and f.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg'))])
            self.camera_files = sorted([f for f in all_files if re.match(r'^camera[_\-]?\d*', f, re.I) and f.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg'))])
            self.narration_files = sorted([f for f in all_files if re.match(r'^SC_\d+', f, re.I) and f.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg'))])
            print(f"🎵 SFX Detection: {len(self.in_files)} intro, {len(self.out_files)} outro, {len(self.camera_files)} camera, {len(self.narration_files)} narrations.")
        else:
            print(f"⚠️ SFX directory not found: {audio_dir}")

        # 3. Videos
        video_dir = os.path.join(abs_public, "renders")
        if os.path.exists(video_dir):
            self.video_files = sorted([f for f in os.listdir(video_dir) if f.lower().endswith('.mp4')])
            print(f"🎬 Video Detection: Found {len(self.video_files)} background videos.")

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
            'shadcn_chart': (1000, 600),
            'ui_panel': (700, 500),
            'data_indicator': (450, 400),
            'shadcn_indicator': (450, 400),
            'svg': (300, 300),
            'kpi': (450, 400),
            'timeline': (1000, 300),
            'hub_network': (800, 800),
            'flow_diagram': (1000, 400),
            'process': (1000, 400),
            'media': (900, 700),
            'image': (900, 700),
            'video': (900, 700)
        }

        # Expert Motion Graphics Budget (High Fidelity)
        MAX_TEXT_PER_SCENE = 3
        MAX_FOCAL_PER_SCENE = 3
        MAX_SVG_PER_SCENE = 12

        # Expert 3-Column Anchors (Wide)
        SECTORS = {
            "TOP_LEFT": {"x": 400, "y": 250},
            "TOP_RIGHT": {"x": 1520, "y": 250},
            "BOTTOM_LEFT": {"x": 400, "y": 830},
            "BOTTOM_RIGHT": {"x": 1520, "y": 830},
            "CENTER_FOCAL": {"x": 960, "y": 540},
            "MID_LEFT": {"x": 400, "y": 540},
            "MID_RIGHT": {"x": 1520, "y": 540},
            "LEFT_COL": {"x": 400, "y": 540},
            "CENTER_COL": {"x": 960, "y": 540},
            "RIGHT_COL": {"x": 1520, "y": 540}
        }

        sfx_manifest = []
        in_ptr, out_ptr, cam_ptr = 0, 0, 0

        for scene_idx, scene in enumerate(data['scenes']):
            scene_sfx = [] # Local collection to allow de-duplication
            s_id = scene.get('scene_id', 'unknown')
            has_relation = False # Initialize to prevent UnboundLocalError

            # Detect language for the scene based on narration if available
            # If no narration context is injected yet, we fallback to text overlays later

            print(f"   🎬 Processing Scene: {s_id}")

            # 1. LLM Fix: Root Level Schema Alignment
            if 'duration' in scene and 'duration_in_frames' not in scene:
                scene['duration_in_frames'] = scene['duration']

            # Robust Overlay Key Detection (Handles empty lists or missing keys)
            if not scene.get('overlays') or (isinstance(scene.get('overlays'), list) and len(scene.get('overlays')) == 0):
                for k in ['elements', 'layers', 'objects', 'visuals', 'components', 'items', 'content_list']:
                    if scene.get(k) and isinstance(scene[k], list) and len(scene[k]) > 0:
                        scene['overlays'] = scene[k]
                        print(f"      🔧 Recovered overlays from list key '{k}'")
                        break

            # LLM Repair: Handle non-list overlays (e.g. single object)
            if 'overlays' in scene and isinstance(scene['overlays'], dict):
                 scene['overlays'] = [scene['overlays']]
                 print(f"      🔧 Converted single overlay object to list")

            # LLM Repair: text_overlay / focal_element object patterns
            if not scene.get('overlays') or not isinstance(scene['overlays'], list) or len(scene['overlays']) == 0:
                scene['overlays'] = []
                # Extreme recovery: search for any key that looks like it contains an overlay
                for k in ['text_overlay', 'focal_element', 'overlay', 'text', 'chart', 'indicator', 'data', 'overlay_list', 'graphic']:
                    if k in scene:
                        val = scene[k]
                        if isinstance(val, list):
                            for obj in val:
                                if isinstance(obj, dict):
                                    if k == 'text_overlay' or k == 'text': obj['type'] = 'text'
                                    scene['overlays'].append(obj)
                            print(f"      🔧 Recovered {len(val)} overlays from list key '{k}'")
                        elif isinstance(val, dict):
                            obj = val
                            if k == 'text_overlay' or k == 'text': obj['type'] = 'text'
                            if k == 'chart' or k == 'indicator': obj['type'] = k
                            scene['overlays'].append(obj)
                            print(f"      🔧 Recovered overlay from dict key '{k}'")

            if 'background' in scene and isinstance(scene['background'], dict):
                bg = scene['background']
                for k in ['background_type', 'video_path', 'audio_enabled', 'procedural_config']:
                    if k in bg and k not in scene: scene[k] = bg[k]

            # LLM Repair: procedural_config as string
            if 'procedural_config' in scene and isinstance(scene['procedural_config'], str):
                 scene['procedural_config'] = {"variant": scene['procedural_config']}

            # 2. Background Handling (Studio V4 SVG Integration)
            if not scene.get('background_type'):
                scene['background_type'] = 'video'

            # STUDIO V4 FIX: Always mute background video to avoid double narration.
            # Drive-based narration mapping in 3b will handle ALL voiceover audio.
            scene['audio_enabled'] = False

            # Smart Indexing: Try to get scene number from ID (e.g. SCENE_05 -> 5)
            id_match = re.search(r'(\d+)', s_id)
            id_num = int(id_match.group(1)) if id_match else (scene_idx + 1)

            if scene['background_type'] == 'video':
                # Preserve existing valid render paths (important for Remake project)
                current_vpath = scene.get('video_path', '')
                if not current_vpath or not current_vpath.startswith('renders/'):
                    # Check if matching video actually exists
                    vname = f"scene_SC_{id_num:02d}.mp4"
                    if vname in self.video_files:
                        scene['video_path'] = f"renders/{vname}"
                        print(f"      🎬 Assigned background: {scene['video_path']} (derived from ID '{s_id}')")
                    else:
                        # Fallback to procedural if video missing
                        scene['background_type'] = 'procedural'
                        if not scene.get('procedural_config') or not isinstance(scene.get('procedural_config'), dict):
                            scene['procedural_config'] = {"variant": "neon_grid"}
                        scene['video_path'] = None
                        print(f"      🎨 Video {vname} missing. Falling back to procedural background.")
            elif scene['background_type'] == 'procedural':
                if not scene.get('procedural_config') or not isinstance(scene.get('procedural_config'), dict):
                    scene['procedural_config'] = {"variant": "neon_grid"}
                scene['video_path'] = None

                variant = scene['procedural_config'].get('variant', 'neon_grid')
                print(f"      🎨 SVG Mode: Using procedural background '{variant}'")

            # 3. Authoritative Duration Resolution
            raw_dur = scene.get('duration_in_frames') or scene.get('duration', 180)

            # STUDIO V4 FIX: Detect if duration is in seconds (small float) or frames
            if isinstance(raw_dur, (float, int)) and raw_dur < 60:
                scene_duration = int(raw_dur * 30)
            else:
                scene_duration = int(raw_dur)

            vpath = scene.get('video_path')
            if vpath:
                vpath = vpath.lstrip('/')
                filename = os.path.basename(vpath)
                if filename in self.fps_cache:
                    scene_duration = self.fps_cache[filename]

            scene['duration_in_frames'] = scene_duration

            # 3b. MAPPING NARRATION AUDIO (SC_XX naming convention)
            pattern = f"SC_{id_num:02d}".lower()
            narration_file = next((f for f in self.narration_files if pattern in f.lower()), None)
            if narration_file:
                # Check for existing narration in sfx_manifest to prevent duplication
                if not any(s.get('scene_id') == s_id and s.get('volume') == 1.0 for s in sfx_manifest):
                    sfx_manifest.append({
                        "scene_id": s_id,
                        "file": narration_file,
                        "start": 0,
                        "end": scene_duration,
                        "volume": 1.0
                    })
                    print(f"      🎙️ Mapped narration: {narration_file}")

            placed_overlays = []
            focal_ids = []

            text_count = 0
            focal_count = 0

            if scene.get('overlays'):
                # LLM Repair: overlays as dict instead of list
                if isinstance(scene['overlays'], dict):
                     scene['overlays'] = [scene['overlays']]
                     print(f"      🔧 Converted single overlay object to list")

                # Pass 0: Detect Title+Content relation
                text_ov = next((o for o in scene['overlays'] if isinstance(o, dict) and (o.get('type') == 'text' or 'text' in o or 'content' in o)), None)
                focal_ov = next((o for o in scene['overlays'] if o.get('type') in ['chart', 'shadcn_chart', 'ui_panel', 'data_indicator', 'shadcn_indicator', 'indicator'] or 'chart_type' in o or 'kind' in o), None)
                has_relation = text_ov and focal_ov

                # First Pass: Budgeting & Schema Alignment
                valid_overlays = []
                for ov in scene['overlays']:
                    # LLM Repair: Map start_frame/end_frame/end
                    if 'start_frame' in ov and 'start' not in ov: ov['start'] = ov['start_frame']

                    if 'duration' not in ov:
                        if 'end_frame' in ov: ov['duration'] = max(60, ov['end_frame'] - ov.get('start', 0))
                        elif 'end' in ov: ov['duration'] = max(60, ov['end'] - ov.get('start', 0))

                    # LLM Repair: text_overlay / focal_element object patterns
                    if not ov.get('type'):
                        if 'text' in ov or 'content' in ov: ov['type'] = 'text'
                        elif 'chart_type' in ov or 'kind' in ov: ov['type'] = 'chart'
                        elif 'indicator_type' in ov: ov['type'] = 'data_indicator'

                    # LLM Repair: kind -> indicator_type / chart_type (CRITICAL: Do this before resolving ov_type)
                    if 'kind' in ov:
                        if ('chart' in str(ov.get('kind')) or 'bar' in str(ov.get('kind')) or 'pie' in str(ov.get('kind'))):
                             ov['type'] = 'chart'
                             if 'chart_type' not in ov: ov['chart_type'] = ov['kind']
                        else:
                             ov['type'] = 'data_indicator'
                             if 'indicator_type' not in ov: ov['indicator_type'] = ov['kind']

                    # Re-resolve type after potential repair
                    ov_type = ov.get('type', 'text')

                    # LLM Repair: ui -> ui_panel, text missing but key present
                    if ov_type == 'ui' or ov_type == 'ui_panel': ov['type'] = 'ui_panel'
                    if ov_type == 'indicator' or ov_type == 'data_indicator': ov['type'] = 'data_indicator'

                    # SHADCN REDIRECTION: If AI hallucinated type but matched shadcn keys
                    if 'chart_type' in ov and ov.get('chart_type') in ['glass_area', 'neon_bar', 'stacked_line', 'radial_score', 'radar_web']:
                        ov['type'] = 'shadcn_chart'
                    if 'indicator_type' in ov and ov.get('indicator_type') in ['metric_tile', 'tech_badge', 'activity_ring', 'crypto_card']:
                        ov['type'] = 'shadcn_indicator'

                    # Final re-resolve for branching
                    ov_type = ov.get('type', 'text')

                    if ov_type == 'text':
                        if text_count >= MAX_TEXT_PER_SCENE: continue
                        text_count += 1
                        # LLM Repair: text/query -> content
                        if not ov.get('content') or str(ov.get('content')).upper() == "INSIGHT":
                            ov['content'] = ov.get('text') or ov.get('query')

                        # Extreme Recovery from story if still missing or generic
                        if not ov.get('content') or str(ov.get('content')).upper() == "INSIGHT":
                            story_text = self.story_scenes.get(s_id, "")
                            if story_text:
                                sentence = re.split(r'[.।]', story_text)[0]
                                words = sentence.split()[:6]
                                ov['content'] = " ".join(words)
                            else:
                                ov['content'] = "REMOTION"

                        # Strip trailing punctuation
                        if ov.get('content'):
                            ov['content'] = str(ov['content']).rstrip('.। ')

                        # Ensure fontSize has units
                        fs = ov.get('fontSize', 120)
                        if isinstance(fs, int): ov['fontSize'] = f"{fs}px"
                        elif isinstance(fs, str) and fs.isdigit(): ov['fontSize'] = f"{fs}px"

                        # Font Fallback
                        content = ov.get('content', '')
                        is_bangla = self._is_bangla(content)
                        f = ov.get('font')
                        if not f or f == 'undefined' or f == 'null':
                            if is_bangla and self.bangla_fonts:
                                ov['font'] = self.bangla_fonts[0]
                            elif not is_bangla and self.english_fonts:
                                ov['font'] = self.english_fonts[0]

                        # Sanitize font names (ensure no weird characters or extensions)
                        if ov.get('font'):
                            ov['font'] = re.sub(r'\.(ttf|otf|woff|woff2)$', '', str(ov['font']), flags=re.I)
                    elif ov_type in ['chart', 'ui_panel', 'data_indicator', 'shadcn_chart', 'shadcn_indicator']:
                        if focal_count >= MAX_FOCAL_PER_SCENE: continue
                        focal_count += 1

                    elif ov_type == 'svg':
                        # Allow multiple SVGs for infographic storytelling
                        pass

                        # LLM Repair: kind -> indicator_type / chart_type
                        if 'kind' in ov:
                            if ov_type == 'chart' and 'chart_type' not in ov: ov['chart_type'] = ov['kind']
                            if (ov_type == 'ui_panel' or ov_type == 'data_indicator') and 'indicator_type' not in ov:
                                ov['indicator_type'] = ov['kind']

                        if ov_type == 'data_indicator' and ov.get('indicator_type') in ['kpi', 'counter']:
                            ov['indicator_type'] = 'kpiNumber'

                        # Mandatory Field Repair for Nivo/Indicators
                        if ov_type == 'data_indicator':
                            if not ov.get('label'): ov['label'] = "Metric"

                            # KPI String Parsing (e.g. "20M" -> 20, suffix: "M")
                            val = ov.get('value', '')
                            if isinstance(val, str):
                                val_match = re.search(r'(\d+)([kKmM%]?)', val)
                                if val_match:
                                    ov['value'] = int(val_match.group(1))
                                    if val_match.group(2) and not ov.get('suffix'):
                                        ov['suffix'] = val_match.group(2).upper()
                                else:
                                    ov['value'] = 0

                            if 'value' not in ov or ov['value'] == 0:
                                 # Try to extract number from related text if available (supports Bengali digits)
                                 num_match = re.search(r'([0-9০-৯]+)', text_ov.get('content', '') if text_ov else '')
                                 if num_match:
                                     eng_val = self._to_eng_digit(num_match.group(1))
                                     ov['value'] = int(eng_val)
                                 else:
                                     ov['value'] = 0
                        elif ov_type == 'chart':
                            if not ov.get('data'): ov['data'] = [{"id": "A", "value": 10}, {"id": "B", "value": 20}]
                            if not ov.get('title'): ov['title'] = "Data Overview"

                    # Ensure start/duration exists
                    if 'start' not in ov: ov['start'] = 0
                    if 'duration' not in ov: ov['duration'] = max(120, scene_duration - ov['start'])

                    valid_overlays.append(ov)

                scene['overlays'] = valid_overlays
                print(f"      📊 Manifest Stats: {len(valid_overlays)} overlays validated ({text_count} text, {focal_count} focal)")

                for i, ov in enumerate(scene['overlays']):
                    # Ensure ID exists
                    if not ov.get('id'):
                        ov['id'] = f"OV_{scene_idx+1}_{i+1}_{ov.get('type', 'element').upper()}"

                    ov_type = ov.get('type', 'text')
                    if ov_type in ['text', 'chart', 'ui_panel', 'data_indicator', 'shadcn_chart', 'shadcn_indicator']:
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

                        # --- HERO WORD SAFETY ---
                        # If a hero word is present, it will scale up significantly (up to 1.35x).
                        # Increase the estimated footprint to prevent collisions with other elements.
                        footprint_scale = 1.4 if ov.get('hero_config') else 1.0

                        # Expert Layout: allow wider text blocks for cinematic feel
                        w = min(1600, len(max(content.split('\n'), key=len)) * (fs * (1.0 if is_bangla else 0.8)) * footprint_scale)
                        h = lines * (fs * (1.8 if is_bangla else 1.5)) * footprint_scale

                    elif ov_type == 'chart':
                        w = ov.get('width', 1000) + 100
                        h = ov.get('height', 600) + 100

                    # 1. Professional Slot Alignment & De-confliction
                    # Force Text and Charts into opposing quadrants for Expert Cinematic Balance
                    slot_name = ov.get('slot', ov.get('layout', ''))
                    if not isinstance(slot_name, str): slot_name = ''
                    slot_name = slot_name.upper()

                    if has_relation:
                        # Stack TITLE (Text) above CONTENT (Focal)
                        # Synchronize timing for related layers
                        ov['start'] = max(text_ov.get('start', 0), focal_ov.get('start', 0))
                        ov['duration'] = min(text_ov.get('duration', 120), focal_ov.get('duration', 120))

                        if ov_type == 'text':
                             ov['position'] = {"x": 400, "y": 540} # Column 1
                        else:
                             ov['position'] = {"x": 1520, "y": 540} # Column 3
                    else:
                        # EXPERT COMPOSITION RULES
                        bg_type = scene.get('background_type', 'procedural')

                        if bg_type == 'video':
                            # Safe Zone Composition (Avoid center focal point of footage)
                            # Strictly avoid CENTER_FOCAL for video
                            if ov_type in ['chart', 'ui_panel', 'data_indicator', 'kpi', 'timeline']:
                                slot_name = ["TOP_RIGHT", "BOTTOM_RIGHT", "MID_RIGHT"][i % 3]
                            elif ov_type in ['hub_network', 'flow_diagram', 'process', 'svg']:
                                # Push flows to columns instead of center for video
                                slot_name = ["MID_LEFT", "MID_RIGHT"][i % 2]
                            else:
                                slot_name = ["TOP_LEFT", "BOTTOM_LEFT", "MID_LEFT"][i % 3]
                        else:
                            # Procedural Composition (Balanced spread)
                            if ov_type in ['hub_network', 'flow_diagram', 'process']:
                                slot_name = "CENTER_COL"
                            elif ov_type in ['chart', 'ui_panel', 'data_indicator', 'kpi', 'timeline']:
                                slot_name = ["TOP_RIGHT", "BOTTOM_RIGHT", "MID_RIGHT"][i % 3]
                            else:
                                slot_name = ["TOP_LEFT", "BOTTOM_LEFT", "MID_LEFT"][i % 3]

                    if not has_relation and slot_name in SECTORS:
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
                    # Expert Whitespace (300px for large focal, 120px for text/small)
                    buffer = 300 if w > 500 else 120
                    for attempt in range(15):
                        collision_found = False
                        for prev_ov, prev_w, prev_h in placed_overlays:
                            s1, e1 = ov.get('start', 0), ov.get('start', 0) + ov.get('duration', 60)
                            s2, e2 = prev_ov.get('start', 0), prev_ov.get('start', 0) + prev_ov.get('duration', 60)

                            if max(s1, s2) < min(e1, e2):
                                x1, y1 = ov['position']['x'], ov['position']['y']
                                x2, y2 = prev_ov['position']['x'], prev_ov['position']['y']

                                # Overlap check with comfort buffer
                                if abs(x1 - x2) < (w + prev_w) / 2 + buffer and abs(y1 - y2) < (h + prev_h) / 2 + buffer:
                                    collision_found = True

                                    # Nudge logic: try vertical first, then horizontal
                                    # Force asymmetric offset for expert feel
                                    if abs(y1 - y2) < (h + prev_h) / 2 + buffer:
                                        if y1 <= y2: ov['position']['y'] = y2 - (h + prev_h) / 2 - buffer
                                        else: ov['position']['y'] = y2 + (h + prev_h) / 2 + buffer

                                        # Add horizontal "breathing" offset
                                        ov['position']['x'] += (50 if x1 > 960 else -50)

                                    # Secondary check: if vertical nudge pushed it off-screen, try horizontal
                                    if ov['position']['y'] < 200 or ov['position']['y'] > 880:
                                        ov['position']['y'] = y1 # reset y
                                        if x1 <= x2: ov['position']['x'] = x2 - (w + prev_w) / 2 - buffer - 50
                                        else: ov['position']['x'] = x2 + (w + prev_w) / 2 + buffer + 50

                                    print(f"   🔧 Expert Nudging {ov['id']} to resolve overlap -> New Pos: ({int(ov['position']['x'])}, {int(ov['position']['y'])})")
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

                    # 4. Expert Cinematic Staging & Intro Sync
                    # Introduce elements gradually to build the story.
                    min_total = 60 # Absolute minimum 2 seconds visibility

                    # Intro Sync: Use word-specific timestamp if possible
                    word_sync = self._get_word_timestamp(s_id, ov.get('content') or ov.get('label') or ov.get('title', ''))

                    # Force staggering if multiple elements start at the exact same frame
                    base_start = word_sync if word_sync != -1 else self._get_scene_start_frame(s_id)

                    # Add staggering (15f per element) to the base start
                    # Primary elements (i=0) appear first, secondary/tertiary follow
                    start_f = base_start + (i * 15)

                    # PERSISTENCE: Expert video editors keep graphics on screen until the scene changes
                    duration_f = scene_duration - start_f

                    # Safety check: if start is too late, shift it back to allow minimum visibility
                    if duration_f < min_total:
                        shift = min(start_f, min_total - duration_f)
                        start_f -= shift
                        duration_f += shift

                    ov['start'] = start_f
                    ov['duration'] = duration_f

                    # Cleanup hallucinated keys
                    for k in ['intro', 'outro', 'resting']:
                        if k in ov: del ov[k]

                    # Subtle local SFX (Volume 0.04)
                    if self.in_files:
                        scene_sfx.append({ "scene_id": s_id, "type": "in", "start": ov['start'], "end": ov['start'] + 20 })
                    if self.out_files:
                        scene_sfx.append({ "scene_id": s_id, "type": "out", "start": ov['start'] + ov['duration'] - 10, "end": ov['start'] + ov['duration'] })

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

            # 5. SFX De-duplication (Scene Level with 5f tolerance window)
            seen_in = []
            seen_out = []
            def is_duplicate(val, seen_list):
                return any(abs(val - s) <= 5 for s in seen_list)

            for sfx in scene_sfx:
                if sfx['type'] == 'in':
                    if not is_duplicate(sfx['start'], seen_in):
                        sfx_file = self.in_files[in_ptr % len(self.in_files)] if self.in_files else "in_1.mp3"
                        sfx_manifest.append({ "scene_id": sfx['scene_id'], "file": sfx_file, "start": sfx['start'], "end": sfx['end'], "volume": 0.05 })
                        in_ptr += 1
                        seen_in.append(sfx['start'])
                else:
                    if not is_duplicate(sfx['start'], seen_out):
                        sfx_file = self.out_files[out_ptr % len(self.out_files)] if self.out_files else "out_1.mp3"
                        sfx_manifest.append({ "scene_id": sfx['scene_id'], "file": sfx_file, "start": sfx['start'], "end": sfx['end'], "volume": 0.05 })
                        out_ptr += 1
                        seen_out.append(sfx['start'])

            if scene['camera'].get('shots'):
                camera_styles = ["slow_push", "zoom_in", "pan_left", "pan_right", "orbit"]
                for shot_idx, shot in enumerate(scene['camera']['shots']):
                    # 1. Assign Camera SFX
                    if self.camera_files:
                        sfx_manifest.append({
                            "scene_id": s_id,
                            "file": self.camera_files[cam_ptr % len(self.camera_files)],
                            "start": shot.get('startFrame', 0) or shot.get('start', 0),
                            "end": (shot.get('startFrame', 0) or shot.get('start', 0)) + 30,
                            "volume": 0.07
                        })
                        cam_ptr += 1

                    # 2. LLM Repair: target -> targetId, type -> style
                    if 'target' in shot and 'targetId' not in shot:
                        shot['targetId'] = shot['target']
                    if ('type' in shot or not shot.get('style')) and 'style' not in shot:
                        shot['style'] = shot.get('type', camera_styles[shot_idx % len(camera_styles)])

                    # 3. Title+Content Safety: Target screen center for stacked layouts
                    if has_relation:
                        # Target focal element for stability, but keep zoom conservative
                        shot['targetId'] = focal_ov['id'] if focal_ov else (text_ov['id'] if text_ov else None)
                        shot['zoom'] = min(shot.get('zoom', 1.25), 1.35)

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

            # 6. ID RESOLUTION SAFETY (Infographic Lines)
            # Ensure AI didn't reference non-existent IDs with fuzzy matching for pluralization
            valid_ids = set([ov['id'] for ov in scene.get('overlays', [])])
            if scene.get('infographic_lines'):
                safe_lines = []
                for l in scene['infographic_lines']:
                    f, t = l.get('from'), l.get('to')

                    # Try direct match first
                    if f in valid_ids and t in valid_ids:
                        safe_lines.append(l)
                        continue

                    # Fuzzy match for common AI pluralization errors (e.g. svg_icons -> svg_icon)
                    def find_fuzzy(target):
                        if target in valid_ids: return target
                        for vid in valid_ids:
                            if target.rstrip('s') == vid or vid.rstrip('s') == target: return vid
                        return None

                    nf = find_fuzzy(f) if f else None
                    nt = find_fuzzy(t) if t else None

                    if nf and nt:
                        l['from'], l['to'] = nf, nt
                        safe_lines.append(l)

                scene['infographic_lines'] = safe_lines

        data['audio_sfx_manifest'] = sfx_manifest
        print(f"✅ Finalization: Processed {len(data['scenes'])} scenes, {len(sfx_manifest)} SFX triggers mapped.")
        return self.validate_and_fix_manifest(data)

    def _get_scene_hero_word(self, scene_id: str, overlay_content: str, scene_duration: int = 180):
        if not self.raw_timestamps or not overlay_content: return None

        # Comprehensive Bangla stop-words to avoid meaningless hero highlights
        STOP_WORDS = [
            "এই", "একটি", "হলো", "হচ্ছে", "আর", "কিন্তু", "এবং", "বা", "তবে", "যদি", "যে", "সে", "তারা", "ছিল", "হবে",
            "করে", "করা", "জন্য", "থেকে", "সাথে", "দ্বারা", "মাধ্যমে", "এক", "দুই", "তিন", "চার", "পাচ", "ছয়", "সাত",
            "আট", "নয়", "দশ", "কোটি", "লক্ষ", "কোটিরও", "বেশি", "কম", "অনেক", "অল্প", "হলে", "যায়", "গিয়ে", "নিয়ে",
            "হয়ে", "থাকা", "রাখা", "বলছে", "বলেন", "শুরু", "শেষ", "এখন", "তখন", "যখন", "পর্যন্ত", "প্রতিটি", "প্রতি",
            "সব", "সবাই", "কেউ", "কেউই", "কিছু", "কোন", "কোনো", "মতো", "মত", "মতোই", "মতই", "নিজেই", "নিজে", "বড়", "ছোট"
        ]

        # SCENE_01: [Original: 0.00s - 0.98s] -> [30fps: 0f - 29f] "ঢাকা।"
        pattern = fr'{scene_id}:.*?\[30fps:\s*(\d+)f\s*-\s*\d+f\]\s*"(.*?)"'
        words = re.findall(pattern, self.raw_timestamps)
        if not words: return None

        content_clean = re.sub(r'[.।]', '', overlay_content)
        content_words = content_clean.split()

        # Filtered word pool: Must be in content AND not a stop-word
        candidates = []
        for frame, word in words:
            word_clean = re.sub(r'[.।]', '', word)
            if word_clean in content_words and word_clean not in STOP_WORDS:
                candidates.append({"word": word_clean, "start": int(frame)})

        if not candidates: return None

        # Priority 1: Pick the longest meaningful word
        hero = max(candidates, key=lambda x: len(x['word']))

        # --- USER RULE: BUFFERING & PACING ---
        # 1. Start buffer: Hero word must wait at least 45 frames
        hero['start'] = max(45, hero['start'])

        # 2. End buffer: Hero word must stay on screen for at least 2 seconds (60 frames)
        # It must start animating AT LEAST 60 frames BEFORE the scene ends.
        # This ensures the highlight is visible for the required duration.
        # We also need to account for the overlay's exit duration (15 frames).
        latest_possible_start = scene_duration - 75

        if hero['start'] > latest_possible_start:
             # If audio sync is too late, shift start earlier to satisfy 2s stay rule
             hero['start'] = max(45, latest_possible_start)

        return hero

    def _get_fallback_hero(self, overlay_content: str):
        """Pick longest word if timestamp matching fails."""
        if not overlay_content: return None
        content_clean = re.sub(r'[.।]', '', overlay_content)
        words = content_clean.split()
        if not words: return None
        hero_word = max(words, key=len)
        return {"word": hero_word, "start": 60} # Default 2sec in

    def validate_and_fix_manifest(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Final integrity pass to ensure compliance with Studio V4 Guidelines & Engine."""
        print("🔍 Guardrail Engine: Performing deep validation of engine compliance and user guidelines...")
        if not data.get('scenes'): return data

        # Camera Style Rotation Pool (40 Ultra-Modern Presets)
        camera_styles = [
            "slow_push", "slow_pull", "push_in", "pull_out", "whip_pan", "dramatic_reveal",
            "cinematic_drift", "dynamic_orbit", "vertical_sweep", "spiral_vortex", "glitch_snap",
            "low_angle_hero", "side_strafe_left", "side_strafe_right", "aerial_top_down",
            "shaky_handheld", "zoom_blur_reveal", "tilt_shift_focus", "power_zoom", "smooth_glide",
            "epic_scaling", "warp_speed", "rolling_horizon", "fisheye_distort", "dolly_zoom",
            "parallax_slide", "staccato_jump", "oblique_view", "macro_focus", "uprising_reveal",
            "descending_gaze", "infinity_loop", "kaleidoscope", "cyber_scan", "extreme_closeup",
            "wide_panorama", "pendulum_swing", "drunken_stumble", "floating_weightless", "rapid_fire",
            "gentle_breeze", "the_matrix", "heartbeat_zoom"
        ]
        # ULTRA MODERN - EYE SOOTHING - ATTENTION GRABBING PALETTE (Curated)
        modern_colors = ["#00F5FF", "#FF3E6C", "#00FFAB", "#ADFF2F", "#FFD700", "#7B68EE", "#FF8C00"] # Cyan, Rose, Neon Mint, Lime, Gold, Iris, Deep Orange

        for idx, scene in enumerate(data['scenes']):
            scene_id = scene.get('scene_id', f"SCENE_{idx+1}")
            duration = scene.get('duration_in_frames', 180)

            # --- GUIDELINE: MANDATORY NIVO FOR NUMBERS ---
            # Scan scene text for digits or numerical words
            all_text = " ".join([o.get('content', '') for o in scene.get('overlays', []) if o.get('type') == 'text'])
            is_scene_bangla = self._is_bangla(all_text)
            has_number = re.search(r'[0-9০-৯]|million|M|k|K|percent|%|দশ|শত|হাজার|কোটি|লক্ষ', all_text, re.I)
            has_focal = any(o.get('type') in ['chart', 'shadcn_chart', 'data_indicator', 'shadcn_indicator', 'ui_panel'] for o in scene.get('overlays', []))

            if has_number and not has_focal:
                print(f"   ⚠️ Scene {scene_id} mentions numbers but lacks focal visualization. Injecting KPI.")
                # Improved number extraction: look for patterns like "২ কোটি" or "20 million"
                num_match = re.search(r'([0-9০-৯]+)', all_text)
                injected_val = self._to_eng_digit(num_match.group(1)) if num_match else "0"

                # Check for magnitude suffixes in text to refine 'injected_val'
                suffix = ""
                if "কোটি" in all_text: suffix = "কোটি"
                elif "লক্ষ" in all_text: suffix = "লক্ষ"
                elif "million" in all_text.lower(): suffix = "M"
                elif "percent" in all_text.lower() or "%" in all_text: suffix = "%"

                scene['overlays'].append({
                    "id": f"kpi_auto_{idx}",
                    "type": "data_indicator",
                    "indicator_type": "kpiNumber",
                    "label": "Metric",
                    "value": int(injected_val) if injected_val != "0" else 10, # Avoid silly '0' values
                    "suffix": suffix,
                    "start": 30,
                    "duration": duration - 60,
                    "position": {"x": 1440, "y": 540} # Default to right
                })

            # --- GUIDELINE: EXPERT HIGH-FIDELITY BUDGET (MAX 3 TEXT, 3 FOCAL, 12 SVG) ---
            # EXCEPTION: SVGs and infographic elements are allowed in bulk for rich storytelling.
            COMPLEX_SVG_TYPES = ['svg', 'hub_network', 'flow_diagram', 'process', 'label', 'callout', 'timeline', 'composition']
            texts = [o for o in scene.get('overlays', []) if o.get('type') == 'text']
            focals = [o for o in scene.get('overlays', []) if o.get('type') not in (['text'] + COMPLEX_SVG_TYPES)]
            svg_elements = [o for o in scene.get('overlays', []) if o.get('type') in COMPLEX_SVG_TYPES]

            # Expert Cap (Enforce all limits simultaneously)
            scene['overlays'] = texts[:3] + focals[:3] + svg_elements[:12]

            # Detect Title+Content relation for stacking
            text_ov = next((o for o in scene['overlays'] if o.get('type') == 'text'), None)
            focal_ov = next((o for o in scene['overlays'] if o.get('type') != 'text'), None)
            has_relation = text_ov and focal_ov

            # 1. Overlay Pass
            for ov in scene.get('overlays', []):
                o_type = ov.get('type', 'text')

                # --- GUIDELINE: TEXT AESTHETICS (STRIP PUNCTUATION) ---
                if o_type == 'text':
                    if ov.get('content'):
                        ov['content'] = str(ov['content']).strip().rstrip('.। ')
                        # MANDATORY TRUNCATION: Keep it punchy (Max 5 words) for the "vibe"
                        words = ov['content'].split()
                        if len(words) > 5:
                            ov['content'] = " ".join(words[:5])
                            print(f"      ✂️ (Guardrail) Truncated verbose text to vibe: \"{ov['content']}\"")

                    # Extreme Recovery for Hallucinations
                    hallucinations = ["INSIGHT", "CITY", "MASTERCLASS", "REMOTION", "OVERVIEW", "DATA", "ANALYSIS"]
                    if not ov.get('content') or str(ov.get('content')).upper() in hallucinations:
                        # Attempt to extract a meaningful phrase from the scene's narration
                        story_text = self.story_scenes.get(scene_id, "")
                        if story_text:
                            # Use first sentence or up to 6 words
                            sentence = re.split(r'[.।]', story_text)[0].strip()
                            words = sentence.split()[:6]
                            ov['content'] = " ".join(words)
                        else:
                            ov['content'] = "DYNAMIC CONTENT" # Final fallback

                    # Modern Color
                    ov['color'] = modern_colors[idx % len(modern_colors)]
                    if not ov.get('style'):
                         ov['style'] = f"text-{ov['color']}"

                    if not ov.get('font'):
                        is_ov_bangla = self._is_bangla(ov.get('content', ''))
                        if is_ov_bangla and self.bangla_fonts:
                            ov['font'] = self.bangla_fonts[0]
                        elif not is_ov_bangla and self.english_fonts:
                            ov['font'] = self.english_fonts[0]
                        else:
                            ov['font'] = "Arial"

                    # Force Bangla font if content contains Bangla characters, regardless of AI selection
                    if self._is_bangla(ov.get('content', '')) and self.bangla_fonts:
                        ov['font'] = self.bangla_fonts[0]

                    # --- GUIDELINE: HERO WORD ---
                    # Only auto-generate if missing or if the word isn't actually in the content
                    existing_hero = ov.get('hero_config', {})
                    hero_word_in_content = existing_hero.get('word') and str(existing_hero.get('word')) in str(ov.get('content', ''))

                    if not hero_word_in_content:
                        hero = self._get_scene_hero_word(scene_id, ov.get('content', ''), duration)
                        if not hero:
                            hero = self._get_fallback_hero(ov.get('content', ''))

                        if hero:
                            hero_anims = [
                                "glow_pulse", "isolate_zoom", "bounce_pop", "neon_flicker", "shake_alert",
                                "rainbow_flow", "ghost_trail", "glitch_pop", "wave_float", "expand_contract",
                                "blur_reveal", "color_shift", "rotation_swing", "shadow_pulse", "letter_jump",
                                "skew_slide", "tilt_pan", "bounce_gravity", "border_glow", "glass_shimmer",
                                "heartbeat", "strobe_flash", "threed_flip", "magnetic_pull", "fire_glow",
                                "pixel_scatter", "swing_pivot", "depth_shadow", "energy_beam", "spiral_in",
                                "fly_in_z", "typewriter_flicker", "vibrate_intense", "float_orbit", "mirror_split",
                                "zoom_blur_pop", "liquid_waver"
                            ]
                            # Robust rotation ensures variety across scenes
                            anim_choice = hero_anims[idx % len(hero_anims)]
                            ov['hero_config'] = {
                                "word": hero['word'],
                                "start": hero.get('start', 45),
                                "color": modern_colors[(idx + 2) % len(modern_colors)],
                                "animation": anim_choice
                            }
                    else:
                        # Existing hero config is valid, just ensure it has a color and animation if missing
                        if not existing_hero.get('color'):
                             existing_hero['color'] = modern_colors[(idx + 2) % len(modern_colors)]
                        if not existing_hero.get('animation'):
                             existing_hero['animation'] = "glow_pulse"
                        if not existing_hero.get('start'):
                             existing_hero['start'] = 45

                if o_type in ['chart', 'shadcn_chart']:
                    # Force Bangla font if scene is Bangla
                    if is_scene_bangla and self.bangla_fonts:
                        ov['font'] = self.bangla_fonts[0]
                    # Robustness: ensure a font is always assigned
                    if not ov.get('font'):
                         ov['font'] = self.english_fonts[0] if self.english_fonts else "Arial"

                    ov['color'] = modern_colors[(idx + 1) % len(modern_colors)]
                    if not ov.get('colors'):
                        ov['colors'] = {"scheme": "nivo"} # Fallback to catchy scheme

                    # Data Integrity Check
                    if not ov.get('data') or (not isinstance(ov['data'], list) and not isinstance(ov['data'], dict)):
                        ov['data'] = [{"id": "A", "value": 10}, {"id": "B", "value": 20}]
                    if not ov.get('title'):
                        ov['title'] = "Data Overview"

                # Indicator Field Integrity
                if o_type in ['data_indicator', 'shadcn_indicator']:
                    # Robustness: ensure a font is always assigned
                    if not ov.get('font'):
                         ov['font'] = self.english_fonts[0] if self.english_fonts else "Arial"

                    # Force Bangla font if scene is Bangla
                    if is_scene_bangla and self.bangla_fonts:
                        ov['font'] = self.bangla_fonts[0]

                    if not ov.get('indicator_type') or ov.get('indicator_type') == 'counter':
                        ov['indicator_type'] = "kpiNumber"

                    # Label Recovery
                    if not ov.get('label') or str(ov.get('label')).upper() in ["INSIGHT", "METRIC", "DATA"]:
                        story_text = self.story_scenes.get(scene_id, "")
                        if story_text:
                            sentence = re.split(r'[.।]', story_text)[0].strip()
                            words = sentence.split()[:4] # Shorter for indicators
                            ov['label'] = " ".join(words)
                        else:
                            ov['label'] = "Insight"

                    if 'value' not in ov or ov['value'] is None: ov['value'] = 0

                    # Modern Color
                    ov['color'] = modern_colors[(idx + 1) % len(modern_colors)]
                    if not ov.get('colors'):
                        ov['colors'] = [ov['color']]

                    # Formatting
                    try:
                        val = float(ov['value'])
                        if val >= 1000000:
                            ov['value'] = int(val / 1000000); ov['suffix'] = " M" + ov.get('suffix', '').strip()
                        elif val >= 1000:
                            ov['value'] = int(val / 1000); ov['suffix'] = " K" + ov.get('suffix', '').strip()

                        # Ensure space for word-based suffixes (e.g. "কোটি", "people")
                        suffix = ov.get('suffix', '')
                        if suffix and not suffix.startswith(' '):
                            # If it starts with a letter or Bangla character, add a space
                            if re.match(r'[a-zA-Z\u0980-\u09FF]', suffix):
                                ov['suffix'] = " " + suffix
                    except: pass

                # --- GUIDELINE: CINEMATIC PACING (15-90-15) ---
                # Strictly enforce 15f intro, 15f outro, and 90-120f resting period.
                # Every overlay should follow the scene start frame from timestamp.txt for intro sync.
                intro_frames = 15
                outro_frames = 15
                resting_frames = 90
                min_total = intro_frames + resting_frames + outro_frames # 120f

                # Force Bangla font for ALL overlay types if scene is Bangla
                if is_scene_bangla and self.bangla_fonts:
                    ov['font'] = self.bangla_fonts[0]

                # Intro Sync: Try word-level matching, fallback to scene start
                word_sync = self._get_word_timestamp(scene_id, ov.get('content') or ov.get('title') or ov.get('label', ''))
                if word_sync != -1:
                    ov['start'] = word_sync
                    print(f"      🔗 Word-Sync for {ov['id']}: {word_sync}f")
                else:
                    ov['start'] = self._get_scene_start_frame(scene_id)

                # --- GUIDELINE: PERSISTENCE (EXPERT DIRECTOR) ---
                # Default duration should span until the end of the scene for expert feel
                ov['duration'] = duration - ov['start']

                # If duration is too short for an overlay to be readable, we must ensure min_total
                if ov['duration'] < min_total:
                    # Shift start earlier if possible to accommodate min_total
                    shift = min(ov['start'], min_total - ov['duration'])
                    ov['start'] -= shift
                    ov['duration'] += shift

                # --- GUIDELINE: TITLE+CONTENT ALIGNMENT ---
                if has_relation:
                    ov['start'] = max(text_ov['start'], focal_ov['start'])
                    ov['duration'] = min(text_ov['duration'], focal_ov['duration'])
                    ov['position']['x'] = 960
                    if o_type == 'text': ov['position']['y'] = 300
                    else: ov['position']['y'] = 700

            # 2. Camera Shot Pass
            if not scene.get('camera'):
                 scene['camera'] = {"enabled": True, "shots": []}

            if not scene['camera'].get('shots'):
                 # Generate a mandatory shot
                 target = focal_ov['id'] if focal_ov else (text_ov['id'] if text_ov else None)
                 scene['camera']['shots'].append({
                     "targetId": target,
                     "startFrame": 0,
                     "duration": duration,
                     "style": "slow_push",
                     "easing": {"type": "bezier", "bezier": [0.65, 0, 0.35, 1]}
                 })

            for s_idx, shot in enumerate(scene['camera']['shots']):
                # --- GUIDELINE: SMART TARGETING ---
                # Contradiction Resolution: Null is ONLY for stacked layouts (center-zoom),
                # otherwise we MUST have a valid target ID to avoid empty focus.
                if has_relation:
                    shot['targetId'] = None
                elif shot.get('targetId') is None:
                    shot['targetId'] = focal_ov['id'] if focal_ov else (text_ov['id'] if text_ov else None)

                # --- GUIDELINE: CAMERA VARIETY (40 PRESET ROTATION) ---
                # Use scene index + shot index to maximize uniqueness across the whole video
                if not shot.get('style') or shot.get('style') == 'static':
                    shot['style'] = camera_styles[(idx + s_idx) % len(camera_styles)]

                # --- GUIDELINE: BUTTERY SMOOTH BEZIER ---
                if not shot.get('easing'):
                    shot['easing'] = {"type": "bezier", "bezier": [0.65, 0, 0.35, 1]}

                # --- GUIDELINE: CAMERA SAFETY (ZOOM CAPS) ---
                max_zoom = 1.35 if has_relation else 1.6
                shot['zoom'] = min(shot.get('zoom', 1.25), max_zoom)

        # 3. SFX Pass
        valid_sfx = []
        for sfx in data.get('audio_sfx_manifest', []):
            scene = next((s for s in data['scenes'] if s['scene_id'] == sfx['scene_id']), None)
            if scene:
                s_dur = scene.get('duration_in_frames', 180)
                if sfx['start'] < s_dur:
                    sfx['end'] = min(sfx.get('end', sfx['start']+30), s_dur)
                    valid_sfx.append(sfx)
        data['audio_sfx_manifest'] = valid_sfx

        print("✨ Deep Validation Complete: All Studio V4 guidelines and engine rules strictly enforced.")
        return data


    def _interact_with_gemini(self, prompt: str, retry_count: int = 2) -> str:
        if self.manual:
            # Check if running in Google Colab for rich UI
            try:
                from google.colab import output
                from IPython.display import HTML, display
                import uuid

                # Unique ID for this interaction instance
                u_id = uuid.uuid4().hex[:8]

                display(HTML(f"""
                    <div id="container-{u_id}" style="background-color: #1a1a1a; color: #fff; padding: 25px; border-radius: 12px; border: 2px solid #4CAF50; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.5); max-width: 800px; margin: 10px auto;">
                        <h2 style="color: #4CAF50; margin-top: 0; font-size: 22px; border-bottom: 1px solid #333; padding-bottom: 10px;">🎬 Studio V4 - Manual AI Interaction</h2>

                        <div style="margin-top: 20px;">
                            <p style="font-size: 15px;">1. Copy the generated prompt:</p>
                            <button id="copyBtn-{u_id}" style="background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%); color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.3); width: 100%;">
                                📋 COPY PROMPT TO CLIPBOARD
                            </button>
                        </div>

                        <div style="margin-top: 25px;">
                            <p style="font-size: 15px;">2. Get response from <a href="https://gemini.google.com" target="_blank" style="color: #2196F3; text-decoration: none; font-weight: bold;">Gemini</a> and paste here:</p>
                            <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                                <button id="pasteBtn-{u_id}" style="background: #444; color: white; border: 1px solid #666; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 13px;">
                                    📋 PASTE FROM CLIPBOARD
                                </button>
                                <button id="clearBtn-{u_id}" style="background: #444; color: white; border: 1px solid #666; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 13px;">
                                    🧹 CLEAR
                                </button>
                            </div>
                            <textarea id="jsonResponse-{u_id}" style="width: 100%; height: 180px; background: #2d2d2d; color: #eee; border: 1px solid #444; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 13px; resize: vertical;" placeholder="Paste JSON response here..."></textarea>
                        </div>

                        <div style="margin-top: 20px;">
                            <button id="submitBtn-{u_id}" style="background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%); color: white; border: none; padding: 14px 28px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.3); width: 100%;">
                                🚀 SUBMIT RESPONSE
                            </button>
                        </div>

                        <textarea id="hiddenPrompt-{u_id}" style="display:none">{prompt}</textarea>
                    </div>

                    <script>
                        (function() {{
                            const u_id = "{u_id}";
                            const copyBtn = document.getElementById('copyBtn-' + u_id);
                            const pasteBtn = document.getElementById('pasteBtn-' + u_id);
                            const clearBtn = document.getElementById('clearBtn-' + u_id);
                            const promptText = document.getElementById('hiddenPrompt-' + u_id).value;
                            const responseArea = document.getElementById('jsonResponse-' + u_id);

                            copyBtn.onclick = () => {{
                                navigator.clipboard.writeText(promptText);
                                copyBtn.innerText = "✅ PROMPT COPIED!";
                                copyBtn.style.background = "#2196F3";
                                setTimeout(() => {{
                                    copyBtn.innerText = "📋 COPY PROMPT TO CLIPBOARD";
                                    copyBtn.style.background = "linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%)";
                                }}, 3000);
                            }};

                            pasteBtn.onclick = async () => {{
                                try {{
                                    const text = await navigator.clipboard.readText();
                                    responseArea.value = text;
                                    pasteBtn.innerText = "✅ PASTED!";
                                    setTimeout(() => pasteBtn.innerText = "📋 PASTE FROM CLIPBOARD", 2000);
                                }} catch (e) {{
                                    alert("Browser blocked clipboard access. Please paste manually (Ctrl+V).");
                                }}
                            }};

                            clearBtn.onclick = () => responseArea.value = "";
                        }})();
                    </script>
                """))

                print(f"⏳ Waiting for your input via the UI above (Instance: {u_id})...")

                # Use eval_js to wait for the result of a promise (blocks Python until resolve)
                result = output.eval_js(f"""
                    new Promise((resolve) => {{
                        const u_id = "{u_id}";
                        const submitBtn = document.getElementById('submitBtn-' + u_id);
                        const responseArea = document.getElementById('jsonResponse-' + u_id);

                        submitBtn.onclick = () => {{
                            const val = responseArea.value.trim();
                            if (!val) {{
                                alert("Please paste the Gemini response first!");
                                return;
                            }}
                            submitBtn.disabled = true;
                            submitBtn.innerText = "⌛ PROCESSING...";
                            resolve(val);
                        }};
                    }})
                """)

                print("✅ Response received. Parsing...")
                return result

            except ImportError:
                # Fallback for standard terminal environments
                print("\n" + "!"*80)
                print("🖐️  MANUAL MODE ACTIVE (Terminal Fallback)")
                print("1. COPY the prompt below.")
                print("-" * 30 + " PROMPT START " + "-" * 30)
                print(prompt)
                print("-" * 30 + "  PROMPT END  " + "-" * 30 + "\n")

                print("\n👉 Paste the JSON response from Gemini below.")
                print("👉 TYPE 'END' ON A NEW LINE AND PRESS ENTER TO SUBMIT.")

                lines = []
                while True:
                    try:
                        line = input()
                        if line.strip().upper() == "END": break
                        lines.append(line)
                    except EOFError:
                        break
                return "\n".join(lines)

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
                    time.sleep(0.2) # Aggressive polling for Colab speed
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
                        # Aggressive early exit for RAW JSON (User Mandate)
                        # If the response ends with } and we've been stable for 2 polls, grab it.
                        if not is_generating and stable_count >= 2:
                             stripped = current_text.strip()
                             if stripped.endswith("}"):
                                 print(f"✨ Gemini response finished ({len(current_text)} chars).")
                                 return current_text

                        if stable_count >= 10: # Lowered from 15 for speed
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

    def _to_eng_digit(self, s: str) -> str:
        bengali_digits = '০১২৩৪৫৬৭৮৯'
        english_digits = '0123456789'
        return s.translate(str.maketrans(bengali_digits, english_digits))

    def repair_json(self, s):
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

    def _compact_timestamps(self, ts_content: str) -> str:
        self.raw_timestamps = ts_content # Store for hero word selection
        if not ts_content: return ""
        compacted = []
        # SCENE_01: [Original: 0.00s - 0.98s] -> [30fps: 0f - 29f] "ঢাকা।"
        pattern = r'(SCENE_\d+):.*?\[30fps:\s*(\d+)f\s*-\s*\d+f\]\s*"(.*?)"'
        for line in ts_content.split('\n'):
            match = re.search(pattern, line)
            if match:
                compacted.append(f"{match.group(1)}:{match.group(2)}f \"{match.group(3)}\"")
        return " | ".join(compacted)

    def _get_scene_start_frame(self, scene_id: str):
        if not self.raw_timestamps: return 0
        # Format: SCENE_01: [Original: 0.00s - 0.98s] -> [30fps: 0f - 29f] "ঢাকা।"
        pattern = fr'{scene_id}:.*?\[30fps:\s*(\d+)f'
        match = re.search(pattern, self.raw_timestamps)
        if match:
            return int(match.group(1))
        return 0

    def _get_word_timestamp(self, scene_id: str, search_text: str) -> int:
        if not self.raw_timestamps or not search_text: return -1

        def normalize(t):
            # Keep only alphanumeric and Bangla characters
            return re.sub(r'[^\w\u0980-\u09FF]', '', str(t)).lower()

        search_clean = normalize(search_text)
        # Extract individual words from search text for broad matching
        search_words = [normalize(w) for w in str(search_text).split() if len(normalize(w)) > 1]

        if not search_clean and not search_words: return -1

        # Look for matches in timestamps for this scene
        # Support formats: "SCENE_01:0f \"ঢাকা।\"" and "SCENE_01: [30fps: 0f - 29f] \"ঢাকা।\""
        pattern = fr'{scene_id}:(?:.*?\[30fps:\s*)?(\d+)f\s*(?:-\s*\d+f\]\s*)?"(.*?)"'
        ts_data = re.findall(pattern, self.raw_timestamps)

        # 1. CRITICAL SYNC: Prioritize matching the START of the phrase
        first_word = search_words[0] if search_words else ""
        if first_word:
            for frame, word in ts_data:
                word_clean = normalize(word)
                if word_clean == first_word or (len(word_clean) > 3 and word_clean in first_word):
                    return int(frame)

        # 2. Broad phrase match (if first word wasn't found)
        for frame, word in ts_data:
            word_clean = normalize(word)
            if not word_clean: continue
            if word_clean in search_clean: return int(frame)

        # 3. Fuzzy word match (last resort)
        for frame, word in ts_data:
            word_clean = normalize(word)
            if any(word_clean == sw or (len(word_clean) > 3 and word_clean in sw) or (len(sw) > 3 and sw in word_clean) for sw in search_words):
                return int(frame)

        return -1

    def _is_bangla(self, text: str) -> bool:
        return any('\u0980' <= c <= '\u09FF' for c in text)

    def generate(self, story: str, guidelines: str, prompt_output_path: str = None, timestamp_context: str = None, scene_durations: List[int] = None) -> Dict[str, Any]:
        # Pre-process story into scenes for explicit language detection and context
        # Support both 'Scene 1' and 'দৃশ্য ১' markers, handling optional colons
        pattern = r'(?:Scene|দৃশ্য)\s+[0-9০-৯]+[:\s]*'
        story_parts = re.split(pattern, story)

        # Filter out empty parts and strip whitespace/colons from the beginning of narrations
        story_parts = [p.strip().lstrip(':').strip() for p in story_parts if p.strip()]

        scene_narrations = []
        self.story_scenes = {} # Reset and populate
        for i, narration in enumerate(story_parts, 1):
            s_id = f"SCENE_{i:02d}"
            lang = "BANGLA" if self._is_bangla(narration) else "ENGLISH"
            scene_narrations.append(f"{s_id} ({lang}): {narration}")
            self.story_scenes[s_id] = narration

        story_context = "\n".join(scene_narrations)

        story = self.adjust_durations_in_text(story)
        local_fonts = f"BANGLA FONTS: {self.bangla_fonts} | ENGLISH FONTS: {self.english_fonts}"
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

        hero_anim_list = [
            "glow_pulse", "isolate_zoom", "bounce_pop", "neon_flicker", "shake_alert",
            "rainbow_flow", "ghost_trail", "glitch_pop", "wave_float", "expand_contract",
            "blur_reveal", "color_shift", "rotation_swing", "shadow_pulse", "letter_jump",
            "skew_slide", "tilt_pan", "bounce_gravity", "border_glow", "glass_shimmer",
            "heartbeat", "strobe_flash", "threed_flip", "magnetic_pull", "fire_glow",
            "pixel_scatter", "swing_pivot", "depth_shadow", "energy_beam", "spiral_in",
            "fly_in_z", "typewriter_flicker", "vibrate_intense", "float_orbit", "mirror_split",
            "zoom_blur_pop", "liquid_waver"
        ]

        camera_style_list = [
            "slow_push", "slow_pull", "push_in", "pull_out", "whip_pan", "dramatic_reveal",
            "cinematic_drift", "dynamic_orbit", "vertical_sweep", "spiral_vortex", "glitch_snap",
            "low_angle_hero", "side_strafe_left", "side_strafe_right", "aerial_top_down",
            "shaky_handheld", "zoom_blur_reveal", "tilt_shift_focus", "power_zoom", "smooth_glide",
            "epic_scaling", "warp_speed", "rolling_horizon", "fisheye_distort", "dolly_zoom",
            "parallax_slide", "staccato_jump", "oblique_view", "macro_focus", "uprising_reveal",
            "descending_gaze", "infinity_loop", "kaleidoscope", "cyber_scan", "extreme_closeup",
            "wide_panorama", "pendulum_swing", "drunken_stumble", "floating_weightless", "rapid_fire",
            "gentle_breeze", "the_matrix", "heartbeat_zoom"
        ]

        # Build the scene target list for the prompt
        scene_targets = "\n".join([f"{sid}: {self.story_scenes[sid]}" for sid in sorted(self.story_scenes.keys())])

        full_prompt = (
            f"TASK: GENERATE PRODUCTION-READY MOTION GRAPHICS JSON FOR THESE {len(self.story_scenes)} SCENES.\n"
            "\n--- START OF STORYBOARD NARRATION (SOURCE) ---\n"
            "```text\n"
            f"{story_context}\n"
            "```\n"
            "--- END OF STORYBOARD NARRATION ---\n"
            "\n--- TIMING & SYNC DATA (MANDATORY) ---\n"
            f"TIMESTAMPS: {compact_ts}\n"
            f"DURATIONS (30fps): {duration_context}\n"
            "\nACT AS A PROFESSIONAL MOTION ARCHITECT. Design an expert documentary sequence (Vox/Polymatter style) using THE NARRATION ABOVE as the absolute source of truth.\n"
            "COMPOSITION CONSTRAINTS (STRICT):\n"
            "1. 3-COLUMN SPATIAL ANCHORS: Absolutely NO center-stacking. Every graphic must occupy a unique region:\n"
            "   - COLUMN 1 (LEFT, x=400): Punchy Short Titles.\n"
            "   - COLUMN 2 (CENTER, x=960): Hub Networks, Flow Diagrams, Primary SVG centerpieces.\n"
            "   - COLUMN 3 (RIGHT, x=1520): KPIs, Charts, Indicators, Statistics.\n"
            "2. VISUAL HIERARCHY: Every scene MUST have 1 'primary' element (largest), 1-2 'secondary' elements, and supporting labels. Eye-path must be clear.\n"
            "3. STAGGERED ENTRANCES: Elements MUST NOT appear simultaneously. Stagger 'start' frames by 15-20f waves (Wave 1: Title, Wave 2: Diagram, Wave 3: Stats).\n"
            "4. INFOGRAPHIC SYSTEMS: Procedural scenes MUST be connected stories. Use 'infographic_lines' (minimum 2 per scene) to link related SVGs. Use SVG icons only as helper nodes in a larger system, not isolated widgets.\n"
            "5. REAL NARRATIVE DATA: Visualize ACTUAL NUMBERS from story. NO placeholder values (10, 20, A, B). If text says '5 million', KPI must show '5M'.\n"
            "6. VIDEO SAFE-ZONES: If background_type='video', keep overlays to Columns 1 and 3. DO NOT obscure the center subjects of the video footage.\n"
            "7. WHITESPACE & BREATHING ROOM: Maintain 300px between Primary elements. Use 40/30/30 spatial balance.\n"
            "8. PERSISTENCE: Overlays stay until scene ends. duration = (scene_duration - start).\n"
            "9. PUNCHY VIBE TEXT: Keep 'content' for text overlays EXTREMELY BRIEF (3-5 words max). It should capture the 'vibe' or a 'core keyword' of the scene, not the full narration. Use dramatic and punchy language.\n"
            "10. HERO HIGHLIGHT: For every text overlay, you MUST identify one 'hero' word from the content and provide 'hero_config'.\n"
            "\nJSON SCHEMA:\n"
            "- 'scenes': [ { 'scene_id', 'duration', 'background_type': 'video'|'procedural', 'procedural_config', 'overlays': [], 'infographic_lines': [], 'groups': [] } ]\n"
            "- 'overlays': [\n"
            "    { 'id', 'type': 'text', 'content', 'font', 'start', 'duration', 'position': {x,y}, 'hero_config': { 'word': 'KEYWORD', 'animation': 'glow_pulse|neon_flicker|glitch_pop', 'color': '#00F5FF' } },\n"
            "    { 'id', 'type': 'svg', 'query', 'animation', 'style', 'importance': 'primary'|'secondary', 'start', 'duration', 'position': {x,y}, 'groupId'? },\n"
            "    { 'id', 'type': 'hub_network'|'flow_diagram', 'centerSvg', 'nodes'|'steps': [], 'start', 'duration', 'position': {x,y} },\n"
            "    { 'id', 'type': 'chart'|'shadcn_chart'|'shadcn_indicator', 'chart_type'|'indicator_type', 'title'|'label', 'data'|'value', 'start', 'duration', 'position': {x,y} }\n"
            "  ]\n"
            "\nAVAILABLE PRESETS:\n"
            "- 'procedural_config': 'dark_particles', 'liquid_gradient', 'neon_grid'.\n"
            "- 'chart_type': glass_area, neon_bar, radial_score, radar_web, step_area, multi_bar_stack.\n"
            "- 'indicator_type': metric_tile, tech_badge, activity_ring, crypto_card, server_status, data_ticker.\n"
            f"\nENV_FONTS: {local_fonts}\n"
            f"ENV_VIDEOS: {self.video_files}\n"
            f"REFERENCE: {schema_ref}\n"
            "\nTASK: OUTPUT RAW JSON BLOCK ONLY. NO PREAMBLE. NO CHATTER. NO ERROR MESSAGES."
        )
        if prompt_output_path:
            with open(prompt_output_path, 'w', encoding='utf-8') as f: f.write(full_prompt)

        print("\n" + "="*50)
        print("🚀 SENDING PROMPT TO GEMINI:")
        print(full_prompt)
        print("="*50 + "\n")

        raw_output = self._interact_with_gemini(full_prompt)

        print("\n" + "="*50)
        print("📥 RAW GEMINI RESPONSE:")
        print(raw_output)
        print("="*50 + "\n")

        print(f"📊 Raw Gemini output length: {len(raw_output)} chars.")
        if len(raw_output.strip()) < 50:
            print("❌ ERROR: Gemini returned an suspiciously short or empty response.")
            return {}

        try:
            # Enhanced JSON extraction: Prioritize the largest balanced object containing "scenes"
            json_str = None

            # 1. Look for markdown code blocks
            all_blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', raw_output, re.DOTALL)

            # 2. Also look for any balanced { } structures outside blocks
            all_starts = [m.start() for m in re.finditer('{', raw_output)]
            for s_idx in all_starts:
                candidate = raw_output[s_idx:]
                stack = 0
                end_pos = -1
                for i, char in enumerate(candidate):
                    if char == '{': stack += 1
                    elif char == '}':
                        stack -= 1
                        if stack == 0:
                            end_pos = i
                            break
                if end_pos != -1:
                    all_blocks.append(candidate[:end_pos+1])

            # Filter candidates that look like valid scenes manifest and pick the longest
            valid_candidates = [b for b in all_blocks if '"scenes"' in b]
            if valid_candidates:
                json_str = max(valid_candidates, key=len)
            elif all_blocks:
                json_str = max(all_blocks, key=len)

            if not json_str:
                print("❌ Could not find any valid JSON objects in Gemini response.")
                return {}

            # Pre-cleanup: Remove control characters except for standard whitespace
            json_str = "".join(ch for ch in json_str if ch.isprintable() or ch in "\n\r\t")

            # Cleanup comments and common syntax issues
            json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
            json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)

            try:
                # Use strict=False to handle unescaped control characters
                parsed = json.loads(json_str, strict=False)
                if isinstance(parsed, dict) and 'error' in parsed:
                    print(f"⚠️ Gemini returned an error JSON: {parsed['error']}")
                    # If it's a conversational error, it's a failure.
                    return {}

                # Validation: if it's a dict but doesn't have 'scenes', it might be conversational junk in a JSON wrapper
                if isinstance(parsed, dict) and 'scenes' not in parsed and len(parsed.keys()) < 3:
                     print(f"⚠️ Extracted JSON lacks 'scenes' and looks conversational. Rejecting.")
                     return {}

                return parsed
            except Exception as e:
                print(f"⚠️ JSON primary parse failed. Attempting repair...")
                result = self.repair_json(json_str)
                if result:
                    if isinstance(result, dict) and 'error' in result:
                        print(f"⚠️ Repaired JSON contains an error key: {result['error']}")
                        return {}
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
    parser.add_argument("--manual", action="store_true", help="Manual prompt interaction")
    parser.set_defaults(headless=True)
    args = parser.parse_args()
    if not os.path.exists(args.story_file): sys.exit(1)
    if os.path.exists(args.output): os.remove(args.output)
    with open(args.story_file, 'r', encoding='utf-8') as f: story = f.read()
    maker = RemotionJsonMaker(user_data_dir=args.user_data_dir, headless=args.headless, manual=args.manual)

    if args.fps_update_file:
        maker.load_fps_update(args.fps_update_file)

    # Use absolute paths where possible
    abs_public = os.path.abspath(args.public_dir)

    # Add project root to sys.path for scripts import
    project_root = os.path.dirname(abs_public)
    if project_root not in sys.path:
        sys.path.append(project_root)

    maker.scan_assets(abs_public)
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

        expected_scenes = len(scene_durations)
        if render_json and 'scenes' in render_json:
             actual_scenes = len(render_json['scenes'])
             if actual_scenes < expected_scenes:
                 print(f"⚠️ Warning: Gemini generated only {actual_scenes}/{expected_scenes} scenes.")

        if not render_json:
             print("❌ ERROR: Gemini failed to produce any JSON.")
             sys.exit(1)

        if 'scenes' not in render_json or not render_json['scenes']:
             print("❌ ERROR: Generated JSON contains no scenes. Manifest is invalid.")
             print(f"DEBUG: Keys found in JSON: {list(render_json.keys())}")
             sys.exit(1)

        render_json = maker.finalize_json_durations(render_json, public_dir=abs_public)
        output_dir = os.path.dirname(args.output)
        if not os.path.exists(output_dir): os.makedirs(output_dir, exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(render_json, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        print(f"✅ Master JSON created: {args.output} ({os.path.getsize(args.output)} bytes)")

        # 3. Quality Assurance Pass
        print("\n🧪 --- RUNNING QUALITY ASSURANCE PASS ---")
        try:
            from scripts.test_manifest_quality import test_manifest_quality
            test_manifest_quality(args.output)
        except ImportError:
            print("⚠️ QA Script not found. Skipping validation.")

        try: shutil.copy(args.output, "/content/remotion_render.json")
        except: pass
    except Exception as e:
        print(f"❌ Error in main: {e}")
        sys.exit(1)
if __name__ == "__main__": main()
