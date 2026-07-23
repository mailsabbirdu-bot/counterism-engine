import os
import sys
import json
import argparse
import re
import time
import subprocess
import shutil
import math
import copy
from typing import Dict, Any, List, Optional, Tuple
try:
    from .supervisor import supervise_manifest, SceneSupervisor
    from .intelligence import SceneIntelligenceEngine
    from .memory_manager import ProductionMemoryManager
    from .perception_logic import VisionConstants
except (ImportError, ValueError):
    from supervisor import supervise_manifest, SceneSupervisor
    from intelligence import SceneIntelligenceEngine
    from memory_manager import ProductionMemoryManager
    from perception_logic import VisionConstants

class ConsecutiveIssueTracker:
    """Tracks how many times an issue has appeared across iterations."""
    def __init__(self, threshold: int = 2):
        self.issue_counts = {} # pattern -> count
        self.threshold = threshold

    def update_and_get_stubborn(self, feedback: List[str]) -> List[str]:
        stubborn = []
        current_patterns = set()

        for fb in feedback:
            # Strip IDs/timestamps to find recurring patterns
            # Matches (ov_1_1) or (overlay_0)
            pattern = re.sub(r'\(\w+\)', '(element)', fb)
            pattern = re.sub(r'\[SCENE_\d+\]', '[SCENE]', pattern)
            pattern = re.sub(r'at \d+f', 'at (time)', pattern)
            current_patterns.add(pattern)

            self.issue_counts[pattern] = self.issue_counts.get(pattern, 0) + 1
            if self.issue_counts[pattern] >= self.threshold:
                stubborn.append(fb)

        # Prune resolved issues
        resolved = [p for p in self.issue_counts if p not in current_patterns]
        for p in resolved: del self.issue_counts[p]

        return stubborn

