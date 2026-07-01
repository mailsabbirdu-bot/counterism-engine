import os
import sys
import json
import argparse
import re
import time
import subprocess
import shutil
import math
from typing import Dict, Any, List, Optional, Tuple
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
        self.visual_analysis = {}
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

    def load_visual_analysis(self, public_dir: str):
        analysis_dir = os.path.join(public_dir, "renders/analysis")
        if not os.path.exists(analysis_dir): return

        print(f"👁️ Loading Visual Eye analysis from: {analysis_dir}")
        for f in os.listdir(analysis_dir):
            if f.endswith(".summary.json"):
                v_name = f.replace(".summary.json", ".mp4")
                try:
                    with open(os.path.join(analysis_dir, f), 'r') as jf:
                        self.visual_analysis[v_name] = json.load(jf)
                except: pass

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
        print(f"🎬 SCANNING ASSETS in {abs_public}...")
        self.bangla_fonts = []
        self.english_fonts = []
        BANGLA_KEYWORDS = ['solaiman', 'kalpurush', 'nikosh', 'hind', 'siliguri', 'adorsho', 'sutonny', 'shonar', 'vrinda', 'bangla', 'liyakats', 'anshu', 'charukola', 'galada', 'mina', 'mukti', 'atreyee', 'benisen', 'bengali', 'shishir', 'shorif', 'maharaj', '_bangla', 'bangla']

        if os.path.exists(fonts_dir):
            print(f"🔍 Font Detection: Scanning {fonts_dir}...")
            for root, dirs, files in os.walk(fonts_dir, followlinks=True):
                for file in files:
                    if file.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
                        name = os.path.splitext(file)[0]
                        # Robustly clean font names by removing common suffixes
                        clean_name = re.sub(r'(_english|_bangla)$', '', name, flags=re.IGNORECASE)
                        clean_name = re.sub(r'-(Regular|Bold|Italic|Light|Medium|Thin|SemiBold|ExtraBold|Black)$', '', clean_name, flags=re.IGNORECASE)

                        if any(kw in name.lower() for kw in BANGLA_KEYWORDS):
                            self.bangla_fonts.append(name) # Keep original name for Remotion loading
                            print(f"   🇧🇩 Found Bangla Font: {name}")
                        else:
                            self.english_fonts.append(name)
                            print(f"   🇬🇧 Found English Font: {name}")
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
        self.load_visual_analysis(abs_public)

    def finalize_json_durations(self, data: Dict[str, Any], public_dir: str = "../public") -> Dict[str, Any]:
        """Hardens layout, timing, camera, and assets with Geometry-Aware Logic and Adaptive Scaling."""
        if not data or not data.get('scenes'): return data

        abs_public = os.path.abspath(public_dir)
        print(f"🛠️ HARDENING ENGINE: Resolving spatial collisions and cinematic timing...")

        TYPE_SIZES = {
            'text': (800, 200), 'chart': (1000, 562), 'shadcn_chart': (1000, 562),
            'ui_panel': (800, 600), 'data_indicator': (500, 375), 'shadcn_indicator': (500, 375),
            'svg': (400, 400), 'kpi': (450, 400), 'kpi_card': (450, 400),
            'timeline': (1200, 300), 'hub_network': (800, 800), 'flow_diagram': (1000, 562), 'process': (1000, 562),
            'media': (960, 540), 'image': (960, 540), 'video': (960, 540),
            'label': (300, 100), 'callout': (400, 200), 'compositions': (1200, 675), 'groups': (1200, 675),
            'graph': (1000, 700), 'shape': (400, 400), 'data_emphasis': (600, 200), 'ambient_graphic': (1920, 1080),
            'connector': (400, 100)
        }

        SEMANTIC_ANIMS = ["wordReveal", "glassReveal", "networkGrow", "barsRise", "cinematicGlow", "fadeScale", "parallaxDrift", "maskReveal", "lineDraw", "particleAssembly", "blurFocus", "svgMorph", "depthZoom"]
        MIN_FONT_SIZE = 40
        MIN_CHART_W, MIN_CHART_H = 300, 200
        MIN_SVG_W, MIN_SVG_H = 100, 100
        MIN_SPACING = 30
        MODERN_COLORS = ["#00F5FF", "#FFD700", "#FF3E6C", "#00FFAB"]
        VALID_TEXT_ANIMS = [
            'glow_pulse', 'isolate_zoom', 'bounce_pop', 'neon_flicker', 'shake_alert',
            'rainbow_flow', 'ghost_trail', 'glitch_pop', 'wave_float', 'expand_contract',
            'blur_reveal', 'color_shift', 'rotation_swing', 'shadow_pulse', 'letter_jump',
            'skew_slide', 'tilt_pan', 'bounce_gravity', 'border_glow', 'glass_shimmer',
            'heartbeat', 'strobe_flash', 'threed_flip', 'magnetic_pull', 'fire_glow',
            'pixel_scatter', 'swing_pivot', 'depth_shadow', 'energy_beam', 'spiral_in',
            'fly_in_z', 'typewriter_flicker', 'vibrate_intense', 'float_orbit',
            'mirror_split', 'zoom_blur_pop', 'liquid_waver'
        ]
        LOCKED_FIELDS = ["content", "hero_config", "tracking"]

        # Production-Grade Grid Anchors (Rule of Thirds)
        ANCHORS = {
            "L_TOP": (550, 320), "C_TOP": (960, 320), "R_TOP": (1370, 320),
            "L_MID": (550, 540), "C_MID": (960, 540), "R_MID": (1370, 540),
            "L_BOT": (550, 760), "C_BOT": (960, 760), "R_BOT": (1370, 760)
        }

        CLAMP_MIN_X, CLAMP_MAX_X = 150, 1770
        CLAMP_MIN_Y, CLAMP_MAX_Y = 150, 930

        PRIORITY = {
            'hero': 1000, 'text': 100, 'hub_network': 90, 'flow_diagram': 90, 'process': 90,
            'chart': 80, 'shadcn_chart': 80, 'kpi_card': 80, 'timeline': 75, 'ui_panel': 60,
            'compositions': 55, 'groups': 55, 'data_indicator': 50, 'shadcn_indicator': 50,
            'label': 45, 'callout': 45, 'svg': 40, 'kpi': 40, 'graph': 30, 'shape': 10, 'background': 0
        }

        sfx_manifest = []
        in_ptr = 0

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
            # PRODUCTION OVERRIDE: Always mute background video to prevent double-audio with narration
            scene['audio_enabled'] = False

            pattern = f"SC_{id_num:02d}".lower()
            narration_file = next((f for f in self.narration_files if pattern in f.lower()), None)
            if narration_file:
                sfx_manifest.append({"scene_id": s_id, "file": narration_file, "start": 0, "end": scene_duration, "volume": 1.0})

            if not scene.get('overlays'):
                for k in ['elements', 'layers', 'visuals']:
                    if scene.get(k) and isinstance(scene[k], list): scene['overlays'] = scene[k]; break
            if not scene.get('overlays'): scene['overlays'] = []

            valid_overlays = []
            text_count, focal_count, svg_count = 0, 0, 0
            is_scene_bangla = self._is_bangla(self.story_scenes.get(s_id, ""))

            raw_overlays = scene['overlays'] if isinstance(scene['overlays'], list) else [scene['overlays']]
            for ov in raw_overlays:
                o_type = str(ov.get('type', 'text')).lower()
                if 'chart_type' in ov: o_type = 'shadcn_chart'
                if 'indicator_type' in ov: o_type = 'shadcn_indicator'

                # Extract content for font decision
                content = str(ov.get('content', ov.get('text', ov.get('label', ov.get('title', ''))))).strip()
                is_content_bangla = self._is_bangla(content)

                if o_type == 'text':
                    if text_count >= 3: continue
                    text_count += 1
                    if not content:
                        story_text = self.story_scenes.get(s_id, "")
                        content = " ".join(story_text.split()[:6]) if story_text else "STUDIO V4"
                    ov['content'] = content
                    ov['type'] = 'text'
                elif o_type in ['chart', 'shadcn_chart', 'hub_network', 'flow_diagram', 'process', 'kpi_card', 'timeline', 'compositions', 'groups']:
                    if focal_count >= 3: continue
                    focal_count += 1
                elif o_type in ['svg', 'label', 'callout', 'data_indicator', 'shadcn_indicator', 'shape', 'graph', 'ambient_graphic']:
                    if svg_count >= 12: continue
                    svg_count += 1

                if not ov.get('id'): ov['id'] = f"ov_{id_num}_{len(valid_overlays)+1}"

                # SURGICAL FONT ENFORCEMENT
                all_scanned_fonts = self.bangla_fonts + self.english_fonts
                ai_font = ov.get('font')

                # Logic: Content Language > Scene Language > First Scanned Font > Fallback
                if is_content_bangla and self.bangla_fonts:
                    # Content is Bangla: Use Bangla font
                    if ai_font in self.bangla_fonts: pass
                    else: ov['font'] = "Sohid_bangla" if "Sohid_bangla" in self.bangla_fonts else self.bangla_fonts[0]
                elif not is_content_bangla and self.english_fonts:
                    # Content is English/Latin: Use English font
                    if ai_font in self.english_fonts: pass
                    else: ov['font'] = self.english_fonts[0]
                elif is_scene_bangla and self.bangla_fonts:
                    # Content is neutral but scene is Bangla
                    ov['font'] = "Sohid_bangla" if "Sohid_bangla" in self.bangla_fonts else self.bangla_fonts[0]
                elif self.english_fonts:
                    # Last resort: first English font
                    if ai_font in self.english_fonts: pass
                    else: ov['font'] = self.english_fonts[0]
                elif not ov.get('font') or ov.get('font') not in all_scanned_fonts:
                    ov['font'] = "Arial"

                if ov['type'] == 'text':
                    ov['maxWidth'] = ov.get('maxWidth', 800)
                    if not ov.get('hero_config'):
                        hero = self._get_scene_hero_word(s_id, ov['content'], scene_duration)
                        if not hero: hero = self._get_fallback_hero(ov['content'])
                        if hero: ov['hero_config'] = {"word": hero['word'], "start": hero['start'], "color": MODERN_COLORS[(scene_idx + 2) % len(MODERN_COLORS)], "animation": VALID_TEXT_ANIMS[scene_idx % len(VALID_TEXT_ANIMS)]}
                    ov['color'] = MODERN_COLORS[scene_idx % len(MODERN_COLORS)]
                    ov['fontSize'] = ov.get('fontSize', "120px")
                valid_overlays.append(ov)

            valid_overlays.sort(key=lambda o: PRIORITY.get(str(o.get('type')).lower(), 0), reverse=True)
            placed_boxes = []
            stagger_step = min(30, max(10, scene_duration // (len(valid_overlays) + 2)))

            # PROACTIVE ANTI-CENTERING & ANCHORING
            scene_analysis = self.visual_analysis.get(filename, {})
            recommended_region = scene_analysis.get("text_region", {}).get("preferred", "center")

            for i, ov in enumerate(valid_overlays):
                o_type = str(ov.get('type', 'text')).lower()
                if o_type in ['graph', 'shape']: ov['start'] = 0
                elif PRIORITY.get(o_type, 0) < 50: ov['start'] = 5
                else: ov['start'] = 15 + i * stagger_step
                ov['duration'] = max(30, scene_duration - ov['start'] - 30)
                if not ov.get('exitAnimation'): ov['exitAnimation'] = "fade_out" if o_type != 'text' else "slide_down"

                base_w, base_h = TYPE_SIZES.get(o_type, (600, 400))
                imp = str(ov.get('importance', '')).lower()
                if imp == 'hero': ov['depth'], ov['parallax'] = 100, 1.0
                elif imp == 'secondary': ov['depth'], ov['parallax'] = 50, 0.8
                elif imp == 'ambient': ov['depth'], ov['parallax'] = -50, 0.5
                elif imp == 'background': ov['depth'], ov['parallax'] = -100, 0.2
                else:
                    prio = PRIORITY.get(o_type, 40)
                    ov['depth'], ov['parallax'] = prio - 50, max(0.2, min(1.0, prio / 100.0))

                pos = ov.get('position', {})
                ax, ay = int(pos.get('x', 960)), int(pos.get('y', 540))

                # Pre-Hardening Safety Clamp: Ensure initial pos isn't crazy
                ax = max(CLAMP_MIN_X, min(CLAMP_MAX_X, ax))
                ay = max(CLAMP_MIN_Y, min(CLAMP_MAX_Y, ay))

                # Studio V4 Aggressive Anti-Centering (Studio-Grade Layouts)
                # Widened "Death Zone" to +/- 200px to force Rule of Thirds variety
                if abs(ax - 960) < 200 and (abs(ay - 540) < 150 or abs(ay - 700) < 150):
                    # Force elements away from the generic center "death zone"
                    if "left" in recommended_region: ax, ay = ANCHORS["L_MID"]
                    elif "right" in recommended_region: ax, ay = ANCHORS["R_MID"]
                    elif "top" in recommended_region: ax, ay = ANCHORS["C_TOP"]
                    elif "bottom" in recommended_region: ax, ay = ANCHORS["C_BOT"]
                    else:
                        # Cyclic distribution based on index to ensure professional spacing
                        layout_targets = [ANCHORS["L_MID"], ANCHORS["R_MID"], ANCHORS["L_TOP"], ANCHORS["R_BOT"]]
                        ax, ay = layout_targets[i % len(layout_targets)]

                # Snapping to closest production grid anchor
                if not ov.get('tracking', {}).get('enabled'):
                    for anchor_name, (grid_x, grid_y) in ANCHORS.items():
                        if abs(ax - grid_x) < 180 and abs(ay - grid_y) < 180:
                            ax, ay = grid_x, grid_y; break

                found = False
                best_pos, final_w, final_h = (ax, ay), base_w, base_h
                fs = int(re.search(r'\d+', str(ov.get('fontSize', '120'))).group()) if o_type == 'text' else 120

                for scale_step in range(7):
                    scale = 1.0 - (scale_step * 0.15)
                    # Protect Hero elements from downscaling
                    if imp == 'hero' and scale < 1.0: break

                    if o_type in ['graph', 'shape']: scale = min(scale, 0.8)
                    if o_type == 'text':
                        curr_fs = max(MIN_FONT_SIZE, int(fs * scale))
                        w = min(ov.get('maxWidth', 800), len(ov['content']) * curr_fs * 0.7)
                        h = curr_fs * 1.5
                    else:
                        w = max(MIN_CHART_W if 'chart' in o_type else MIN_SVG_W, base_w * scale)
                        h = max(MIN_CHART_H if 'chart' in o_type else MIN_SVG_H, base_h * scale)

                    for step in range(0, 80):
                        radius = step * 15
                        angles = [0, 180, 90, 270, 45, 135, 225, 315] if radius > 0 else [0]
                        for angle in angles:
                            rad = math.radians(angle)
                            cx, cy = ax + radius * math.cos(rad), ay + radius * math.sin(rad)
                            l, t, r, b = cx-w/2, cy-h/2, cx+w/2, cy+h/2
                            if l < CLAMP_MIN_X or r > CLAMP_MAX_X or t < CLAMP_MIN_Y or b > CLAMP_MAX_Y: continue
                            collision = False
                            for p_id, p_l, p_t, p_r, p_b, p_s, p_e in placed_boxes:
                                if max(ov['start'], p_s) < min(ov['start']+ov['duration'], p_e):
                                    if not (r + MIN_SPACING < p_l or l - MIN_SPACING > p_r or b + MIN_SPACING < p_t or t - MIN_SPACING > p_b):
                                        collision = True; break
                            if not collision:
                                best_pos, found = (cx, cy), True
                                if radius > 80:
                                    print(f"   🔧 Expert Nudging {ov['id']} to resolve overlap -> New Pos: ({int(cx)}, {int(cy)})")
                                    if not ov.get('animation') or ov.get('animation') not in SEMANTIC_ANIMS:
                                        ov['animation'] = SEMANTIC_ANIMS[scene_idx % len(SEMANTIC_ANIMS)]
                                if scale < 1.0:
                                    print(f"   🔧 Scaling down {ov['id']} to {int(scale*100)}% to fit")
                                    if o_type == 'text': ov['fontSize'] = f"{int(curr_fs)}px"
                                    else: ov['width'], ov['height'] = int(w), int(h)
                                final_w, final_h = (w if o_type != 'text' else min(1600, len(ov['content']) * int(curr_fs) * 0.7)), (h if o_type != 'text' else int(curr_fs) * 1.5)
                                break
                        if found: break
                    if found: break

                ov['position'] = {"x": int(best_pos[0]), "y": int(best_pos[1])}
                ov['visual_anchor'] = True
                if ov.get('hero_config'): ov['hero_config']['start'] = max(ov['start'] + 10, ov['hero_config'].get('start', 0))
                placed_boxes.append((ov['id'], best_pos[0]-final_w/2, best_pos[1]-final_h/2, best_pos[0]+final_w/2, best_pos[1]+final_h/2, ov['start'], ov['start']+ov['duration']))

            # PRODUCTION SYNC: Auto-sort overlays by 'start' time to prevent chronological array sequence errors.
            valid_overlays.sort(key=lambda o: (int(o.get('start', 0)), PRIORITY.get(str(o.get('type')).lower(), 0)))
            scene['overlays'] = valid_overlays
            if 'transition' not in scene: scene['transition'] = {"type": "cinematicMatchCut", "duration": 15}
            if 'beats' not in scene: scene['beats'] = [{"frame": o['start'], "event": f"{o['id']}_reveal"} for o in valid_overlays if PRIORITY.get(o['type'], 0) >= 50]
            if 'connections' not in scene: scene['connections'] = []

            hero_ids = [o['id'] for o in valid_overlays if str(o.get('importance', '')).lower() == 'hero' or PRIORITY.get(o['type'], 0) >= 100]
            focal_ids = [o['id'] for o in valid_overlays if PRIORITY.get(str(o.get('type')).lower(), 0) >= 50 and o['id'] not in hero_ids]
            background_ids = [o['id'] for o in valid_overlays if PRIORITY.get(str(o.get('type')).lower(), 0) < 50]

            ai_shots = scene.get('camera', {}).get('shots', [])
            if not ai_shots or not all(s.get('targetId') in [o['id'] for o in valid_overlays] for s in ai_shots):
                CAM_STYLES = ["cinematic_drift", "slow_push", "pan_right", "orbit", "rack_focus", "dramatic_reveal"]
                shots = []
                if background_ids: shots.append({"targetId": background_ids[0], "startFrame": 0, "duration": 45, "style": "cinematic_drift", "zoom": 1.05, "inDuration": 15})
                ordered_targets = sorted([o for o in valid_overlays if o['id'] in (hero_ids + focal_ids)], key=lambda x: x['start'])
                for i, ov in enumerate(ordered_targets[:4]):
                    start = max(shots[-1]['startFrame'] + 10, ov['start']) if shots else ov['start']
                    if shots: shots[-1]['duration'] = max(20, start - shots[-1]['startFrame'])
                    shots.append({"targetId": ov['id'], "startFrame": start, "duration": 60, "style": CAM_STYLES[(scene_idx + i) % len(CAM_STYLES)], "zoom": 1.1 + (i * 0.05), "inDuration": 20, "ease": "cubicOut"})
                if shots: shots[-1]['duration'] = max(30, scene_duration - shots[-1]['startFrame'])
                scene['camera'] = {"enabled": True, "shots": shots}
            else:
                scene['camera']['enabled'] = True
                for shot in scene['camera']['shots']: shot['ease'] = shot.get('ease', "cubicOut")

            for i, ov in enumerate(valid_overlays):
                if self.in_files: sfx_manifest.append({"scene_id": s_id, "file": self.in_files[(in_ptr+i)%len(self.in_files)], "start": ov['start'], "end": ov['start']+30, "volume": 0.05})
            in_ptr += len(valid_overlays)

        data['audio_sfx_manifest'] = sfx_manifest
        return data

    def _get_scene_hero_word(self, scene_id: str, overlay_content: str, scene_duration: int = 180):
        if not self.raw_timestamps or not overlay_content: return None
        matches = re.findall(fr'{scene_id}:.*?\[30fps:\s*(\d+)f\s*-\s*\d+f\]\s*"(.*?)"', self.raw_timestamps)
        content_words = re.sub(r'[.।]', '', overlay_content).split()
        candidates = [{"word": w, "start": int(f)} for f, w in matches if re.sub(r'[.।]', '', w) in content_words]
        if not candidates: return None
        hero = max(candidates, key=lambda x: len(x['word']))
        hero['start'] = max(30, min(hero['start'], scene_duration - 60))
        return hero

    def _get_fallback_hero(self, overlay_content: str):
        words = re.sub(r'[.।]', '', str(overlay_content)).split()
        return {"word": max(words, key=len), "start": 45} if words else None

    def _interact_with_gemini(self, prompt: str, previous_json: str = None, errors: List[str] = None, score: int = 0) -> str:
        if self.manual:
            try:
                from google.colab import output
                import uuid
                u_id = uuid.uuid4().hex[:8]
                feedback_html = ""
                header_color = "#4CAF50" if score >= 100 else "#FF9800" if score >= 80 else "#FF3E6C"

                if errors:
                    err_list = "".join([f"<li>{e}</li>" for e in errors])
                    feedback_html = f"""<div style='color: #FF3E6C; margin-bottom: 15px; border-left: 4px solid #FF3E6C; padding-left: 15px; background: #1a0a0d; padding: 10px;'>
                        <strong style='font-size: 16px;'>🚨 QA FEEDBACK (CURRENT SCORE: {score}%)</strong>
                        <ul style='margin-top: 8px; font-size: 13px; color: #ff85a1;'>{err_list}</ul>
                    </div>"""

                copy_payload = prompt
                if previous_json:
                    protocol = """
--- PRODUCTION CORRECTION PROTOCOL (STRICT) ---
You have FAILED the quality assurance pass. You must REPAIR the manifest using the surgical feedback below.

1. MANDATORY DIAGNOSTIC: List each error from the 'ERROR LIST' below and state the EXACT numerical change you are making to fix it.
2. GEOMETRY: Use the suggested coordinates. Rule of Thirds Anchors: L_MID(550, 540), R_MID(1370, 540), C_TOP(960, 320), C_BOT(960, 760).
3. SYNC: Re-order the 'overlays' array objects so that 'start' times strictly increase.
4. INTEGRITY: Do NOT alter narration content, hero words, or timestamps unless fixing an out-of-bounds error.
5. OUTPUT: Provide the Diagnostic List first, then the Entire Corrected RAW JSON Block. No conversational chatter.
"""
                    copy_payload = f"🚨 URGENT: PRODUCTION ERRORS DETECTED ({score}% ACCURACY)\n\n--- ERROR LIST ---\n{chr(10).join(errors)}\n\n{protocol}\n\n--- PREVIOUS JSON ---\n{previous_json}\n\n--- ORIGINAL TASK CONTEXT ---\n{prompt}"

                js_code = f"""
                    (async () => {{
                        const u_id = "{u_id}";
                        const container = document.createElement('div');
                        container.style = "background: #0a0a0a; color: #fff; padding: 25px; border-radius: 16px; border: 2px solid {header_color}; font-family: 'Segoe UI', Tahoma, sans-serif; max-width: 850px; margin: 20px auto; box-shadow: 0 10px 30px rgba(0,0,0,0.5);";
                        container.innerHTML = `
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                                <h3 style="color: {header_color}; margin: 0; font-size: 22px;">🎬 Studio V4 Production Pipeline</h3>
                                <span style="background: {header_color}; color: #000; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 14px;">ACCURACY: {score}%</span>
                            </div>
                            {feedback_html}
                            <div style="background: #111; padding: 15px; border-radius: 8px; border: 1px solid #333; margin-bottom: 15px;">
                                <p style="margin: 0 0 10px 0; font-size: 14px; color: #aaa;">1. Copy the instructions and failed JSON.</p>
                                <button id="copy-${{u_id}}" style="background: {header_color}; color: #000; border: none; padding: 12px; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; transition: opacity 0.2s;">📋 COPY PROMPT & FEEDBACK</button>
                            </div>
                            <div style="background: #111; padding: 15px; border-radius: 8px; border: 1px solid #333;">
                                <p style="margin: 0 0 10px 0; font-size: 14px; color: #aaa;">2. Paste Gemini's corrected response below.</p>
                                <textarea id="paste-${{u_id}}" style="width: 100%; height: 250px; background: #000; color: #00FFAB; border: 1px solid #444; padding: 12px; font-family: 'Cascadia Code', 'Courier New', monospace; font-size: 13px; border-radius: 6px; resize: vertical;" placeholder="Paste corrected JSON block here..."></textarea>
                                <div style="display: flex; gap: 10px; margin-top: 15px;">
                                    <button id="submit-${{u_id}}" style="flex: 2; background: #2196F3; color: #fff; border: none; padding: 14px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 16px; box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);">🚀 SUBMIT FOR HARDENING</button>
                                    <button id="force-${{u_id}}" style="flex: 1; background: #FF3E6C; color: #fff; border: none; padding: 14px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px; box-shadow: 0 4px 15px rgba(255, 62, 108, 0.3);">🛑 END & FINALIZE</button>
                                </div>
                            </div>
                        `;
                        document.body.appendChild(container);
                        document.getElementById('copy-'+u_id).onclick = () => {{
                            navigator.clipboard.writeText({json.dumps(copy_payload)});
                            document.getElementById('copy-'+u_id).innerText = "COPIED!";
                        }};
                        return new Promise((resolve) => {{
                            document.getElementById('submit-'+u_id).onclick = () => {{
                                const val = document.getElementById('paste-'+u_id).value.trim();
                                if (!val) {{ alert("Please paste Gemini's response first."); return; }}
                                if (!val.startsWith('{{')) {{ alert("Invalid input. Please paste a raw JSON block."); return; }}
                                container.remove(); resolve(val);
                            }};
                            document.getElementById('force-'+u_id).onclick = () => {{
                                const val = document.getElementById('paste-'+u_id).value.trim();
                                if (window.confirm("🛑 STOP ITERATIONS?\\n\\nThis will end the AI generation loop and save current files even if accuracy is not 100%. Proceed?")) {{
                                    container.remove(); resolve("FORCE_QUIT_SIGNAL:" + val);
                                }}
                            }};
                        }});
                    }})();
                """
                return output.eval_js(js_code)
            except:
                val = ""
                while not val.strip():
                    val = input("Paste Gemini JSON (Required): ").strip()
                return val
        return ""

    def _compact_timestamps(self, ts_content: str) -> str:
        self.raw_timestamps = ts_content
        if not ts_content: return ""
        matches = re.findall(r'(SCENE_\d+):.*?\[30fps:\s*(\d+)f\s*-\s*\d+f\]\s*"(.*?)"', ts_content)
        return " | ".join([f"{m[0]}:{m[1]}f \"{m[2]}\"" for m in matches])

    def _is_bangla(self, text: str) -> bool:
        return any('\u0980' <= c <= '\u09FF' for c in str(text))

    def generate(self, story: str, prompt_output_path: str = None, timestamp_context: str = None, scene_durations: List[int] = None, drive_prompt_path: str = None,
                 previous_json: str = None, feedback_errors: List[str] = None, current_score: int = 0, interaction_log_path: str = None) -> Tuple[Dict[str, Any], bool]:
        pattern = r'(?:Scene|দৃশ্য)\s+[0-9০-৯]+[:\s]*'
        story_parts = [p.strip().lstrip(':').strip() for p in re.split(pattern, story, flags=re.IGNORECASE) if p.strip()]
        for i, n in enumerate(story_parts, 1): self.story_scenes[f"SCENE_{i:02d}"] = n
        compact_ts = self._compact_timestamps(timestamp_context)
        duration_context = ", ".join([f"SCENE_{i+1:02d}:{d}f" for i, d in enumerate(scene_durations)]) if scene_durations else ""

        drive_guideline = ""
        if drive_prompt_path and os.path.exists(drive_prompt_path):
            try:
                with open(drive_prompt_path, 'r', encoding='utf-8') as f: drive_guideline = f"\n--- DIRECTOR'S GUIDELINES ---\n{f.read()}\n"
            except: pass

        visual_context = ""
        if self.visual_analysis:
            visual_context = "\n--- VISUAL PERCEPTION DATA (PRODUCTION GROUNDING) ---\n"
            for v_name, analysis in self.visual_analysis.items():
                s_id = v_name.replace("scene_SC_", "SCENE_").replace(".mp4", "").upper()
                v_desc = analysis.get("semantic_description", "")
                v_style = analysis.get("visual_style", {})

                track_info = ""
                hero = analysis.get("hero_subject", {})
                if hero and hero.get("type"):
                    track_info = f" [TRACKABLE: {hero['type']} as 'hero_track']"

                visual_context += f"- {s_id}: {v_desc}{track_info} (Style: Brightness={v_style.get('brightness', 0):.2f}, Contrast={v_style.get('contrast', 0):.2f})\n"

        full_prompt = (
            f"TASK: GENERATE A PRODUCTION-READY CINEMATIC MOTION GRAPHICS MANIFEST.\n\n"
            f"--- SOURCE CONTENT ---\n"
            f"STORY:\n{story}\n"
            f"TIMESTAMPS: {compact_ts}\n"
            f"DURATIONS: {duration_context}\n"
            f"{visual_context}\n"
            f"--- PROJECT ASSETS ---\n"
            f"ENV_FONTS: BANGLA: {self.bangla_fonts} | ENGLISH: {self.english_fonts}\n"
            f"ENV_VIDEOS: {self.video_files}\n\n"
            f"--- SYSTEM ROLE & CORE RULES ---\n"
            f"ROLE: WORLD-CLASS CINEMATIC MOTION DESIGNER (Vox/Polymatter Style).\n"
            f"1. TYPOGRAPHY: Bangla text MUST use a font from the BANGLA list. English uses ENGLISH list. Use concise 2-3 word headers.\n"
            f"2. COMPOSITION: Use the Rule of Thirds. Stop centering everything. Use negative space identified in VISUAL PERCEPTION DATA.\n"
            f"3. SYNC: Match 'start' and 'duration' strictly to TIMESTAMPS. Sort overlays by entry time.\n"
            f"4. BACKGROUND: Always use 'background_type': 'video'. video_path: 'renders/scene_SC_XX.mp4'. Set 'audio_enabled': false.\n"
            f"5. CAMERA: Every scene MUST have a camera 'shot' targeting a valid overlay ID. Use 'slow_push' or 'cinematic_drift'.\n"
            f"6. MOTION TRACKING: If a subject is 'TRACKABLE', use 'tracking': {{ 'enabled': true, 'target': 'hero_track', 'offset': {{ 'x': 0, 'y': -80 }} }}.\n\n"
            f"--- COMPONENT PRESETS ---\n"
            f"CHARTS: glass_area, neon_bar, stacked_line, radial_score, radar_web, pie_donut_glass, step_area, multi_bar_stack, bar_race_top, thick_line_glow, area, bar, line.\n"
            f"INDICATORS: metric_tile, tech_badge, activity_ring, crypto_card, server_status, data_ticker, notification_stack, kpiNumber, deltaIndicator, semiGauge, milestoneTimeline, statGrid, batteryLevel.\n"
            f"HERO ANIMATIONS: glow_pulse, isolate_zoom, bounce_pop, neon_flicker, shake_alert, rainbow_flow, glitch_pop, wave_float, blur_reveal, glass_shimmer, heartbeat, fire_glow.\n\n"
            f"--- DATA SCHEMA ENFORCEMENT ---\n"
            f"- 'milestoneTimeline' requires 'events': [ {{ 'title': '...', 'date': '...', 'description': '...' }} ].\n"
            f"- 'statGrid' requires 'stats': [ {{ 'label': '...', 'value': 80, 'suffix': '%' }} ].\n"
            f"- 'stepIndicator' requires 'steps': [ 'Step 1', 'Step 2' ].\n\n"
            f"{drive_guideline}\n"
            f"OUTPUT RAW JSON BLOCK ONLY. NO PREAMBLE. NO CHATTER."
        )
        if prompt_output_path:
            with open(prompt_output_path, 'w', encoding='utf-8') as f: f.write(full_prompt)

        raw_output = self._interact_with_gemini(full_prompt, previous_json, feedback_errors, current_score)
        force_stop = False
        if raw_output.startswith("FORCE_QUIT_SIGNAL:"):
            force_stop = True
            raw_output = raw_output.replace("FORCE_QUIT_SIGNAL:", "")
            print("🛑 Force-finalize requested by user.")

        if interaction_log_path:
            try:
                with open(interaction_log_path, 'a', encoding='utf-8') as log_f:
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    log_f.write(f"\n\n{'='*80}\n")
                    log_f.write(f"🕒 ITERATION LOG: {timestamp}\n")
                    log_f.write(f"📊 CURRENT SCORE: {current_score}%\n")
                    log_f.write(f"{'='*80}\n\n")

                    if previous_json:
                        log_f.write(f"--- PREVIOUS JSON ---\n{previous_json}\n\n")
                    if feedback_errors:
                        log_f.write(f"--- FEEDBACK ERRORS ---\n{chr(10).join(feedback_errors)}\n\n")

                    log_f.write(f"--- FULL PROMPT SENT ---\n{full_prompt}\n\n")
                    log_f.write(f"--- RAW RESPONSE RECEIVED ---\n{raw_output}\n\n")
            except Exception as e:
                print(f"⚠️ Failed to write to interaction log: {e}")

        try:
            blocks = re.findall(r'\{.*\}', raw_output, re.DOTALL)
            if blocks:
                json_str = max(blocks, key=len)
                data = json.loads(json_str, strict=False)
                return data, force_stop
            return {}, force_stop
        except: return {}, force_stop

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

    story = open(args.story_file, 'r', encoding='utf-8').read() if os.path.exists(args.story_file) else ""
    ts_content = open(args.timestamp_file, 'r', encoding='utf-8').read() if args.timestamp_file and os.path.exists(args.timestamp_file) else None
    scene_durations = [maker.fps_cache[f"scene_SC_{i:02d}.mp4"] for i in range(1, 100) if f"scene_SC_{i:02d}.mp4" in maker.fps_cache]

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scripts.test_manifest_quality import test_manifest_quality

    iteration = 1
    previous_json = None
    feedback_errors = None
    current_score = 0
    best_score = -1
    best_json = None

    manifest_dir = os.path.dirname(args.output)
    interaction_log = os.path.join(manifest_dir, "interaction_log.txt")

    while iteration <= 10: # Increased attempts for production perfection
        print(f"\n🚀 ITERATION {iteration}: AI Generation & Hardening...")
        render_json, force_stop = maker.generate(story, args.prompt_output, ts_content, scene_durations, args.drive_prompt,
                                     previous_json, feedback_errors, current_score, interaction_log_path=interaction_log)

        if not render_json and not force_stop:
            print("⚠️ Failed to parse AI output. Retrying...")
            iteration += 1
            continue

        # Post-Paste Hardening
        render_json = maker.finalize_json_durations(render_json, public_dir=args.public_dir)

        # Final pass verification for mandatory fields before QA & Save
        for scene in render_json.get('scenes', []):
            for ov in scene.get('overlays', []):
                o_type = str(ov.get('type')).lower()
                var = ov.get('indicator_type') or ov.get('chart_type')
                if var == 'milestoneTracker' and 'milestones' not in ov:
                    ov['milestones'] = [{"label": "Milestone 1", "date": "T-0"}]
                if var in ['timeline', 'milestoneTimeline'] and 'events' not in ov and 'milestones' not in ov:
                    ov['events'] = [{"title": "Event 1", "date": "Start", "description": "System activated."}]
                if var == 'statGrid' and 'stats' not in ov:
                    ov['stats'] = [{"label": "Metric 1", "value": 85, "suffix": "%"}, {"label": "Metric 2", "value": 92, "suffix": "%"}]
                if var in ['multiProgress', 'ringChart'] and 'items' not in ov and 'rings' not in ov:
                    ov['items'] = [{"label": "Process A", "value": 75, "color": "#00F5FF"}]
                if var in ['stepIndicator', 'step_indicator_glass'] and 'steps' not in ov:
                    ov['steps'] = ["Initiate", "Process", "Complete"]

        # Save temporarily for QA
        with open(args.output, 'w', encoding='utf-8') as f: json.dump(render_json, f, indent=2, ensure_ascii=False)

        print(f"🧪 STAGE 3: Production QA (Iteration {iteration})...")
        success, score, feedback = test_manifest_quality(args.output, args.public_dir)
        current_score = score

        # Track best result
        if score > best_score:
            best_score = score
            best_json = render_json
            print(f"   🏆 New Best Score: {best_score}%")

        if success or force_stop:
            if force_stop:
                print(f"\n🛑 PROCESS ENDED MANUALLY. Restoring Best Result ({best_score}%)...")
                render_json = best_json
            else:
                print(f"\n✨ PRODUCTION READY! Final Rating: {score}%")
            break
        else:
            print(f"\n⚠️ QA FAILED ({score}%). Re-prompting for correction...")
            previous_json = json.dumps(render_json, indent=2, ensure_ascii=False)
            feedback_errors = feedback
            iteration += 1

    # Ensure final best result is saved
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(render_json, f, indent=2, ensure_ascii=False)
    print(f"✅ Final Manifest saved to: {args.output}")

if __name__ == "__main__": main()
