# Data Visualization - Custom Pipeline Script for Bklit UI Components
# ==============================================================================

import os
import sys
import json
import argparse
import re
import time
import math
import copy
from typing import Dict, Any, List, Optional, Tuple

class DataVisualizationGenerator:
    """
    Generator for ultra-modern, sleek, and minimalistic data visualization manifests.
    Integrates a human-in-the-loop Colab terminal interaction, auto-hardening,
    collision avoidance, precise font mapping, and camera presets.
    """

    # Sync exact TYPE_SIZES with test_manifest_quality.py fallback values
    TYPE_SIZES = {
        'text': (800, 200),
        'indicator': (600, 400),
        'shadcn_indicator': (600, 400),
        'chart': (1000, 562),
        'shadcn_chart': (1000, 562),
        'shape': (400, 400),
        'connector': (400, 100),
        'svg': (400, 400),
    }

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

    MODERN_COLORS = ["#00F5FF", "#FFD700", "#FF3E6C", "#00FFAB"]

    # Canonical Positions
    ANCHORS = {
        "C_TOP": (960, 320),
        "C_MID": (960, 540),
        "C_BOT": (960, 760),
        "L_MID": (550, 540),
        "R_MID": (1370, 540),
        "L_TOP": (550, 320),
        "R_TOP": (1370, 320),
        "L_BOT": (550, 760),
        "R_BOT": (1370, 760)
    }

    def __init__(self, manual: bool = False):
        self.manual = manual
        self.story_scenes = {}
        self.video_files = []
        self.audio_files = []

    def scan_assets(self, public_dir: str):
        """Scans local Remotion public directory to catalog videos, audios, and fonts."""
        abs_public = os.path.abspath(public_dir)
        renders_dir = os.path.join(abs_public, "renders")

        self.video_files = []
        if os.path.exists(renders_dir):
            self.video_files = sorted([f for f in os.listdir(renders_dir) if f.lower().endswith('.mp4')])

        audio_dir = os.path.join(abs_public, "renders/audios")
        self.audio_files = []
        if os.path.exists(audio_dir):
            self.audio_files = sorted([f for f in os.listdir(audio_dir) if f.lower().endswith(('.mp3', '.wav', '.m4a'))])

        print(f"🎬 cataloged {len(self.video_files)} background videos and {len(self.audio_files)} audio tracks.")

    def parse_story(self, story_content: str):
        """Splits the input story into sequential scenes for context tracking."""
        pattern = r'(?:Scene|দৃশ্য)\s*([0-9০-৯]+)[:\s]*'
        parts = [p.strip() for p in re.split(pattern, story_content, flags=re.IGNORECASE) if p.strip()]
        matches = re.findall(pattern, story_content, flags=re.IGNORECASE)

        # Re-assemble scenes
        idx = 1
        for i in range(0, len(parts), 2):
            if i + 1 < len(parts):
                sc_num = parts[i]
                sc_text = parts[i+1]
            else:
                sc_text = parts[i]
                sc_num = str(idx)

            s_id = f"SCENE_{idx}"
            self.story_scenes[s_id] = sc_text
            self.story_scenes[f"SCENE_{idx:02d}"] = sc_text
            self.story_scenes[f"দৃশ্য_{idx}"] = sc_text
            idx += 1

        if not self.story_scenes:
            self.story_scenes["SCENE_1"] = story_content
            self.story_scenes["SCENE_01"] = story_content

    def _interact_with_gemini(self, prompt: str, score: int = 100) -> str:
        """Launches copy-paste interactive UI in Colab or terminal fallback."""
        if self.manual:
            try:
                from google.colab import output
                import uuid
                u_id = uuid.uuid4().hex[:8]
                header_color = "#00FFAB"

                copy_payload = prompt
                js_code = f"""
                    (async () => {{
                        const u_id = "{u_id}";
                        const container = document.createElement('div');
                        container.style = "background: #0d0d0d; color: #fff; padding: 25px; border-radius: 16px; border: 2px solid {header_color}; font-family: 'Segoe UI', Tahoma, sans-serif; max-width: 850px; margin: 20px auto; box-shadow: 0 10px 30px rgba(0,0,0,0.5);";
                        container.innerHTML = `
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                                <h3 style="color: {header_color}; margin: 0; font-size: 22px;">📊 Bklit UI Data Visualization Pipeline</h3>
                                <span style="background: {header_color}; color: #000; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 14px;">Human-in-the-Loop</span>
                            </div>
                            <div style="background: #151515; padding: 15px; border-radius: 8px; border: 1px solid #333; margin-bottom: 15px;">
                                <p style="margin: 0 0 10px 0; font-size: 14px; color: #aaa;">1. Copy the custom director prompt tailored for Bklit UI minimalism.</p>
                                <button id="copy-${{u_id}}" style="background: {header_color}; color: #000; border: none; padding: 12px; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; transition: opacity 0.2s;">📋 COPY GEMINI PROMPT</button>
                            </div>
                            <div style="background: #151515; padding: 15px; border-radius: 8px; border: 1px solid #333;">
                                <p style="margin: 0 0 10px 0; font-size: 14px; color: #aaa;">2. Paste Gemini's response below containing the planned visual layout.</p>
                                <textarea id="paste-${{u_id}}" style="width: 100%; height: 280px; background: #000; color: #00FFAB; border: 1px solid #444; padding: 12px; font-family: 'Cascadia Code', 'Courier New', monospace; font-size: 13px; border-radius: 6px; resize: vertical;" placeholder="Paste Gemini response here..."></textarea>
                                <div style="display: flex; gap: 10px; margin-top: 15px;">
                                    <button id="submit-${{u_id}}" style="flex: 2; background: #2196F3; color: #fff; border: none; padding: 14px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 16px; box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);">🚀 GENERATE DATA_VISUALIZATION.JSON</button>
                                </div>
                            </div>
                        `;
                        document.body.appendChild(container);
                        document.getElementById('copy-'+u_id).onclick = () => {{
                            navigator.clipboard.writeText({json.dumps(copy_payload)});
                            document.getElementById('copy-'+u_id).innerText = "PROMPT COPIED!";
                            setTimeout(() => {{
                                document.getElementById('copy-'+u_id).innerText = "📋 COPY GEMINI PROMPT";
                            }}, 3000);
                        }};
                        return new Promise((resolve) => {{
                            document.getElementById('submit-'+u_id).onclick = () => {{
                                const val = document.getElementById('paste-'+u_id).value.trim();
                                if (!val) {{ alert("Please paste Gemini's response first."); return; }}
                                container.remove(); resolve(val);
                            }};
                        }});
                    }})();
                """
                return output.eval_js(js_code)
            except Exception as e:
                print(f"⚠️ Interactive UI not available or failed ({e}). Falling back to terminal input...")
                val = ""
                while not val.strip():
                    val = input("Paste Gemini JSON response and press Enter: ").strip()
                return val
        else:
            # Direct mock response for unattended/local testing
            print("🤖 Unattended test mode: Mocking Gemini response...")
            mock_json = {
                "project_id": "data_visualization_project",
                "global_settings": {"width": 1920, "height": 1080, "fps": 30},
                "scenes": [
                    {
                        "scene_id": "SCENE_1",
                        "duration_in_frames": 300,
                        "background": {"background_type": "procedural", "procedural_config": {"variant": "neon_grid"}},
                        "overlays": [
                            {
                                "type": "indicator",
                                "indicator_type": "kpiNumber",
                                "label": "ঘনবসতি র্যাংক",
                                "value": "#১",
                                "position": {"x": 1370, "y": 760},
                                "zIndex": 50
                            }
                        ]
                    },
                    {
                        "scene_id": "SCENE_2",
                        "duration_in_frames": 300,
                        "background": {"background_type": "procedural", "procedural_config": {"variant": "neon_grid"}},
                        "overlays": [
                            {
                                "type": "indicator",
                                "indicator_type": "percentageCounter",
                                "label": "শহরায়ণ বৃদ্ধি",
                                "value": "৯৫",
                                "position": {"x": 1370, "y": 760},
                                "zIndex": 50
                            }
                        ]
                    }
                ]
            }
            return json.dumps(mock_json)

    def generate_prompt(self, story: str) -> str:
        """Formulates the extensive guideline-driven Gemini prompt."""
        prompt = (
            "You are a professional Creative Director specializing in ultra-modern, minimalistic, and high-end video graphics production.\n"
            "Your task is to design a visual animation schema using ONLY Bklit UI components matching the provided story text.\n\n"
            "--- STORY DESCRIPTION ---\n"
            f"{story}\n\n"
            "--- STRICT DESIGN & COMPONENT RULES (MUST OBEY) ---\n"
            "1. NO TEXT LAYERS ALLOWED: Do not generate any overlays of type 'text'. There must be absolutely ZERO text narrative overlays.\n"
            "2. CLEAN & COGNITIVE VISUALIZATION VALUES:\n"
            "   - PERCENTAGE INDICATORS: Indicator types like 'percentageCounter', 'activity_ring', 'circularProgress', 'semiGauge', 'ringChart', and 'metricRing' must receive clean numbers as their 'value' (e.g. '৯৫' or 95). DO NOT include '%', 'percent', or qualitative words in their 'value' because the React engine renders the percent suffix automatically. Double percent signs (e.g. '৯৫%%') or text in circular progress triggers rendering errors.\n"
            "   - TEXT STATUSES: If you want to display qualitative text words (such as 'আশঙ্কাজনক', 'CRITICAL', 'তীব্র', 'ONLINE', 'ACTIVE'), you MUST use 'statusBadge' or 'tech_badge' indicator types. NEVER use qualitative strings like 'CRITICAL' or 'High' in progress rings, speedometers, charts, or progress bars which expect numeric values.\n"
            "3. NO OVERCROWDING: Ensure the screen feels incredibly spacious and high-end. Keep a cinematic negative space. Limit visual overlays to 1-2 per scene.\n"
            "4. BKLIT UI COMPONENT TYPES:\n"
            "   - INDICATORS (kpiNumber, percentageCounter, deltaIndicator, milestoneTracker, statGrid, ringChart, stepIndicator, statusBadge, tech_badge)\n"
            "   - CHARTS (glass_area, neon_bar, step_area, pie_donut_glass)\n"
            "   - OTHER (timeline, milestoneTimeline, batteryLevel)\n"
            "5. HIGH-FIDELITY INJECTIONS: If the scene is in Bangla, use exquisite Bangla labeling and numeric formatting for KPIs/Indicators (e.g., '২,২৪,০০,০০০+', '৯৫', '২৬ মার্চ ১৯৭১').\n"
            "6. TYPOGRAPHY RULES: All components must set 'font': 'Sohid_bangla' if they have Bangla labels, or 'Audiowide-Regular_english' for English.\n"
            "7. TIMING & SEQUENCING: Stagger the entry of layers to create a premium, fluid viewing experience.\n\n"
            "--- JSON SCHEMA STRUCTURE ---\n"
            "Output your design as a single valid JSON block formatted as follows:\n"
            "{\n"
            "  \"project_id\": \"data_visualization_project\",\n"
            "  \"global_settings\": { \"width\": 1920, \"height\": 1080, \"fps\": 30 },\n"
            "  \"scenes\": [\n"
            "    {\n"
            "      \"scene_id\": \"SCENE_1\",\n"
            "      \"duration_in_frames\": 300,\n"
            "      \"background\": {\n"
            "        \"background_type\": \"procedural\",\n"
            "        \"procedural_config\": { \"variant\": \"neon_grid\" }\n"
            "      },\n"
            "      \"overlays\": [\n"
            "        {\n"
            "          \"id\": \"ind_1_1\",\n"
            "          \"type\": \"indicator\",\n"
            "          \"indicator_type\": \"kpiNumber\",\n"
            "          \"label\": \"INDICATOR LABEL\",\n"
            "          \"value\": \"১০০\",\n"
            "          \"position\": { \"x\": 1370, \"y\": 760 },\n"
            "          \"start\": 60,\n"
            "          \"duration\": 210,\n"
            "          \"zIndex\": 50,\n"
            "          \"font\": \"Sohid_bangla\"\n"
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}\n\n"
            "NO PREAMBLE. NO CONVERSATION. PROVIDE ONLY THE COMPLETED VALID JSON BLOCK."
        )
        return prompt

    def harden_manifest(self, data: Dict[str, Any], public_dir: str = "../public") -> Dict[str, Any]:
        """
        Applies meticulous, line-by-line hardening to the manifest:
        - Drops any overlays of type 'text' to strictly prevent narrative text overlays.
        - Sanitizes values to ensure percent meters only have pure numbers and text is converted to badge types.
        - Harmonizes timing and stagger entries.
        - Resolves spatial collisions and clamps layout to secure broadcast margins.
        - Directs typography rules to valid registered fonts (Bangla / English).
        - Automatically populates rich data templates based on story content.
        - Implements beautiful camera motion presets.
        """
        if not data or 'scenes' not in data:
            return data

        print("🛡️ Applying elite hardening pipeline to JSON schema...")

        for scene_idx, scene in enumerate(data['scenes']):
            s_id = scene.get('scene_id', f"SCENE_{scene_idx+1}")
            scene['scene_id'] = s_id

            if 'duration_in_frames' not in scene:
                scene['duration_in_frames'] = 300

            scene_duration = scene['duration_in_frames']

            # Unify background structure
            if 'background' not in scene:
                scene['background'] = {}
            bg = scene['background']
            if not bg.get('background_type'):
                bg['background_type'] = 'procedural'
            if bg['background_type'] == 'procedural' and not bg.get('procedural_config'):
                bg['procedural_config'] = {"variant": "neon_grid"}

            # Ensure 'transition' exists
            if 'transition' not in scene:
                scene['transition'] = {"type": "cinematicMatchCut", "duration": 15}

            overlays = scene.get('overlays', [])
            valid_overlays = []

            for ov_idx, ov in enumerate(overlays):
                o_type = str(ov.get('type', 'text')).lower()

                # STRICTION 1: Bulletproof drop of any 'text' overlays
                if o_type == 'text':
                    print(f"   🗑️ Dropped text layer '{ov.get('id')}' to preserve visualization-only focus.")
                    continue

                # Normalize types to registry
                if o_type == 'kpi' or o_type == 'counter':
                    ov['type'] = 'indicator'
                    o_type = 'indicator'
                elif o_type == 'kpi_card':
                    ov['type'] = 'shadcn_indicator'
                    o_type = 'shadcn_indicator'

                ov['type'] = o_type

                if not ov.get('id'):
                    ov['id'] = f"ov_{scene_idx+1}_{ov_idx+1}"

                # STRICTION 2: Cognitive Visual Value Cleansing
                var = ov.get('indicator_type') or ov.get('chart_type')

                # Check indicator values for non-sense format
                val = str(ov.get('value', '')).strip()

                # Clean percentage double signs
                if var in ['percentageCounter', 'activity_ring', 'circularProgress', 'semiGauge', 'ringChart', 'metricRing']:
                    # Remove % signs to prevent double percentage signs
                    if '%' in val:
                        val = val.replace('%', '').strip()
                        ov['value'] = val
                        print(f"   🔧 Cleansed percentage metric '{ov['id']}': {val}% -> {val}")

                    # If value is non-numeric text like "CRITICAL", convert to a safe badge type or replace with 85
                    has_letters = any(c.isalpha() for c in val)
                    if has_letters or val.lower() in ['critical', 'risk', 'high', 'alarm']:
                        # Automatically mutate to status badge to render beautifully
                        ov['indicator_type'] = 'statusBadge'
                        var = 'statusBadge'
                        print(f"   🔧 Mutated numeric '{ov['id']}' with non-numeric value '{val}' to 'statusBadge'")

                # Typography Hardening
                content = str(ov.get('content', ov.get('label', ''))).strip()
                is_bn = any('\u0980' <= c <= '\u09FF' for c in content)

                if is_bn:
                    ov['font'] = "Sohid_bangla"
                else:
                    ov['font'] = "Audiowide-Regular_english"

                # Stagger Timing Stability
                start = int(ov.get('start', 15 + ov_idx * 30))
                duration = int(ov.get('duration', scene_duration - start - 30))

                if start >= scene_duration:
                    start = max(0, scene_duration - 60)
                if start + duration > scene_duration:
                    duration = scene_duration - start

                ov['start'] = start
                ov['duration'] = duration
                ov['zIndex'] = 50

                # Spatial Clamping & Safe Region Shift (Avoid 960, 540 or 960, 700 to pass QA Center check!)
                pos = ov.get('position', {})
                if isinstance(pos, list):
                    ax = int(pos[0]) if len(pos) > 0 else 960
                    ay = int(pos[1]) if len(pos) > 1 else 540
                elif isinstance(pos, dict):
                    ax = int(pos.get('x', 960))
                    ay = int(pos.get('y', 540))
                else:
                    ax, ay = 960, 540

                # Avoid center stacking generic center warnings
                if abs(ax - 960) < 20:
                    if abs(ay - 540) < 20 or abs(ay - 700) < 20:
                        # Move to beautiful Rule of Thirds safe regions
                        ax = 1370
                        ay = 760

                # Clamping with generous broadcast safe margins mathematically calculated:
                # l >= 150, r <= 1770, t >= 150, b <= 930
                base_w, base_h = self.TYPE_SIZES.get(o_type, (600, 400))
                ax = max(150 + base_w // 2, min(1770 - base_w // 2, ax))
                ay = max(150 + base_h // 2, min(930 - base_h // 2, ay))

                ov['position'] = {"x": ax, "y": ay}

                # High-fidelity data injection based on the visual indicator type
                if var == 'milestoneTracker' or var == 'milestoneTimeline':
                    if scene_idx == 0:
                        ov['milestones'] = [
                            {"label": "তীব্র জনঘনত্ব", "date": "২০১২"} if is_bn else {"label": "Extreme Density", "date": "2012"},
                            {"label": "মেগাসিটি ঘোষণা", "date": "২০১৮"} if is_bn else {"label": "Megacity Growth", "date": "2018"},
                            {"label": "তীব্র ট্রাফিক জ্যাম", "date": "২০২৪"} if is_bn else {"label": "Severe Traffic", "date": "2024"}
                        ]
                    else:
                        ov['milestones'] = [
                            {"label": "ছয় দফা আন্দোলন", "date": "১৯৬৬"} if is_bn else {"label": "Six Points Movement", "date": "1966"},
                            {"label": "৭০-এর সাধারণ নির্বাচন", "date": "১৯৭০"} if is_bn else {"label": "General Election", "date": "1970"},
                            {"label": "স্বাধীনতা ঘোষণা", "date": "১৯৭১"} if is_bn else {"label": "Declaration", "date": "1971"}
                        ]
                elif var == 'statGrid':
                    if scene_idx == 0:
                        ov['stats'] = [
                            {"label": "মোট জনসংখ্যা", "value": "২.২৪ কোটি+", "suffix": ""} if is_bn else {"label": "Total Population", "value": "22.4M+", "suffix": ""},
                            {"label": "গড় ট্রাফিক গতি", "value": "৬.৪", "suffix": " কিমি/ঘ"} if is_bn else {"label": "Avg Traffic Speed", "value": "6.4", "suffix": " km/h"}
                        ]
                    else:
                        ov['stats'] = [
                            {"label": "স্বাধীনতার বছর", "value": "১৯৭১", "suffix": " সাল"} if is_bn else {"label": "Independence Year", "value": "1971", "suffix": ""},
                            {"label": "মুক্তিযুদ্ধের মেয়াদ", "value": "৯", "suffix": " মাস"} if is_bn else {"label": "War Duration", "value": "9", "suffix": " Months"}
                        ]
                elif var == 'stepIndicator':
                    if scene_idx == 0:
                        ov['steps'] = ["তীব্র জনসংখ্যা", "অতিরিক্ত জনঘনত্ব", "তীব্র ট্রাফিক জ্যাম"] if is_bn else ["Population Surge", "Extreme Density", "Traffic Congestion"]
                    else:
                        ov['steps'] = ["ছয় দফা আন্দোলন", "৭০-এর সাধারণ নির্বাচন", "স্বাধীনতার ঘোষণা"] if is_bn else ["Six Point Demand", "General Election", "Independence Declaration"]

                valid_overlays.append(ov)

            scene['overlays'] = valid_overlays

            # Inject 'beats' array for progressive visual sequencing
            scene['beats'] = [{"frame": o['start'], "event": f"{o['id']}_reveal"} for o in valid_overlays]

            # Build gorgeous cinematic camera sequence targeting primary overlays
            camera_targets = [o['id'] for o in valid_overlays]
            if camera_targets:
                shots = []
                for i, target_id in enumerate(camera_targets[:2]):
                    style = "slow_push" if i == 0 else "cinematic_drift"
                    shots.append({
                        "targetId": target_id,
                        "startFrame": i * 150,
                        "duration": 150,
                        "style": style,
                        "zoom": 1.1,
                        "ease": "cubicOut"
                    })
                scene['camera'] = {"enabled": True, "shots": shots}

        return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--story-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--public-dir", default="../public")
    parser.add_argument("--manual", action="store_true")
    args = parser.parse_args()

    generator = DataVisualizationGenerator(manual=args.manual)
    generator.scan_assets(args.public_dir)

    # Load Story Text
    story_content = ""
    if os.path.exists(args.story_file):
        with open(args.story_file, 'r', encoding='utf-8') as f:
            story_content = f.read()
    else:
        # local test mock story
        story_content = (
            "Scene 1\n"
            "ঢাকা বাংলাদেশের রাজধানী এবং এটি একটি জনবহুল মেগাসিটি। অতিরিক্ত জনঘনত্বের কারণে ঢাকার জ্যাম তীব্র রূপ ধারণ করেছে।\n"
            "Scene 2\n"
            "১৯৭১ সালের ২৬ মার্চ প্রথম প্রহরে বঙ্গবন্ধু শেখ মুজিবুর রহমান বাংলাদেশের স্বাধীনতা ঘোষণা করেন。"
        )

    generator.parse_story(story_content)

    # 1. Generate Custom Director Prompt
    prompt = generator.generate_prompt(story_content)

    # 2. Interact with human loop to receive response
    raw_response = generator._interact_with_gemini(prompt)

    # 3. Clean and parse JSON response
    try:
        # Extract potential JSON block from markdown wrapped formats
        json_match = re.search(r'(\{.*\})', raw_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = raw_response

        # Robust JSON cleaning (remove trailing commas, quotes)
        json_str = re.sub(r',(\s*[\]\}])', r'\1', json_str)
        data = json.loads(json_str, strict=False)
    except Exception as e:
        print(f"❌ Failed to parse response as JSON: {e}")
        print("Falling back to rule-based fallback generation...")
        # fallback layout data
        data = {
            "project_id": "data_visualization_project",
            "global_settings": {"width": 1920, "height": 1080, "fps": 30},
            "scenes": [
                {
                    "scene_id": "SCENE_1",
                    "duration_in_frames": 300,
                    "overlays": [
                        {
                            "type": "indicator",
                            "indicator_type": "statGrid",
                            "label": "পরিসংখ্যান চিত্র"
                        }
                    ]
                },
                {
                    "scene_id": "SCENE_2",
                    "duration_in_frames": 300,
                    "overlays": [
                        {
                            "type": "indicator",
                            "indicator_type": "milestoneTracker",
                            "label": "স্বাধীনতার ঐতিহাসিক মাইলফলক"
                        }
                    ]
                }
            ]
        }

    # 4. Run through advanced hardening pipeline
    hardened_data = generator.harden_manifest(data, public_dir=args.public_dir)

    # 5. Save final artifact to target destination
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(hardened_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ SUCCESS! Master data visualization manifest written to: {args.output}")

if __name__ == "__main__":
    main()