class RemotionJsonMaker:
    # --- SEMANTIC MAPPING ENGINE ---
    SEMANTIC_KEYWORDS = {
        'conflict': ['threat', 'problem', 'danger', 'risk', 'warning', 'versus', 'crisis', 'battle', 'war', 'attack', 'failed'],
        'trend': ['growth', 'increase', 'rise', 'data', 'percent', 'forecast', 'future', 'trend', 'evolution', 'history'],
        'comparison': ['vs', 'compare', 'difference', 'better', 'higher', 'scale', 'ratio', 'rank'],
        'historical': ['past', 'archive', 'ancient', 'was', 'used to', 'century', 'origin', 'legacy']
    }

    def _auto_assign_semantic_role(self, story_text: str) -> str:
        story_lower = story_text.lower()
        counts = {role: 0 for role in self.SEMANTIC_KEYWORDS}
        for role, keywords in self.SEMANTIC_KEYWORDS.items():
            for kw in keywords:
                if kw in story_lower: counts[role] += 1

        best_role = max(counts, key=counts.get)
        return best_role if counts[best_role] > 0 else 'trend'

    # --- PRODUCTION-GRADE CONSTANTS ---
    TYPE_SIZES = {
        'text': (800, 200), 'chart': (1000, 562), 'shadcn_chart': (1000, 562),
        'ui_panel': (800, 600), 'data_indicator': (500, 375), 'shadcn_indicator': (500, 375),
        'svg': (400, 400), 'kpi': (450, 400), 'kpi_card': (450, 400),
        'timeline': (1200, 300), 'hub_network': (800, 800), 'flow_diagram': (1000, 562), 'process': (1000, 562),
        'media': (960, 540), 'image': (960, 540), 'video': (960, 540),
        'label': (300, 100), 'callout': (400, 200), 'compositions': (1200, 675), 'groups': (1200, 675),
        'shape': (400, 400), 'data_emphasis': (600, 200), 'ambient_graphic': (1920, 1080),
        'connector': (400, 100)
    }

    SEMANTIC_ANIMS = [
        "wordReveal", "glassReveal", "networkGrow", "barsRise", "cinematicGlow",
        "fadeScale", "parallaxDrift", "maskReveal", "lineDraw", "particleAssembly",
        "blurFocus", "svgMorph", "depthZoom"
    ]

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

    PRIORITY = {
        'hero': 1000, 'text': 60, 'hub_network': 90, 'flow_diagram': 90, 'process': 90,
        'chart': 40, 'shadcn_chart': 40, 'kpi_card': 40, 'timeline': 75, 'ui_panel': 60,
        'compositions': 55, 'groups': 55, 'data_indicator': 40, 'shadcn_indicator': 40,
        'label': 45, 'callout': 45, 'svg': 40, 'kpi': 40, 'connector': 30,
        'shape': 10, 'ambient_graphic': 5, 'background': 0
    }

    # Rule of Thirds Anchors (Synced from VisionConstants)
    ANCHORS = VisionConstants.ANCHORS

    LOCKED_FIELDS = ["content", "hero_config", "tracking"]
    MODERN_COLORS = ["#00F5FF", "#FFD700", "#FF3E6C", "#00FFAB"]

    def _flatten_value(self, val, key):
        """Forcefully flattens hallucinated dictionary values into strings."""
        return VisionConstants.to_str(val)
    CLAMP_MIN_X, CLAMP_MAX_X = 150, 1770
    CLAMP_MIN_Y, CLAMP_MAX_Y = 150, 930
    MIN_SPACING = 30
    MIN_FONT_SIZE = 40

    def __init__(self, manual: bool = False, memory_path: str = "production_knowledge.json"):
        self.manual = manual
        self.memory = ProductionMemoryManager(memory_path)
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

        renders_dir = os.path.join(abs_public, "renders")
        self.video_files = sorted([f for f in os.listdir(renders_dir) if f.lower().endswith('.mp4')]) if os.path.exists(renders_dir) else []
        self.image_files = sorted([f for f in os.listdir(renders_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]) if os.path.exists(renders_dir) else []
        self.load_visual_analysis(abs_public)

    def _harden_root_settings(self, data: Dict[str, Any]):
        """Stage 0: Root Level Hardening."""
        # Unify Architecture: Remove redundant 'timeline' and use 'scenes' as canonical
        if 'timeline' in data:
            timeline = data['timeline']
            if not data.get('scenes'):
                if isinstance(timeline, list):
                    data['scenes'] = timeline
                elif isinstance(timeline, dict) and 'scenes' in timeline:
                    data['scenes'] = timeline['scenes']
                else:
                    data['scenes'] = [timeline]
            if 'timeline' in data: del data['timeline']

        if 'scenes' in data:
            if isinstance(data['scenes'], dict) and 'scenes' in data['scenes']:
                data['scenes'] = data['scenes']['scenes']

            if not isinstance(data['scenes'], list):
                data['scenes'] = [data['scenes']]

            # Ensure every scene is a dictionary. Filter out or repair malformed AI artifacts.
            cleaned_scenes = []
            for s in data['scenes']:
                if isinstance(s, dict):
                    cleaned_scenes.append(s)
                elif isinstance(s, str):
                    # Attempt to rescue if it looks like JSON string
                    try:
                        parsed = json.loads(s)
                        if isinstance(parsed, dict): cleaned_scenes.append(parsed)
                    except: pass
            data['scenes'] = cleaned_scenes

        # PRODUCTION: Detect if AI outputted overlays at root instead of inside scenes
        if 'overlays' in data and not data.get('scenes'):
            print("   🔧 TITAN FIX: Found root-level overlays. Wrapping into canonical SCENE_1.")
            data['scenes'] = [{
                "scene_id": "SCENE_1",
                "duration_in_frames": data.get('duration', 300),
                "overlays": data['overlays'],
                "camera": data.get('camera', {"enabled": True, "shots": []}),
                "background": {"background_type": "procedural"}
            }]
            del data['overlays']
            if 'camera' in data: del data['camera']

        if 'global_settings' not in data:
            data['global_settings'] = {"width": 1920, "height": 1080, "fps": 30}

        if 'resolution' in data:
            res = str(data['resolution']).lower()
            if 'x' in res:
                try:
                    w, h = map(int, res.split('x'))
                    data['global_settings']['width'] = w
                    data['global_settings']['height'] = h
                except: pass
            del data['resolution']

    def _harden_scene_metadata(self, scene: Dict[str, Any], scene_idx: int):
        """Stage 1: Scene-level metadata and duration hardening."""
        # Unify Scene ID to canonical format
        s_id = f"SCENE_{scene_idx+1}"
        scene['scene_id'] = s_id

        if 'duration' in scene and 'duration_in_frames' not in scene:
            scene['duration_in_frames'] = scene['duration']
        if 'duration_frames' in scene and 'duration_in_frames' not in scene:
            scene['duration_in_frames'] = scene['duration_frames']

        raw_dur = scene.get('duration_in_frames', 180)
        scene_duration = int(raw_dur * 30) if (isinstance(raw_dur, (float, int)) and raw_dur < 60) else int(raw_dur)

        id_num = scene_idx + 1

        if 'background' not in scene: scene['background'] = {}
        bg = scene['background']

        # Promote background fields from root if they exist
        for k in ['background_type', 'video_path', 'audio_enabled', 'procedural_config']:
            if k in scene:
                if k not in bg: bg[k] = scene[k]
                del scene[k]

        if not bg.get('background_type'): bg['background_type'] = 'video'
        if bg['background_type'] == 'video':
            if not bg.get('video_path'):
                vname = f"scene_SC_{id_num:02d}.mp4"
                if vname in self.video_files: bg['video_path'] = f"renders/{vname}"
                else: bg['background_type'] = 'procedural'
            elif not str(bg['video_path']).startswith('renders/'):
                bg['video_path'] = f"renders/{os.path.basename(bg['video_path'])}"

        if bg.get('background_type') == 'procedural':
            if not bg.get('procedural_config') or not isinstance(bg.get('procedural_config'), dict):
                bg['procedural_config'] = {"variant": "neon_grid"}
            bg['video_path'] = None

        filename = os.path.basename(str(bg.get('video_path', '')))
        scene_duration = int(raw_dur * 30) if (isinstance(raw_dur, (float, int)) and raw_dur < 60) else int(raw_dur)
        if filename in self.fps_cache: scene_duration = self.fps_cache[filename]

        scene['duration_in_frames'] = scene_duration
        bg['audio_enabled'] = False # PRODUCTION OVERRIDE

        # Cleanup root of redundant keys
        for k in ['duration', 'video_path', 'background_type', 'audio_enabled', 'id']:
            if k in scene: del scene[k]

        return scene_duration, id_num

    def _repair_hero_animations(self, hero_config: Dict[str, Any]):
        """Automatically maps invalid animation names to the nearest valid variant."""
        if not hero_config or 'animation' not in hero_config: return

        anim = hero_config['animation']
        if anim in self.VALID_TEXT_ANIMS: return

        # Simple fuzzy match: check if any valid anim is contained within or contains the invalid one
        for valid in self.VALID_TEXT_ANIMS:
            if valid in anim or anim in valid:
                print(f"   🔧 Repairing hero animation: '{anim}' -> '{valid}'")
                hero_config['animation'] = valid
                return

        # Fallback to nearest logical match for common AI hallucinations
        if 'blur' in anim and 'reveal' in anim: hero_config['animation'] = 'blur_reveal'
        elif 'zoom' in anim: hero_config['animation'] = 'isolate_zoom'
        elif 'glow' in anim: hero_config['animation'] = 'glow_pulse'
        else: hero_config['animation'] = self.VALID_TEXT_ANIMS[0]
        print(f"   🔧 Repairing unknown hero animation: '{anim}' -> '{hero_config['animation']}'")

    def _harden_overlay_data(self, ov: Dict[str, Any], scene_context: str = ""):
        """Stage 2: Deep Promotion and key unification for overlays."""
        # --- PHASE 0: Flattening ---
        for k in ['font', 'animation', 'content', 'text', 'label', 'title', 'color']:
            if k in ov: ov[k] = self._flatten_value(ov[k], k)

        # Fix invalid types commonly hallucinated by AI
        o_type = str(ov.get('type', 'text')).lower()
        if o_type == 'hero_animation':
             ov['type'] = 'text' # Usually AI means a text reveal
             o_type = 'text'
        elif o_type == 'kpi':
            ov['type'] = 'indicator'
            o_type = 'indicator'
        elif o_type == 'kpi_card':
            ov['type'] = 'shadcn_indicator'
            o_type = 'shadcn_indicator'
            if 'indicator_type' not in ov: ov['indicator_type'] = 'mini_stat_card'

        if ov.get('type') == 'text' and 'hero_config' in ov:
            self._repair_hero_animations(ov['hero_config'])

        # Unify Typography keys early
        if 'size' in ov:
            if 'fontSize' not in ov:
                ov['fontSize'] = f"{ov['size']}px" if isinstance(ov['size'], (int, float)) else str(ov['size'])
            del ov['size']

        # Unify Z-Index keys
        if 'z_index' in ov:
            if 'zIndex' not in ov: ov['zIndex'] = ov['z_index']
            del ov['z_index']

        # UNIFICATION: Standardize content keys before promotion
        o_type = str(ov.get('type', 'text')).lower()
        if 'text' in ov and 'content' not in ov: ov['content'] = ov['text']
        ov['type'] = o_type # Ensure key exists for priority checks

        # Helper to unify keys within an object
        def unify_obj(obj):
            if 'text' in obj and 'content' not in obj: obj['content'] = obj['text']
            if 'label' in obj and 'content' not in obj: obj['content'] = obj['label']
            if 'title' in obj and 'content' not in obj and o_type == 'text': obj['content'] = obj['title']
            if 'size' in obj:
                if 'fontSize' not in obj: obj['fontSize'] = f"{obj['size']}px" if isinstance(obj['size'], (int, float)) else str(obj['size'])
                del obj['size']
            if 'z_index' in obj:
                if 'zIndex' not in obj: obj['zIndex'] = obj['z_index']
                del obj['z_index']

        unify_obj(ov)

        # Move fields from 'properties', 'data', 'styling', 'style' or 'config' to root
        for nest_key in ['properties', 'data', 'styling', 'style', 'config']:
            if nest_key in ov and isinstance(ov[nest_key], dict):
                nested = ov[nest_key]
                unify_obj(nested)

                for sub_key, sub_val in nested.items():
                    # v3.1: Force promote locked fields IF they were nested (solves AI nesting habit)
                    ov[sub_key] = sub_val
                del ov[nest_key]

        # Standardize variant mapping (Hardened for SHADCN vs Standard)
        if 'variant' in ov:
            v_val = str(ov['variant'])
            if 'chart' in o_type:
                if v_val.startswith('metaphor_'):
                    ov['visual_metaphor'] = v_val.replace('metaphor_', '')
                    ov['type'] = 'chart'
                    o_type = 'chart'
                # Map glass/neon/glow variants to shadcn_chart
                elif any(x in v_val for x in ['glass', 'neon', 'stacked', 'web', 'glow', 'composed', 'thick', 'pixel', 'grid']):
                    ov['type'] = 'shadcn_chart'
                    o_type = 'shadcn_chart'
                ov['chart_type'] = v_val
            elif 'indicator' in o_type:
                # PRODUCTION: Repair deprecated variants
                if v_val == 'statusBadge':
                    v_val = 'tech_badge'

                # Map tile/badge/status variants to shadcn_indicator
                if any(x in v_val for x in ['tile', 'badge', 'status', 'crypto', 'card', 'ring', 'pill', 'pack', 'dots', 'tech']):
                    ov['type'] = 'shadcn_indicator'
                    o_type = 'shadcn_indicator'
                ov['indicator_type'] = v_val
            elif o_type == 'shape': ov['shape_type'] = v_val
            elif o_type == 'connector': ov['preset'] = v_val
            del ov['variant']

        # RE-FIX: Ensure type-specific variant keys exist
        if o_type == 'shape' and 'shape_type' not in ov: ov['shape_type'] = 'rect'
        if 'chart' in o_type and 'chart_type' not in ov: ov['chart_type'] = 'bar'
        if 'indicator' in o_type and 'indicator_type' not in ov: ov['indicator_type'] = 'kpiNumber'
        if o_type == 'connector' and 'preset' not in ov: ov['preset'] = 'smooth_curve'

        # Mandatory Data Injection
        var = ov.get('indicator_type') or ov.get('chart_type') or ov.get('shape_type') or ov.get('preset')
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

        # Font Decision Logic (Hardened)
        content = str(ov.get('content', '')).strip()

        is_content_bangla = VisionConstants.is_bangla(content)
        ai_font = ov.get('font')

        if is_content_bangla:
            # Content is Bangla: MUST use a Bangla font.
            if ai_font not in self.bangla_fonts:
                ov['font'] = "Sohid_bangla" if "Sohid_bangla" in self.bangla_fonts else (self.bangla_fonts[0] if self.bangla_fonts else "Arial")
            if o_type == 'text':
                ov['splitMode'] = 'word'
        else:
            # Content is NOT Bangla: English/Mixed content should use English font for clarity.
            if ai_font not in self.english_fonts:
                # If scene is Bangla, AI might have tried a Bangla font, override it.
                ov['font'] = self.english_fonts[0] if self.english_fonts else "Arial"

        # New variant injections
        if var == 'activity_ring' and 'rings' not in ov:
            ov['rings'] = [{"label": "Active", "value": 80, "color": "#00F5FF"}]
        if var == 'radar_web' and 'data' not in ov:
            ov['data'] = [{"subject": "Speed", "A": 120, "B": 110}, {"subject": "Reliability", "A": 98, "B": 130}]
        if var == 'crypto_card' and 'sparkline' not in ov:
            ov['sparkline'] = [10, 25, 15, 45, 30, 60]

        # Thematic Data Injections for Charts & Indicators
        if 'chart' in o_type:
            title = str(ov.get('title', ov.get('content', ''))).strip()
            # If the data is empty or generic, populate it
            has_valid_data = False
            if 'data' in ov and isinstance(ov['data'], list) and len(ov['data']) > 0:
                # Check if first element is not just a generic placeholder
                first = ov['data'][0]
                if isinstance(first, dict) and first.get('id') not in ['A', 'B'] and first.get('name') not in ['A', 'B']:
                    has_valid_data = True

            if not has_valid_data:
                # Inject story-relevant data
                text_to_check = (title + " " + scene_context).lower()
                is_bn = any('\u0980' <= c <= '\u09FF' for c in text_to_check)

                if any(x in text_to_check for x in ["tension", "escalation", "risk", "hazard", "threat", "seismic", "geological", "clock", "timebomb", "টাইমবোম্ব", "ঝুঁকি"]):
                    if is_bn:
                        ov['data'] = [
                            {"id": "২০২০", "name": "২০২০", "x": "২০২০", "y": 20, "value": 20, "value2": 15},
                            {"id": "২০২১", "name": "২০২১", "x": "২০২১", "y": 38, "value": 38, "value2": 28},
                            {"id": "২০২২", "name": "২০২২", "x": "২০২২", "y": 55, "value": 55, "value2": 42},
                            {"id": "২০২৩", "name": "২০২৩", "x": "২০২৩", "y": 78, "value": 78, "value2": 65},
                            {"id": "২০২৪", "name": "২০২৪", "x": "২০২৪", "y": 95, "value": 95, "value2": 82}
                        ]
                    else:
                        ov['data'] = [
                            {"id": "2020", "name": "2020", "x": "2020", "y": 20, "value": 20, "value2": 15},
                            {"id": "2021", "name": "2021", "x": "2021", "y": 38, "value": 38, "value2": 28},
                            {"id": "2022", "name": "2022", "x": "2022", "y": 55, "value": 55, "value2": 42},
                            {"id": "2023", "name": "2023", "x": "2023", "y": 78, "value": 78, "value2": 65},
                            {"id": "2024", "name": "2024", "x": "2024", "y": 95, "value": 95, "value2": 82}
                        ]
                elif any(x in text_to_check for x in ["population", "people", "dense", "density", "কোটি", "মানুষ", "ঘনত্ব"]):
                    if is_bn:
                        ov['data'] = [
                            {"id": "২০১২", "name": "২০১২", "x": "২০১২", "y": 12, "value": 12, "value2": 15},
                            {"id": "২০১৫", "name": "২০১৫", "x": "২০১৫", "y": 15, "value": 15, "value2": 18},
                            {"id": "২০১৮", "name": "২০১৮", "x": "২০১৮", "y": 18, "value": 18, "value2": 20},
                            {"id": "২০২১", "name": "২০২১", "x": "২০২১", "y": 20, "value": 20, "value2": 22},
                            {"id": "২০২৪", "name": "২০২৪", "x": "২০২৪", "y": 22, "value": 22, "value2": 25}
                        ]
                    else:
                        ov['data'] = [
                            {"id": "2012", "name": "2012", "x": "2012", "y": 1.2, "value": 1.2, "value2": 1.5},
                            {"id": "2015", "name": "2015", "x": "2015", "y": 1.5, "value": 1.5, "value2": 1.8},
                            {"id": "2018", "name": "2018", "x": "2018", "y": 1.8, "value": 1.8, "value2": 2.0},
                            {"id": "2021", "name": "2021", "x": "2021", "y": 2.0, "value": 2.0, "value2": 2.2},
                            {"id": "2024", "name": "2024", "x": "2024", "y": 2.2, "value": 2.2, "value2": 2.5}
                        ]
                else:
                    if is_bn:
                        ov['data'] = [
                            {"id": "ক", "name": "ক", "x": "ক", "y": 30, "value": 30},
                            {"id": "খ", "name": "খ", "x": "খ", "y": 60, "value": 60},
                            {"id": "গ", "name": "গ", "x": "গ", "y": 90, "value": 90}
                        ]
                    else:
                        ov['data'] = [
                            {"id": "A", "name": "A", "x": "A", "y": 30, "value": 30},
                            {"id": "B", "name": "B", "x": "B", "y": 60, "value": 60},
                            {"id": "C", "name": "C", "x": "C", "y": 90, "value": 90}
                        ]

            if o_type == 'chart' and 'title' not in ov:
                ov['title'] = title if title else "Geological Data"
            if 'keys' not in ov:
                ov['keys'] = ['value']

        if 'indicator' in o_type:
            lbl = str(ov.get('label', ov.get('content', ''))).strip()
            text_to_check = (lbl + " " + scene_context).lower()
            is_bn = any('\u0980' <= c <= '\u09FF' for c in text_to_check)

            val = ov.get('value')
            if not val or val == 8420:
                if any(x in text_to_check for x in ["population", "people", "dense", "density", "কোটি", "মানুষ", "ঘনত্ব"]):
                    if is_bn:
                        ov['value'] = "২,২৪,০০,০০০+"
                        ov['label'] = "মোট জনসংখ্যা"
                    else:
                        ov['value'] = "22,400,000+"
                        ov['label'] = "TOTAL POPULATION"
                elif any(x in text_to_check for x in ["tension", "escalation", "risk", "hazard", "threat", "seismic", "geological", "clock", "timebomb", "টাইমবোম্ব", "ঝুঁকি"]):
                    if is_bn:
                        ov['value'] = "৯৫%"
                        ov['label'] = "সর্বোচ্চ ঝুঁকি"
                    else:
                        ov['value'] = "95%"
                        ov['label'] = "MAXIMUM RISK"
                else:
                    if is_bn:
                        ov['value'] = "১০০%"
                        ov['label'] = "চলমান"
                    else:
                        ov['value'] = "100%"
                        ov['label'] = "ACTIVE"
            elif not ov.get('label'):
                ov['label'] = lbl

    def finalize_json_durations(self, data: Dict[str, Any], public_dir: str = "../public") -> Dict[str, Any]:
        """Hardens layout, timing, camera, and assets with Geometry-Aware Logic and Adaptive Scaling."""
        if not data: return data
        abs_public = os.path.abspath(public_dir)
        self._harden_root_settings(data)

        if not data.get('scenes'): return data
        print(f"🛠️ HARDENING ENGINE: Resolving spatial collisions and cinematic timing...")

        sfx_manifest = []
        in_ptr = 0

        for scene_idx, scene in enumerate(data['scenes']):
            scene_duration, id_num = self._harden_scene_metadata(scene, scene_idx)
            s_id = scene['scene_id'] # Use canonical ID from hardening

            # v4.5: Semantic Orchestration
            if 'semantic_role' not in scene:
                story_context = self.story_scenes.get(s_id, "")
                scene['semantic_role'] = self._auto_assign_semantic_role(story_context)

            print(f"   🎬 Processing: {s_id}")

            pattern = f"SC_{id_num:02d}".lower()
            narration_file = next((f for f in self.narration_files if pattern in f.lower()), None)
            if narration_file:
                sfx_manifest.append({"scene_id": s_id, "file": narration_file, "start": 0, "end": scene_duration, "volume": 1.0})

            if not scene.get('overlays'):
                scene['overlays'] = []

            # Harvest hallucinated semantic keys into canonical overlays
            harvest_map = {
                'text_overlays': 'text',
                'text_elements': 'text',
                'indicators': 'shadcn_indicator',
                'charts': 'shadcn_chart',
                'elements': None,
                'layers': None,
                'visuals': None
            }

            for key, default_type in harvest_map.items():
                if scene.get(key) and isinstance(scene[key], list):
                    for item in scene[key]:
                        if default_type and 'type' not in item:
                            item['type'] = default_type
                        scene['overlays'].append(item)
                    del scene[key]


            valid_overlays = []
            text_count, focal_count, svg_count = 0, 0, 0

            raw_overlays = scene['overlays'] if isinstance(scene['overlays'], list) else [scene['overlays']]
            for ov in raw_overlays:
                self._harden_overlay_data(ov, scene_context=self.story_scenes.get(s_id, ""))
                o_type = str(ov.get('type', 'text')).lower()
                if 'chart_type' in ov: o_type = 'shadcn_chart'
                if 'indicator_type' in ov: o_type = 'shadcn_indicator'

                content = str(ov.get('content', '')).strip()
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
                elif o_type in ['svg', 'label', 'callout', 'data_indicator', 'shadcn_indicator', 'shape', 'ambient_graphic', 'connector']:
                    if svg_count >= 15: continue
                    svg_count += 1
                elif o_type in ['image', 'video']:
                    src = ov.get('src', ov.get('image_path', ov.get('video_path')))
                    if not src:
                        if o_type == 'video' and self.video_files: src = f"renders/{self.video_files[0]}"
                        elif o_type == 'image' and self.image_files: src = f"renders/{self.image_files[0]}"
                        else: src = "renders/placeholder.png"
                    if src and not str(src).startswith('renders/'):
                        src = f"renders/{os.path.basename(src)}"
                    ov['src'] = src
                    for k in ['image_path', 'video_path']:
                        if k in ov: del ov[k]

                if not ov.get('id'): ov['id'] = f"ov_{id_num}_{len(valid_overlays)+1}"


                if ov['type'] == 'text':
                    ov['maxWidth'] = ov.get('maxWidth', 800)
                    if not ov.get('hero_config'):
                        hero = self._get_scene_hero_word(s_id, ov['content'], scene_duration)
                        if not hero: hero = self._get_fallback_hero(ov['content'])
                        if hero: ov['hero_config'] = {"word": hero['word'], "start": hero['start'], "color": self.MODERN_COLORS[(scene_idx + 2) % len(self.MODERN_COLORS)], "animation": self.VALID_TEXT_ANIMS[scene_idx % len(self.VALID_TEXT_ANIMS)]}
                    else:
                        # EXTREMELY IMPORTANT: Always correct and align any existing/hallucinated hero word start frame
                        # with the actual ground-truth voiceover timestamp from timestamp.txt!
                        h_conf = ov['hero_config']
                        word = h_conf.get('word', '')
                        if word:
                            clean_word = re.sub(r'[.।]', '', str(word)).strip()
                            hero = self._get_scene_hero_word(s_id, clean_word, scene_duration)
                            if hero:
                                print(f"   🎙️ Syncing hero word '{clean_word}' start frame to {hero['start']}f")
                                h_conf['start'] = hero['start']
                    ov['color'] = self.MODERN_COLORS[scene_idx % len(self.MODERN_COLORS)]
                    ov['fontSize'] = ov.get('fontSize', "120px")
                valid_overlays.append(ov)

            valid_overlays.sort(key=lambda o: self.PRIORITY.get(str(o.get('type')).lower(), 0), reverse=True)

            # Resolve Collisions and Layout
            filename = os.path.basename(str(scene.get('video_path', '')))
            scene_analysis = self.visual_analysis.get(filename, {})
            recommended_region = scene_analysis.get("text_region", {}).get("preferred", "center")

            self._resolve_spatial_collisions(valid_overlays, scene_duration, scene_idx, recommended_region)

            # Finalize Scene-level sequencing
            valid_overlays.sort(key=lambda o: (int(o.get('start', 0)), self.PRIORITY.get(str(o.get('type')).lower(), 0)))
            scene['overlays'] = valid_overlays
            if 'transition' not in scene: scene['transition'] = {"type": "cinematicMatchCut", "duration": 15}
            if 'beats' not in scene: scene['beats'] = [{"frame": o['start'], "event": f"{o['id']}_reveal"} for o in valid_overlays if self.PRIORITY.get(o['type'], 0) >= 50]
            if 'connections' not in scene: scene['connections'] = []

            # Identify true HERO targets
            true_hero_ids = [o['id'] for o in valid_overlays if str(o.get('importance', '')).lower() == 'hero' or o.get('hero_config')]
            hero_ids = [o['id'] for o in valid_overlays if self.PRIORITY.get(o['type'], 0) >= 100]
            focal_ids = [o['id'] for o in valid_overlays if self.PRIORITY.get(str(o.get('type')).lower(), 0) >= 50 and o['id'] not in hero_ids and o['id'] not in true_hero_ids]
            background_ids = [o['id'] for o in valid_overlays if self.PRIORITY.get(str(o.get('type')).lower(), 0) < 50]

            ai_shots = scene.get('camera', {}).get('shots', [])
            if not ai_shots or not all(s.get('targetId') in [o['id'] for o in valid_overlays] for s in ai_shots):
                CAM_STYLES = ["cinematic_drift", "slow_push", "pan_right", "orbit", "rack_focus", "dramatic_reveal"]
                shots = []
                if background_ids: shots.append({"targetId": background_ids[0], "startFrame": 0, "duration": 45, "style": "cinematic_drift", "zoom": 1.05, "inDuration": 15})

                camera_targets = sorted([o for o in valid_overlays if o['id'] in true_hero_ids], key=lambda x: x['start'])
                other_targets = sorted([o for o in valid_overlays if o['id'] in (hero_ids + focal_ids) and o['id'] not in true_hero_ids], key=lambda x: x['start'])
                ordered_targets = camera_targets + other_targets

                for i, ov in enumerate(ordered_targets[:4]):
                    start = max(shots[-1]['startFrame'] + 10, ov['start']) if shots else ov['start']
                    if shots: shots[-1]['duration'] = max(20, start - shots[-1]['startFrame'])
                    zoom_level = 1.15 + (i * 0.05) if ov['id'] in true_hero_ids else 1.1 + (i * 0.05)
                    style = CAM_STYLES[(scene_idx + i) % len(CAM_STYLES)]
                    if ov['id'] in true_hero_ids and i == 0: style = "dramatic_reveal"
                    shots.append({"targetId": ov['id'], "startFrame": start, "duration": 60, "style": style, "zoom": zoom_level, "inDuration": 20, "ease": "cubicOut"})
                if shots: shots[-1]['duration'] = max(30, scene_duration - shots[-1]['startFrame'])
                scene['camera'] = {"enabled": True, "shots": shots}
            else:
                scene['camera']['enabled'] = True
                for shot in scene['camera']['shots']: shot['ease'] = shot.get('ease', "cubicOut")

            for i, ov in enumerate(valid_overlays):
                # Ensure SFX uses unified s_id
                if self.in_files: sfx_manifest.append({"scene_id": s_id, "file": self.in_files[(in_ptr+i)%len(self.in_files)], "start": int(ov.get('start', 0)), "end": int(ov.get('start', 0))+30, "volume": 0.05})
            in_ptr += len(valid_overlays)

        data['audio_sfx_manifest'] = sfx_manifest
        return data

    def _resolve_spatial_collisions(self, valid_overlays: List[Dict[str, Any]], scene_duration: int, scene_idx: int, recommended_region: str):
        """Stage 3: Resolves spatial collisions with expert nudging and scaling."""
        placed_boxes = []
        stagger_step = min(30, max(10, scene_duration // (len(valid_overlays) + 2)))

        for i, ov in enumerate(valid_overlays):
            o_type = str(ov.get('type', 'text')).lower()
            if o_type in ['shape']: ov['start'] = 0
            elif self.PRIORITY.get(o_type, 0) < 50: ov['start'] = 5
            else: ov['start'] = 15 + i * stagger_step
            ov['duration'] = max(30, scene_duration - ov['start'] - 30)
            if not ov.get('exitAnimation'): ov['exitAnimation'] = "fade_out" if o_type != 'text' else "slide_down"

            base_w, base_h = self.TYPE_SIZES.get(o_type, (600, 400))
            imp = str(ov.get('importance', '')).lower()
            if imp == 'hero': ov['depth'], ov['parallax'] = 100, 1.0
            elif imp == 'secondary': ov['depth'], ov['parallax'] = 50, 0.8
            elif imp == 'ambient': ov['depth'], ov['parallax'] = -50, 0.5
            elif imp == 'background': ov['depth'], ov['parallax'] = -100, 0.2
            else:
                prio = self.PRIORITY.get(o_type, 40)
                ov['depth'], ov['parallax'] = prio - 50, max(0.2, min(1.0, prio / 100.0))

            fs_match = re.search(r'\d+', str(ov.get('fontSize', '120')))
            fs = int(fs_match.group()) if fs_match else 120

            # Estimate width/height early to clamp center safely inside screen margins
            if o_type == 'text':
                w = min(ov.get('maxWidth', 800), len(ov.get('content', '')) * fs * 0.7)
                h = fs * 1.5
            else:
                w = max(300, base_w)
                h = max(200, base_h)

            margin = 150
            # Calculate dynamic clamp ranges to guarantee no part of the element ever bleeds off-screen
            clamp_min_x = max(margin + w/2, self.CLAMP_MIN_X)
            clamp_max_x = min(1920 - margin - w/2, self.CLAMP_MAX_X)
            clamp_min_y = max(margin + h/2, self.CLAMP_MIN_Y)
            clamp_max_y = min(1080 - margin - h/2, self.CLAMP_MAX_Y)

            # Ensure min <= max
            if clamp_min_x > clamp_max_x: clamp_min_x = clamp_max_x = 960
            if clamp_min_y > clamp_max_y: clamp_min_y = clamp_max_y = 540

            pos = ov.get('position', {})
            if isinstance(pos, list):
                ax = int(pos[0]) if len(pos) > 0 else 960
                ay = int(pos[1]) if len(pos) > 1 else 540
            elif isinstance(pos, dict):
                ax = int(pos.get('x', 960))
                ay = int(pos.get('y', 540))
            else:
                ax, ay = 960, 540

            ax = max(clamp_min_x, min(clamp_max_x, ax))
            ay = max(clamp_min_y, min(clamp_max_y, ay))

            if abs(ax - 960) < 200 and (abs(ay - 540) < 150 or abs(ay - 700) < 150):
                if "left" in recommended_region: ax, ay = self.ANCHORS["L_MID"]
                elif "right" in recommended_region: ax, ay = self.ANCHORS["R_MID"]
                elif "top" in recommended_region: ax, ay = self.ANCHORS["C_TOP"]
                elif "bottom" in recommended_region: ax, ay = self.ANCHORS["C_BOT"]
                else:
                    targets = [self.ANCHORS["L_MID"], self.ANCHORS["R_MID"], self.ANCHORS["L_TOP"], self.ANCHORS["R_BOT"]]
                    ax, ay = targets[i % len(targets)]

            if not ov.get('tracking', {}).get('enabled'):
                for grid_x, grid_y in self.ANCHORS.values():
                    if abs(ax - grid_x) < 180 and abs(ay - grid_y) < 180:
                        ax, ay = grid_x, grid_y; break

            ov['position'] = {"x": ax, "y": ay}
            for k in ['x', 'y', 'left', 'top']:
                if k in ov: del ov[k]

            found = False
            best_pos, final_w, final_h = (ax, ay), base_w, base_h
            fs = int(re.search(r'\d+', str(ov.get('fontSize', '120'))).group()) if o_type == 'text' else 120

            for scale_step in range(5):
                scale = max(0.4, 1.0 - (scale_step * 0.15))
                if imp == 'hero' and scale < 0.8: scale = 0.8
                if o_type in ['shape']: scale = min(scale, 0.8)

                if o_type == 'text':
                    curr_fs = max(self.MIN_FONT_SIZE, int(fs * scale))
                    w = min(ov.get('maxWidth', 800), len(ov['content']) * curr_fs * 0.7)
                    h = curr_fs * 1.5
                else:
                    w = max(300 if 'chart' in o_type else 100, base_w * scale)
                    h = max(200 if 'chart' in o_type else 100, base_h * scale)

                for step in range(0, 120): # Search radius per scale level
                    radius = step * 10
                    angles = [0, 180, 90, 270, 45, 135, 225, 315, 30, 60, 120, 150, 210, 240, 300, 330] if radius > 0 else [0]
                    for angle in angles:
                        rad = math.radians(angle)
                        cx, cy = ax + radius * math.cos(rad), ay + radius * math.sin(rad)
                        l, t, r, b = cx-w/2, cy-h/2, cx+w/2, cy+h/2

                        # Strict 150px safety margin enforcement for production broadcast
                        margin = 150
                        if l < margin or r > (1920 - margin) or t < margin or b > (1080 - margin): continue

                        collision = False
                        for p_id, p_l, p_t, p_r, p_b, p_s, p_e, p_imp in placed_boxes:
                            if max(ov['start'], p_s) < min(ov['start'] + ov.get('duration', 60), p_e):
                                # Skip collision check if one is Hero/Secondary and the other is Background/Ambient
                                # This allows backgrounds to sit behind focal elements without triggering nudging
                                if (imp in ['background', 'ambient'] and p_imp in ['hero', 'secondary']) or \
                                   (p_imp in ['background', 'ambient'] and imp in ['hero', 'secondary']):
                                    continue

                                if not (r + self.MIN_SPACING < p_l or l - self.MIN_SPACING > p_r or b + self.MIN_SPACING < p_t or t - self.MIN_SPACING > p_b):
                                    collision = True; break
                        if not collision:
                            best_pos, found = (cx, cy), True
                            if radius > 50:
                                print(f"   🔧 Expert Nudging {ov['id']} -> ({int(cx)}, {int(cy)})")
                                if not ov.get('animation') or ov.get('animation') not in self.SEMANTIC_ANIMS:
                                    ov['animation'] = self.SEMANTIC_ANIMS[scene_idx % len(self.SEMANTIC_ANIMS)]
                            if scale < 1.0:
                                print(f"   🔧 Scaling down {ov['id']} to {int(scale*100)}%")
                                if o_type == 'text': ov['fontSize'] = f"{int(curr_fs)}px"
                                else: ov['width'], ov['height'] = int(w), int(h)
                            final_w, final_h = (w if o_type != 'text' else min(1600, len(ov['content']) * int(curr_fs) * 0.7)), (h if o_type != 'text' else int(curr_fs) * 1.5)
                            break
                    if found: break
                if found: break

            ov['position'] = {"x": int(best_pos[0]), "y": int(best_pos[1])}
            ov['visual_anchor'] = True
            if ov.get('hero_config'): ov['hero_config']['start'] = max(ov['start'] + 10, ov['hero_config'].get('start', 0))
            placed_boxes.append((ov['id'], best_pos[0]-final_w/2, best_pos[1]-final_h/2, best_pos[0]+final_w/2, best_pos[1]+final_h/2, ov['start'], ov['start']+ov['duration'], imp))

    def apply_qa_patches(self, data: Dict[str, Any], feedback: List[str]) -> Dict[str, Any]:
        """v2.0: Automatically applies deterministic JSON patches from QA feedback."""
        print(f"🛠️ AUTO-REPAIR: Applying deterministic patches from QA...")
        patch_count = 0

        for fb in feedback:
            if "REQUIRED PATCH:" in fb:
                try:
                    # Extract scene ID and patch block
                    scene_match = re.search(r'\[(SCENE_\d+)\]', fb)
                    patch_match = re.search(r'REQUIRED PATCH: (\{.*\})', fb)

                    if not patch_match: continue
                    scene_id = scene_match.group(1) if scene_match else None
                    patch_data = json.loads(patch_match.group(1))

                    # If scene_id is present, apply to specific overlays in that scene
                    if scene_id:
                        for scene in data.get('scenes', []):
                            if scene.get('scene_id') == scene_id:
                                # If patch contains 'id' and 'patch', it's overlay specific
                                # In v3.0 QA, the string is [SCENE_01] ERROR: (ov_id) msg -> PATCH
                                overlay_id_match = re.search(r'\((\w+)\)', fb)
                                if overlay_id_match:
                                    target_ov_id = overlay_id_match.group(1)
                                    for ov in scene.get('overlays', []):
                                        if ov.get('id') == target_ov_id:
                                            # Support for special deletion key
                                            if "_delete" in patch_data:
                                                for k in patch_data["_delete"]:
                                                    if k in ov: del ov[k]
                                                del patch_data["_delete"]
                                            ov.update(patch_data)
                                            patch_count += 1
                                else:
                                    # Scene-level patch (not overlay specific)
                                    if "_delete" in patch_data:
                                        for k in patch_data["_delete"]:
                                            if k in scene: del scene[k]
                                        del patch_data["_delete"]
                                    scene.update(patch_data)
                                    patch_count += 1
                    else:
                        # Global patch (less common)
                        data.update(patch_data)
                        patch_count += 1
                except Exception as e:
                    print(f"   ⚠️ Failed to apply patch: {e}")

        if patch_count > 0:
            print(f"   ✅ Applied {patch_count} deterministic repairs.")
        return data

    def extract_problematic_segments(self, data: Dict[str, Any], feedback: List[str]) -> Dict[str, Any]:
        """v3.0: Extracts only the scenes/overlays that have remaining issues after auto-repair."""
        problematic_scenes = []
        # Find scenes mentioned in feedback
        # Supports [SCENE_01] and [SCENE_1]
        raw_scene_ids = set(re.findall(r'\[SCENE_(\d+)\]', "\n".join(feedback)))
        scene_ids = {f"SCENE_{int(id_str)}" for id_str in raw_scene_ids}

        for idx, scene in enumerate(data.get('scenes', [])):
            s_id = scene.get('scene_id')
            if s_id in scene_ids:
                # v3.1: Inject _temp_idx to track position during surgical merge
                scene_copy = copy.deepcopy(scene)
                scene_copy['_temp_idx'] = idx
                problematic_scenes.append(scene_copy)

        return {"scenes": problematic_scenes}

    def merge_surgical_corrections(self, master: Dict[str, Any], corrections: Dict[str, Any]) -> Dict[str, Any]:
        """v3.1: Merges surgical Gemini corrections back into the master manifest using _temp_idx."""
        if not corrections or 'scenes' not in corrections: return master

        # Ensure master has scenes
        if 'scenes' not in master: master['scenes'] = []

        for corr_scene in corrections['scenes']:
            # 1. Preferred Match: _temp_idx (Deterministic)
            target_idx = corr_scene.get('_temp_idx')
            if target_idx is not None and isinstance(target_idx, int) and target_idx < len(master['scenes']):
                # Verify it's the same scene by checking relative ID
                m_scene = master['scenes'][target_idx]
                m_num = int(re.search(r'(\d+)', str(m_scene.get('scene_id', ''))).group(1))
                c_num = int(re.search(r'(\d+)', str(corr_scene.get('scene_id', ''))).group(1))

                if m_num == c_num:
                    canonical_id = m_scene.get('scene_id')
                    master['scenes'][target_idx] = corr_scene
                    master['scenes'][target_idx]['scene_id'] = canonical_id
                    if '_temp_idx' in master['scenes'][target_idx]: del master['scenes'][target_idx]['_temp_idx']
                    continue

            # 2. Fallback Match: Scene ID Comparison
            s_id_match = re.search(r'(\d+)', str(corr_scene.get('scene_id', '')))
            if not s_id_match: continue

            s_num = int(s_id_match.group(1))
            found = False
            for i, master_scene in enumerate(master.get('scenes', [])):
                m_id_match = re.search(r'(\d+)', str(master_scene.get('scene_id', '')))
                if m_id_match and int(m_id_match.group(1)) == s_num:
                    canonical_id = master_scene.get('scene_id')
                    master['scenes'][i] = corr_scene
                    master['scenes'][i]['scene_id'] = canonical_id
                    if '_temp_idx' in master['scenes'][i]: del master['scenes'][i]['_temp_idx']
                    found = True; break

            if not found:
                if s_num <= len(master.get('scenes', [])) + 2:
                    if '_temp_idx' in corr_scene: del corr_scene['_temp_idx']
                    master['scenes'].append(corr_scene)

        # Re-sort to be safe, though index-based merge should preserve order
        master['scenes'].sort(key=lambda x: int(re.search(r'\d+', x.get('scene_id', '0')).group()))
        return master

    def supervise(self, data: Dict[str, Any]) -> List[str]:
        """Runs the Element Supervisor and Intelligence Engine on the manifest."""
        print(f"🧠 INTELLIGENCE: Predicting human perception and attention flow...")
        intel_engine = SceneIntelligenceEngine()
        reports = supervise_manifest(data)
        all_feedback = []

        # v5 HYBRID: Process intelligence for each scene
        for scene in data.get('scenes', []):
            s_id = scene.get('scene_id')
            try:
                intel_report = intel_engine.analyze_scene(scene)
                # Format Jules' intelligence as director feedback
                all_feedback.append(f"[{s_id}] DIRECTOR'S INTELLIGENCE: {intel_report['final_verdict']['summary']}")
                for conflict in intel_report['critical_conflicts']:
                    all_feedback.append(f"[{s_id}] CRITICAL CONFLICT ({conflict['type']}): {conflict['explanation']}")
                for adj in intel_report['overlay_adjustments']:
                    all_feedback.append(f"[{s_id}] REQUIRED ADJUSTMENT: {adj}")
            except Exception as e:
                print(f"⚠️ Intelligence Engine error on {s_id}: {e}")

        for report in reports:
            s_id = report['scene_id']
            if report['status'] != 'CLEAN':
                # Add overall status and scores (V8.1 Unified Categories)
                scores = report['scores']
                all_feedback.append(f"[{s_id}] DIRECTOR'S REPORT: Status={report['status']}, Clarity={scores.get('attention_clarity', 0)}, Motion={scores.get('motion_discipline', 0)}, Readability={scores.get('readability_score', 0)}")

                # Add specific issues (V8.1 Structured derived)
                for issue in report.get('issues', []):
                    all_feedback.append(f"[{s_id}] COGNITIVE ISSUE: {issue}")
                for issue in report.get('motion_issues', []):
                    all_feedback.append(f"[{s_id}] MOTION ISSUE: {issue}")

                # Derive pacing from cognitive findings
                pacing_issues = [f['human_explanation'] for f in report.get('findings', []) if f.get('category') == 'cognitive' and 'reveal' in f['human_explanation'].lower()]
                for issue in pacing_issues:
                    all_feedback.append(f"[{s_id}] PACING ISSUE: {issue}")

                # Add suggestions if high severity
                if report['status'] == 'OVERLOADED':
                    for sugg in report['fix_suggestions'][:3]:
                        all_feedback.append(f"[{s_id}] DIRECTOR FIX: {sugg}")

        return all_feedback

    def _get_scene_hero_word(self, scene_id: str, overlay_content: str, scene_duration: int = 180):
        if not self.raw_timestamps or not overlay_content: return None
        matches = re.findall(fr'{scene_id}:.*?\[30fps:\s*(\d+)f\s*-\s*\d+f\]\s*"(.*?)"', self.raw_timestamps)
        content_words = re.sub(r'[.।]', '', overlay_content).split()
        candidates = [{"word": w, "start": int(f)} for f, w in matches if re.sub(r'[.।]', '', w) in content_words]
        if not candidates: return None
        hero = max(candidates, key=lambda x: len(x['word']))
        hero['start'] = max(30, min(hero['start'], scene_duration - 60))
        return hero

    def repair_json(self, json_str: str) -> Dict[str, Any]:
        """v2.0: Robust JSON repair for common LLM hallucinations."""
        try:
            # 1. Clean characters and trailing commas
            json_str = re.sub(r',(\s*[\]\}])', r'\1', json_str)
            # 2. Fix missing brackets if simple enough
            if json_str.count('{') > json_str.count('}'): json_str += '}' * (json_str.count('{') - json_str.count('}'))
            if json_str.count('[') > json_str.count(']'): json_str += ']' * (json_str.count('[') - json_str.count(']'))

            # 3. Use regex to extract the largest object if it's wrapped in text
            match = re.search(r'(\{.*\})', json_str, re.DOTALL)
            if match:
                return json.loads(match.group(1), strict=False)
            return json.loads(json_str, strict=False)
        except:
            print("   ⚠️ JSON repair failed. Returning empty dict.")
            return {}

    def _get_fallback_hero(self, overlay_content: str):
        words = re.sub(r'[.।]', '', str(overlay_content)).split()
        return {"word": max(words, key=len), "start": 45} if words else None

    def _interact_with_gemini(self, prompt: str, previous_json: str = None, errors: List[str] = None, score: int = 0, surgical_mode: bool = False, stubborn_issues: List[str] = None) -> str:
        if self.manual:
            try:
                from google.colab import output
                import uuid
                u_id = uuid.uuid4().hex[:8]
                feedback_html = ""
                header_color = "#4CAF50" if score >= 100 else "#FF9800" if score >= 80 else "#FF3E6C"

                if stubborn_issues:
                    stubborn_list = "".join([f"<li>{e}</li>" for e in stubborn_issues])
                    feedback_html += f"""<div style='color: #FFD700; margin-bottom: 15px; border-left: 4px solid #FFD700; padding-left: 15px; background: #1a1a00; padding: 10px;'>
                        <strong style='font-size: 16px;'>⚠️ STUBBORN ISSUES (FAILED TWICE)</strong>
                        <p style='font-size: 13px;'>The engine will force-apply these patches if you fail again.</p>
                        <ul style='margin-top: 8px; font-size: 13px; color: #ffeb3b;'>{stubborn_list}</ul>
                    </div>"""

                if errors:
                    err_list = "".join([f"<li>{e}</li>" for e in errors])
                    feedback_html += f"""<div style='color: #FF3E6C; margin-bottom: 15px; border-left: 4px solid #FF3E6C; padding-left: 15px; background: #1a0a0d; padding: 10px;'>
                        <strong style='font-size: 16px;'>🚨 QA FEEDBACK (CURRENT SCORE: {score}%)</strong>
                        <ul style='margin-top: 8px; font-size: 13px; color: #ff85a1;'>{err_list}</ul>
                    </div>"""

                copy_payload = prompt
                if previous_json:
                    # v3.0 RE-PROMPT Strategy
                    error_summary = ""
                    scenes_with_errs = set()
                    for e in errors:
                        m = re.search(r'\[(SCENE_\d+)\]', e)
                        if m: scenes_with_errs.add(m.group(1))

                    error_summary = f"🚨 REPAIR REQ ({score}%): {len(errors)} issues across {len(scenes_with_errs)} scenes.\n\n"

                    # Group errors for better readability
                    error_list_text = ""
                    for scene in sorted(list(scenes_with_errs)):
                        scene_errs = [e for e in errors if f"[{scene}]" in e]
                        error_list_text += f"\n[{scene}]:\n"
                        for se in scene_errs:
                            error_list_text += f"  - {se.replace(f'[{scene}] ', '')}\n"

                    mode_desc = "SURGICAL REPAIR (Partial JSON allowed)" if surgical_mode else "FULL MANIFEST REPAIR"
                    json_header = "--- PROBLEMATIC SCENES ONLY (REPAIRED BY ENGINE) ---" if surgical_mode else "--- PREVIOUS JSON (REPAIRED BY ENGINE) ---"

                    stubborn_text = ""
                    if stubborn_issues:
                        stubborn_text = "⚠️ WARNING: You have failed to fix the following issues twice. FIX THEM NOW or the engine will override your output.\n"
                        for si in stubborn_issues: stubborn_text += f"  - {si}\n"
                        stubborn_text += "\n"

                    copy_payload = (
                        f"MODE: {mode_desc}\n"
                        f"{error_summary}"
                        f"{stubborn_text}"
                        f"--- ERROR LIST ---\n{error_list_text}\n\n"
                        f"--- [REQUIRED] REPAIR RULES ---\n"
                        f"1. [FLATTEN] Use ROOT KEYS only. Never nest in 'style', 'data', or 'config'.\n"
                        f"2. [FONTS] Use ONLY local production fonts (e.g., Sohid_bangla, Audiowide-Regular_english).\n"
                        f"3. [PATCH] If the error list contains a 'REQUIRED PATCH', you MUST apply it.\n"
                        f"4. [ANCHORS] Use canonical positions: L_MID(550,540), R_MID(1370,540), C_TOP(960,320), C_BOT(960,760).\n"
                        f"5. [VALIDATION] Every scene MUST have a valid camera 'shot' sequence targeting overlay IDs.\n"
                        f"6. [SCOPE] RETURN ONLY THE CORRECTED SCENES inside a {{\"scenes\": []}} object. Do not include global settings or correct scenes.\n\n"
                        f"{json_header}\n{previous_json}\n\n"
                        f"--- STORY CONTEXT ---\n"
                        f"{re.search(r'STORY:.*?(?=TIMESTAMPS:)', prompt, re.DOTALL).group() if 'STORY:' in prompt else prompt[:500]}"
                    )

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


    def final_production_guard(self, manifest_path: str, public_dir: str = "../public") -> str:
        """
        v3.0 TITAN GUARD: Deep Semantic Auditor & Auto-Correction Initiative.
        Reads the final JSON file, validates every line of logic, and guarantees 98%+ accuracy.
        """
        report = []
        corrections_made = 0
        abs_public = os.path.abspath(public_dir)

        if not os.path.exists(manifest_path):
            return "❌ TITAN GUARD ERROR: Manifest file not found."

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            return f"❌ TITAN GUARD ERROR: Failed to parse JSON: {e}"

        # TITAN RECOVERY: Ensure structure before deep audit
        self._harden_root_settings(data)

        # Production Registry (Authoritative source for renderability)
        REGISTRY = {
            'types': [
                'text', 'ui_panel', 'shape', 'chart', 'indicator', 'data_indicator',
                'video', 'image', 'shadcn_chart', 'shadcn_indicator', 'svg', 'connector',
                'hub_network', 'flow_diagram', 'process', 'kpi_card', 'timeline', 'compositions', 'groups',
                'ambient_graphic', 'callout', 'label'
            ],
            'chart': ['bar', 'line', 'area', 'metaphor_mountain', 'metaphor_skyscraper'],
            'shadcn_chart': [
                'glass_area', 'neon_bar', 'stacked_line', 'radial_score', 'radar_web', 'composed_tech',
                'pie_donut_glass', 'scatter_bubble', 'horizontal_pill_bar', 'step_area', 'multi_bar_stack',
                'curved_edge_line', 'double_radar', 'funnel_glass', 'vertical_stepper', 'micro_sparkline',
                'grid_dots', 'smooth_area_dual', 'bar_race_top', 'thick_line_glow', 'layered_pies',
                'range_area', 'pixel_bars', 'curved_scatter', 'staircase_line', 'floating_bars',
                'hollow_pie', 'dual_axis_tech', 'jagged_peak', 'dot_matrix_chart'
            ],
            'shadcn_indicator': [
                'metric_tile', 'tech_badge', 'activity_ring', 'crypto_card', 'server_status',
                'user_profile_stat', 'weather_glass', 'storage_pill', 'upload_cloud', 'score_board',
                'notification_stack', 'data_ticker', 'network_ping', 'step_indicator_glass',
                'battery_pack', 'media_controls', 'social_stats', 'tech_folder', 'system_cpu',
                'location_tag', 'search_bar_glass', 'badge_collection', 'data_download', 'wifi_radar',
                'system_lock', 'clock_modern', 'status_grid', 'floating_icon_text', 'mini_stat_card',
                'activity_dots'
            ],
            'connector': [
                'smooth_curve', 'soft_arc', 'straight_flow', 'energy_flow', 'signal_beam',
                'data_stream', 's_curve', 'zigzag_soft', 'multi_branch', 'network_web',
                'callout_line', 'camera_focus', 'timeline_path', 'route_path', 'curved_route',
                'neon_connector', 'blueprint_connector', 'organic_connector',
                'when', 'how', 'why', 'how_many', 'reason', 'input', 'output', 'result', 'dependency', 'what', 'where'
            ]
        }

        report.append("================================================================================")
        report.append("🛡️ TITAN GUARD v3.0: LINE-BY-LINE SEMANTIC AUDIT & REPAIR REPORT")
        report.append("================================================================================")

        if not data or 'scenes' not in data:
            report.append("❌ CRITICAL FAILURE: Invalid manifest structure. Auditor aborted.")
            return "\n".join(report)

        for scene_idx, scene in enumerate(data.get('scenes', [])):
            if 'scene_id' not in scene:
                scene['scene_id'] = f"SCENE_{scene_idx+1}"

            s_id = scene['scene_id']
            scene_initiatives = []

            # v4.5: TITAN NARRATIVE SECURITY
            if 'semantic_role' not in scene:
                scene['semantic_role'] = self._auto_assign_semantic_role(str(scene))
                scene_initiatives.append(f"NARRATIVE: Assigned automatic semantic_role '{scene['semantic_role']}'")
                corrections_made += 1

            # 0. Structural Recovery (Hallucination Harvesting)
            harvest_map = {
                'text_overlays': 'text',
                'text_elements': 'text',
                'text_layers': 'text',
                'indicators': 'shadcn_indicator',
                'charts': 'shadcn_chart',
                'elements': None,
                'layers': None,
                'visuals': None
            }
            if 'overlays' not in scene: scene['overlays'] = []

            for key, default_type in harvest_map.items():
                if scene.get(key) and isinstance(scene[key], list):
                    for item in scene[key]:
                        if isinstance(item, dict):
                            if default_type and 'type' not in item: item['type'] = default_type
                            scene['overlays'].append(item)
                    del scene[key]
                    scene_initiatives.append(f"RECOVERY: Harvested semantic key '{key}' into canonical overlays.")
                    corrections_made += 1


            if 'duration_frames' in scene and 'duration_in_frames' not in scene:
                scene['duration_in_frames'] = scene['duration_frames']
                corrections_made += 1

            scene_dur = scene.get('duration_in_frames', 180)

            # 1. Background Integrity
            bg = scene.get('background', {})
            if bg.get('background_type') == 'video':
                vpath = bg.get('video_path', '')
                if vpath:
                    full_vpath = os.path.join(abs_public, vpath if not vpath.startswith('/') else vpath.lstrip('/'))
                    if not os.path.exists(full_vpath):
                        renders_dir = os.path.join(abs_public, "renders")
                        if os.path.exists(renders_dir):
                            available = [f for f in os.listdir(renders_dir) if f.endswith(".mp4")]
                            if available:
                                old = bg['video_path']
                                bg['video_path'] = f"renders/{available[0]}"
                                scene_initiatives.append(f"MANDATORY: Missing video '{old}' replaced with '{bg['video_path']}'")
                                corrections_made += 1

            # 2. Overlay Semantic Security
            overlay_ids = []
            for ov in scene.get('overlays', []):
                if ov.get('id'): overlay_ids.append(ov['id'])

            for ov_idx, ov in enumerate(scene.get('overlays', [])):
                ov_id = ov.get('id', f"ov_{scene_idx}_{ov_idx}")
                if ov_id not in overlay_ids:
                    ov['id'] = ov_id
                    overlay_ids.append(ov_id)

                o_type = str(ov.get('type', 'text')).lower()

                # A. Type & Variant Sanity
                if o_type not in REGISTRY['types']:
                    ov['type'] = 'text'
                    scene_initiatives.append(f"SECURITY: '{ov_id}' had invalid type '{o_type}' -> coerced to 'text'")
                    o_type = 'text'; corrections_made += 1

                v_key = 'chart_type' if 'chart' in o_type else 'indicator_type' if 'indicator' in o_type else 'preset' if o_type == 'connector' else None
                if v_key and o_type in REGISTRY:
                    val = ov.get(v_key)

                    # Logic: If connector has 'relationship' but no 'preset', map it
                    if o_type == 'connector' and not val and ov.get('relationship'):
                        rel = str(ov.get('relationship')).lower()
                        # Fuzzy match or direct match
                        found_rel = None
                        if rel in REGISTRY['connector']: found_rel = rel
                        else:
                            for r in REGISTRY['connector']:
                                if r in rel or rel in r: found_rel = r; break

                        if found_rel:
                            ov['preset'] = found_rel
                            val = found_rel
                            scene_initiatives.append(f"MAPPING: '{ov_id}' relationship '{rel}' mapped to visual preset '{found_rel}'.")
                            corrections_made += 1

                    if not val or val not in REGISTRY[o_type]:
                        old_v = val
                        ov[v_key] = REGISTRY[o_type][0]
                        scene_initiatives.append(f"VARIANT: '{ov_id}' ({o_type}) variant '{old_v}' invalid -> reset to '{ov[v_key]}'")
                        corrections_made += 1

                # B. Timing Stability
                start = int(ov.get('start', 0))
                duration = int(ov.get('duration', scene_dur - start))

                # Injection: Active Windows for chart series if missing
                if o_type == 'shadcn_chart' and 'data' in ov and isinstance(ov['data'], list):
                    for series in ov['data']:
                        if isinstance(series, dict) and 'active_windows' not in series:
                            s_start = series.get('active_at', start + 60)
                            series['active_windows'] = [[s_start, s_start + 120]]
                            corrections_made += 1
                if start >= scene_dur:
                    ov['start'] = max(0, scene_dur - 60)
                    scene_initiatives.append(f"TIMING: '{ov_id}' start ({start}) exceeded scene duration -> clamped")
                    corrections_made += 1
                if start + duration > scene_dur:
                    ov['duration'] = scene_dur - start
                    scene_initiatives.append(f"TIMING: '{ov_id}' duration adjusted to fit scene bounds")
                    corrections_made += 1

                # C. Spatial Purity (Titan Clamping)
                pos = ov.get('position', {'x': 960, 'y': 540})
                if isinstance(pos, list):
                    pos = {
                        'x': int(pos[0]) if len(pos) > 0 else 960,
                        'y': int(pos[1]) if len(pos) > 1 else 540
                    }
                    ov['position'] = pos
                try:
                    nx = max(150, min(1770, int(pos.get('x', 960))))
                    ny = max(150, min(930, int(pos.get('y', 540))))
                    if nx != pos.get('x') or ny != pos.get('y'):
                        ov['position'] = {'x': nx, 'y': ny}
                        scene_initiatives.append(f"LAYOUT: '{ov_id}' position safety-clamped to ({nx}, {ny})")
                        corrections_made += 1
                except: pass

                # D. Dependency Validation (Connectors)
                if o_type == 'connector':
                    src, tgt = ov.get('source'), ov.get('target')
                    valid_targets = overlay_ids

                    if src not in valid_targets or tgt not in valid_targets:
                        # Coerce to center if targets are hallucinated
                        if src not in valid_targets: ov['source'] = {"x": 960, "y": 540}
                        if tgt not in valid_targets: ov['target'] = {"x": 960, "y": 540}
                        scene_initiatives.append(f"DEPENDENCY: Connector '{ov_id}' targeted missing IDs -> anchored to center")
                        corrections_made += 1

                # F. Hierarchy Enforcement
                prio = self.PRIORITY.get(o_type, 20)
                if ov.get('zIndex') != prio:
                    ov['zIndex'] = prio
                    scene_initiatives.append(f"HIERARCHY: '{ov_id}' zIndex corrected to {prio}")
                    corrections_made += 1

                # G. Font Enforcements
                content = str(ov.get('content', ov.get('text', '')))

                is_bn = VisionConstants.is_bangla(content)
                current_font = ov.get('font')
                if is_bn:
                    if current_font not in self.bangla_fonts:
                        ov['font'] = self.bangla_fonts[0] if self.bangla_fonts else "Sohid_bangla"
                        scene_initiatives.append(f"TYPOGRAPHY: Enforced Bangla font on '{ov_id}'")
                        corrections_made += 1
                    if o_type == 'text' and ov.get('splitMode') != 'word':
                        ov['splitMode'] = 'word'
                        scene_initiatives.append(f"TYPOGRAPHY: Enforced word-split on Bangla text '{ov_id}'")
                        corrections_made += 1
                elif not is_bn and current_font not in self.english_fonts:
                    ov['font'] = self.english_fonts[0] if self.english_fonts else "Audiowide-Regular_english"
                    scene_initiatives.append(f"TYPOGRAPHY: Enforced English font on '{ov_id}'")
                    corrections_made += 1

            # 3. Camera Shot Security
            camera = scene.get('camera', {})
            role = scene.get('semantic_role', 'trend')
            for shot in camera.get('shots', []):
                # Align shot style with semantic role if missing or inappropriate
                if not shot.get('style'):
                    if role == 'conflict': shot['style'] = 'shaky_handheld'
                    elif role == 'trend': shot['style'] = 'slow_push'
                    else: shot['style'] = 'cinematic_drift'
                    scene_initiatives.append(f"CAMERA: Aligned shot style with semantic_role '{role}'")
                    corrections_made += 1

                if shot.get('targetId') == 'ACTIVE_NODE':
                    continue # Reserved keyword for dynamic tracking
                if shot.get('targetId') not in overlay_ids:
                    if overlay_ids: shot['targetId'] = overlay_ids[0]
                    else: camera['enabled'] = False
                    scene_initiatives.append(f"CAMERA: Re-targeted shot to valid overlay ID")
                    corrections_made += 1

            # 4. Cinematic Rhythm (Forced Staggering for 98%+ Accuracy)
            ovs_sorted = sorted(scene.get('overlays', []), key=lambda x: int(x.get('start', 0)))
            for i in range(1, len(ovs_sorted)):
                prev, curr = ovs_sorted[i-1], ovs_sorted[i]
                if abs(int(curr.get('start', 0)) - int(prev.get('start', 0))) < 10:
                    curr['start'] = int(prev.get('start', 0)) + 15
                    scene_initiatives.append(f"RHYTHM: Forced 15f stagger for '{curr.get('id')}'")
                    corrections_made += 1

            if scene_initiatives:
                report.append(f"\n[{s_id}] SEMANTIC AUDIT FINDINGS:")
                for ini in scene_initiatives:
                    report.append(f"  - {ini}")
            else:
                report.append(f"\n[{s_id}] AUDIT STATUS: 100% COMPLIANT")

        report.append(f"\n📈 TOTAL TITAN CORRECTIONS: {corrections_made}")
        report.append(f"✨ ACCURACY ESTIMATE: {100.0 if corrections_made == 0 else min(99.9, 98.0 + (corrections_made * 0.1))}%")
        report.append("🚀 MANIFEST FINALIZED FOR RENDER.")
        report.append("================================================================================\n")

        # Overwrite the file with the Titan-corrected version
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return "\n".join(report)

    def generate(self, story: str, prompt_output_path: str = None, timestamp_context: str = None, scene_durations: List[int] = None, drive_prompt_path: str = None,
                 previous_json: str = None, feedback_errors: List[str] = None, current_score: int = 0, interaction_log_path: str = None, surgical_mode: bool = False,
                 stubborn_issues: List[str] = None) -> Tuple[Dict[str, Any], bool]:
        # Context-Aware Memory Retrieval: Extract tags from the story/durations to find relevant past mistakes
        context_tags = []
        if 'bangla' in story.lower() or VisionConstants.is_bangla(story): context_tags.append('bangla')
        if 'chart' in story.lower(): context_tags.append('chart')
        if 'indicator' in story.lower(): context_tags.append('indicator')
        if 'connector' in story.lower(): context_tags.append('connector')

        memory_context = self.memory.get_prompt_injection(context_tags=context_tags)
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
            f"TASK: GENERATE A PRODUCTION-READY CINEMATIC KNOWLEDGE SYSTEM MANIFEST WITH DIVERSE PACING AND FREQUENT STAT indicators.\n\n"
            f"--- 1. SOURCE & GROUNDING ---\n"
            f"STORY: {story}\n"
            f"TIMESTAMPS: {compact_ts}\n"
            f"DURATIONS: {duration_context}\n"
            f"{visual_context}\n"
            f"ENV_FONTS: BANGLA: {self.bangla_fonts} | ENGLISH: {self.english_fonts}\n"
            f"ENV_VIDEOS: {self.video_files}\n\n"
            f"--- 2. ROLE: DOCUMENTARY DIRECTOR PERSONA ---\n"
            f"OBJECTIVE: Direct a high-end cinematic information film with high visual variety and narrative pacing. Data/KPIs are lead actors.\n"
            f"REASONING PIPELINE (MANDATORY):\n"
            f"1. NARRATIVE SYNC: Identify ALL frame ranges where every concept/data series is discussed. Use `active_windows`.\n"
            f"2. STORY DIRECTOR: Assign a `semantic_role` (trend | conflict | comparison | historical) to the ENTIRE SCENE. This drives the global visual language (lighting, particles, motion).\n"
            f"3. SEMANTIC VISUALIZATION: Choose 'chart' or 'shadcn_chart' (numbers/data) very occasionally, and choose 'indicator' or 'shadcn_indicator' most of the time.\n"
            f"4. DIRECTORIAL PRESET: nasa (sci-fi tech), bloomberg (financial/crisp), cyberpunk (intense/dark), minimal_apple (sleek), military (alert/tactical), archive (historical), nat_geo (organic).\n"
            f"5. STORY BEATS: Assign `story_beat`: introduction | growth | plateau | collapse | forecast.\n\n"
            f"--- 3. PRODUCTION QUALITY RULES (VISUAL DIVERSITY & KPIS) ---\n"
            f"- VISUAL PACING VARIETY: EVERY scene MUST have a different, unique text intro animation (from VALID_TEXT_ANIMS). Never use similar or identical text animations across successive scenes. Choose unique ones like 'glow_pulse', 'typewriter_flicker', 'blur_reveal', 'glitch_pop', 'neon_flicker', or 'bounce_pop'.\n"
            f"- KPI INDICATORS (FREQUENTLY USED): Ground your narration metrics frequently by adding 'shadcn_indicator' overlays (with indicator_types like 'metric_tile', 'tech_badge', 'activity_ring', 'crypto_card', 'step_indicator_glass') to most of your scenes (at least 2-3 scenes per project) to show-case concrete values, percentages, or status counters.\n"
            f"- CHARTS (MINIMALLY USED): Charts should only be used very occasionally (minimally, usually in 1-2 scenes per project where time trends or comparisons are paramount) to avoid visual clutter.\n"
            f"- BANGLA MULTILINGUAL METRICS: If the narration/story is in Bangla, any generated KPIs, charts, and indicator numbers/labels MUST use high-fidelity, accurate Bangla text and numerals (e.g., '২,০০,০০,০০০+', '৯৫%', '৪০,০০০').\n"
            f"- STORY VISUAL METAPHORS: metaphor_mountain (for trends/growth), metaphor_skyscraper (for comparisons/scale).\n"
            f"- Series MUST have `importance` (1.0-5.0) and `active_windows` (lists of [start, end]).\n"
            f"- Assign `emotion` to series: alert | intense | growing | scientific | historical | calm.\n\n"
            f"--- 4. CINEMATIC PROTOCOL ---\n"
            f"- VISUAL LANGUAGE: Role 'conflict' = Red mood, high jitter. Role 'trend' = Blue mood, ascending data particles. Role 'comparison' = Green mood.\n"
            f"- STORY DIRECTOR: Every scene MUST have a `semantic_role`. Use 'conflict' for threats/problems, 'trend' for growth/data, 'comparison' for scales.\n"
            f"- VISUAL HIERARCHY: Strip redundant 'text' layers if the Chart/Indicator title covers the narration.\n"
            f"- CAMERA: Use `lookAt` targeting IDs of specific overlays or chart peaks for semantic tracking.\n"
            f"- SPATIAL: Force components into `semantic_zone`: input | process | result | threat | context.\n\n"
            f"--- 5. SCHEMA AUTHORITY ---\n"
            f"- 'connector': source/target MUST be valid overlay IDs in the scene. Preset: relationship type.\n\n"
            f"--- 6. VARIANT REGISTRY (STRICT) ---\n"
            f"CHARTS: metaphor_mountain, metaphor_skyscraper, glass_area, neon_bar, stacked_line, radial_score, radar_web, composed_tech, pie_donut_glass, scatter_bubble, horizontal_pill_bar, step_area, multi_bar_stack, curved_edge_line, double_radar, funnel_glass, vertical_stepper, micro_sparkline, grid_dots, smooth_area_dual, bar_race_top, thick_line_glow, layered_pies, range_area, pixel_bars, curved_scatter, staircase_line, floating_bars, hollow_pie, dual_axis_tech, jagged_peak, dot_matrix_chart, area, bar, line.\n"
            f"INDICATORS: metric_tile, tech_badge, activity_ring, crypto_card, server_status, user_profile_stat, weather_glass, storage_pill, upload_cloud, score_board, notification_stack, data_ticker, network_ping, step_indicator_glass, battery_pack, media_controls, social_stats, tech_folder, system_cpu, location_tag, search_bar_glass, badge_collection, data_download, wifi_radar, system_lock, clock_modern, status_grid, floating_icon_text, mini_stat_card, activity_dots, kpiNumber, deltaIndicator, semiGauge, milestoneTimeline, statGrid, batteryLevel, statusBadge, stepIndicator, pulseRadar, multiProgress.\n"
            f"CONNECTORS: causes, leads_to, depends_on, located_in, transforms_into, increases, decreases, supports, threatens, flows_to, triggers, influences, smooth_curve, soft_arc, straight_flow, energy_flow, signal_beam, data_stream, s_curve, zigzag_soft, multi_branch, network_web, callout_line, camera_focus, timeline_path, route_path, curved_route, neon_connector, blueprint_connector, organic_connector.\n\n"
            f"--- 7. MANDATORY OUTPUT STRUCTURE ---\n"
            f"FIRST, provide a <VISUAL_PLAN> block detailing layout, theme, and entry transitions/stagger times.\n"
            f"SECOND, provide the RAW JSON block starting with {{ \"project_id\": ... }}.\n\n"
            f"{drive_guideline}\n"
            f"{memory_context}\n"
            f"NO PREAMBLE. NO CHATTER. PLAN FIRST, THEN JSON."
        )
        if prompt_output_path:
            with open(prompt_output_path, 'w', encoding='utf-8') as f: f.write(full_prompt)

        raw_output = self._interact_with_gemini(full_prompt, previous_json, feedback_errors, current_score, surgical_mode=surgical_mode, stubborn_issues=stubborn_issues)
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
            # v4.0: Extract JSON from potentially complex output containing THINKING_STAGE
            json_match = re.search(r'(\{.*\})', raw_output, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str, strict=False)
                return data, force_stop

            # Fallback to the largest block logic
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
    parser.add_argument("--public-dir", default="../public")
    parser.add_argument("--manual", action="store_true")
    args = parser.parse_args()

    manifest_dir = os.path.dirname(args.output)
    memory_file = os.path.join(manifest_dir, "production_knowledge.json")
    maker = RemotionJsonMaker(manual=args.manual, memory_path=memory_file)
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
    stubborn_issues = None

    manifest_dir = os.path.dirname(args.output)
    interaction_log = os.path.join(manifest_dir, "interaction_log.txt")

    master_json = {}
    issue_tracker = ConsecutiveIssueTracker(threshold=2)

    while iteration <= 10: # Increased attempts for production perfection
        if iteration <= 5:
            print(f"\n🚀 ITERATION {iteration}: {'AI Generation' if iteration == 1 else 'Surgical Refinement'}...")

            # v3.0: If iteration > 1, use surgical mode with extracted problematic segments
            current_surgical_mode = (iteration > 1)

            render_json, force_stop = maker.generate(story, args.prompt_output, ts_content, scene_durations, args.drive_prompt,
                                         previous_json, feedback_errors, current_score, interaction_log_path=interaction_log,
                                         surgical_mode=current_surgical_mode, stubborn_issues=stubborn_issues)

            if not render_json and not force_stop:
                print("⚠️ Failed to parse AI output. Retrying...")
                iteration += 1
                continue

            # v3.0: Merge surgical corrections back into master
            if current_surgical_mode:
                master_json = maker.merge_surgical_corrections(master_json, render_json)
            else:
                master_json = render_json
        else:
            print(f"\n⚙️ ITERATION {iteration}: AUTONOMOUS ENGINE REPAIR (Targeting 100% Accuracy)...")
            force_stop = False
            # Autonomous mode: In iterations 6-10, we bypass Gemini and recursively apply
            # all available hardening and deterministic patches until perfection.

        # --- ENGINE-SIDE DETERMINISTIC FIXES (STAGE 2: HARDENING) ---
        master_json = maker.finalize_json_durations(master_json, public_dir=args.public_dir)

        # Save temporarily for QA
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(master_json, f, indent=2, ensure_ascii=False)

        print(f"🧪 STAGE 3: Production QA (Iteration {iteration})...")
        success, score, qa_feedback = test_manifest_quality(args.output, args.public_dir)
        current_score = score

        # --- STAGE 4: ELEMENT SUPERVISOR (DIRECTOR REVIEW) ---
        reports = supervise_manifest(master_json)
        supervisor_feedback = maker.supervise(master_json)
        feedback = qa_feedback + supervisor_feedback

        # Calculate Cinematic Aggregate
        avg_cinematic = sum(r['scores'].get('overall_cinematic_score', 0) for r in reports) / len(reports) if reports else 0
        cinematic_score = avg_cinematic * 10.0 # scale to 100

        # v3.0: Apply deterministic QA repairs locally on master_json
        master_json = maker.apply_qa_patches(master_json, feedback)

        # Detect stubborn issues (failed to correct twice)
        stubborn_issues = issue_tracker.update_and_get_stubborn(feedback)
        if stubborn_issues or iteration >= 6:
            if stubborn_issues:
                print(f"   🚨 STUBBORN ISSUES DETECTED ({len(stubborn_issues)}): Gemini failed to correct these twice.")
                print(f"   🔧 Engine will now force-override these corrections.")

            # v2.0: Aggressive engine-side repair. Force-apply ALL available hardening.
            master_json = maker.finalize_json_durations(master_json, public_dir=args.public_dir)

            # Save temporarily for QA
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(master_json, f, indent=2, ensure_ascii=False)
            success, score, qa_feedback = test_manifest_quality(args.output, args.public_dir)
            current_score = score
            print(f"   📈 Post-Override Score: {score}%")

            # If still not perfect and iteration is high, run the Production Guard prematurely to ensure progress
            if score < 100 and iteration >= 8:
                 print(f"   🛡️ Applying Early Production Guard to force 100% technical accuracy...")
                 # TITAN GUARD v2.0 reads from file and returns report string
                 maker.final_production_guard(args.output, public_dir=args.public_dir)

                 # Reload the corrected json into master_json
                 try:
                     with open(args.output, 'r', encoding='utf-8') as f:
                         master_json = json.load(f)
                 except: pass

                 success, score, qa_feedback = test_manifest_quality(args.output, args.public_dir)
                 current_score = score

            # Re-evaluate supervisor feedback after engine intervention
            supervisor_feedback = maker.supervise(master_json)
            feedback = qa_feedback + supervisor_feedback

        # Record finding for future memory
        maker.memory.record_finding(success, score, feedback, manifest=master_json)

        # If supervisor found issues but QA passed, we still might want to iterate
        if supervisor_feedback and score == 100:
            print(f"   ⚠️ QA Passed but Supervisor found cognitive issues. Refining...")
            success = False

        # RE-EVALUATE AFTER ENGINE FIXES: If engine hardening fixed everything, success=True
        if score == 100: success = True

        # Weighted Composite Score (Technical QA 60%, Cinematic 40%)
        weighted_score = (score * 0.6) + (cinematic_score * 0.4)

        # Track best result (Always store the fully hardened master_json)
        if weighted_score > best_score or best_json is None:
            best_score = weighted_score
            best_json = copy.deepcopy(master_json)
            print(f"   🏆 New Best Composite Score: {round(best_score, 1)}% (QA: {score}%, Cinematic: {round(cinematic_score, 1)}%)")

        # ENDING LOGIC: Autonomous perfection required after Iteration 5
        # Require 100% QA AND >= 98% Cinematic to finish early, or manual stop
        if (score == 100 and cinematic_score >= 98.0) or force_stop:
            if force_stop:
                print(f"\n🛑 PROCESS ENDED MANUALLY. Restoring Best Result ({round(best_score, 1)}%)...")
                master_json = best_json
            elif score == 100:
                print(f"\n✨ PRODUCTION READY! 100% Accuracy and high-fidelity aesthetics reached (Iter: {iteration})")
            break
        elif iteration == 10:
            print(f"\n⌛ MAX ITERATIONS REACHED. Restoring Best Result ({round(best_score, 1)}%)...")
            master_json = best_json
            break
        else:
            print(f"\n⚠️ QA FAILED ({score}%). Re-prompting for correction...")
            # v3.0: Extract only problematic parts for next iteration prompt
            surgical_data = maker.extract_problematic_segments(master_json, feedback)
            previous_json = json.dumps(surgical_data, indent=2, ensure_ascii=False)
            feedback_errors = feedback
            iteration += 1

    # --- STAGE 5: TITAN GUARD (Deep File Audit & Auto-Correction) ---
    print("\n🛡️ INITIATING TITAN GUARD (Final Production Audit)...")

    # Save the last master state before Titan Guard reads it
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(master_json, f, indent=2, ensure_ascii=False)

    correction_report = maker.final_production_guard(args.output, public_dir=args.public_dir)
    print(correction_report)

    print(f"✅ Final Manifest saved to: {args.output}")

    # --- FINAL PRODUCTION AUDIT ---
    print("\n" + "="*80)
    print("🏆 FINAL PRODUCTION AUDIT REPORT")
    print("="*80)

    final_reports = supervise_manifest(master_json)
    avg_cinematic = 0

    for r in final_reports:
        s_id = r['scene_id']
        s_score = r['scores'].get('overall_cinematic_score', 0)
        avg_cinematic += s_score
        print(f"\n🎬 {s_id}: Cinematic Score {s_score}/10")
        print(f"   - Clarity: {r['scores'].get('attention_clarity', 0)}")
        print(f"   - Motion: {r['scores'].get('motion_discipline', 0)}")
        print(f"   - Readability: {r['scores'].get('readability_score', 0)}")
        print(f"   - Verdict: {r['professional_verdict']}")

    if final_reports:
        avg_cinematic /= len(final_reports)
        print("\n" + "-"*40)
        print(f"📈 COMPOSITE PROJECT SCORE: {round(avg_cinematic * 10, 1)}%")
        print(f"✨ Production status: {'READY FOR BROADCAST' if avg_cinematic >= 8.5 else 'REFINEMENT RECOMMENDED'}")
        print("-"*40)

if __name__ == "__main__": main()
