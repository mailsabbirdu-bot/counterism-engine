import os
import json
import sys
import re
import shutil
import subprocess
from typing import Dict, Any, List

# Add parent directory to path so we can import from remotion_jsonMaker
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from remotion_jsonMaker.generator import RemotionJsonMaker
except ImportError:
    # Fallback if structure is different in Colab
    sys.path.append('/content/engine')
    from remotion_jsonMaker.generator import RemotionJsonMaker

class RemotionRemaker:
    def __init__(self, manifest_path: str, public_dir: str, timestamp_file: str = None, story_path: str = None):
        self.manifest_path = manifest_path
        self.public_dir = os.path.abspath(public_dir)
        self.story_path = story_path
        self.story_scenes = {}
        self.data = self.load_manifest()
        self.maker = RemotionJsonMaker(headless=True)
        self.maker.scan_assets(self.public_dir)
        if timestamp_file and os.path.exists(timestamp_file):
            print(f"📂 Loading timestamps for audio sync: {timestamp_file}")
            with open(timestamp_file, 'r', encoding='utf-8') as f:
                self.maker.raw_timestamps = f.read()

        self.load_story()

    def load_story(self):
        if not self.story_path or not os.path.exists(self.story_path):
            return
        try:
            with open(self.story_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Split by দৃশ্য (Scene) markers, handling cases where it starts at the beginning
                # Regex looks for "দৃশ্য" followed by space and numbers
                pattern = r'দৃশ্য\s+[0-9০-৯]+'
                parts = re.split(pattern, content)
                # If the first part is empty, it means the file started with a scene marker
                if parts and not parts[0].strip():
                    parts = parts[1:]

                for i, text in enumerate(parts, 1):
                    self.story_scenes[f"SCENE_{i:02d}"] = text.strip()
            print(f"📖 Loaded {len(self.story_scenes)} scenes from story.")
        except Exception as e:
            print(f"⚠️ Error loading story: {e}")

    def load_manifest(self) -> Dict[str, Any]:
        if not os.path.exists(self.manifest_path):
            print(f"❌ Error: Manifest not found at {self.manifest_path}")
            return {}
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_manifest(self):
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        # Redundant save to /content/ for safety
        try: shutil.copy(self.manifest_path, "/content/remotion_render.json")
        except: pass

    def get_scene(self, scene_num_or_id: Any) -> Dict[str, Any]:
        # Handle numeric input (e.g. 1 -> SCENE_01)
        if isinstance(scene_num_or_id, int) or (isinstance(scene_num_or_id, str) and scene_num_or_id.isdigit()):
            scene_id = f"SCENE_{int(scene_num_or_id):02d}"
        else:
            scene_id = str(scene_num_or_id).upper()

        for scene in self.data.get('scenes', []):
            cur_id = scene.get('scene_id', '').upper()
            if cur_id == scene_id or cur_id.startswith(f"{scene_id}_"):
                return scene
        return None

    def validate_color(self, color: str) -> bool:
        return bool(re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color))

    def manual_change(self, scene: Dict[str, Any]):
        while True:
            print(f"\n🛠️  Modifying {scene['scene_id']}")
            print("1. Text Content")
            print("2. Font")
            print("3. Primary Color")
            print("4. Overlay Animation")
            print("5. Position (X, Y)")
            print("6. Hero Word Config")
            print("7. Camera Style")
            print("8. Camera Zoom")
            print("9. KPI/Indicator Values")
            print("10. Background Video Path")
            print("0. Done with this scene")

            choice = input("\nEnter serial number to change: ").strip()

            if choice == '0': break

            overlays = scene.get('overlays', [])
            text_ov = next((o for o in overlays if o.get('type') == 'text'), None)
            focal_ov = next((o for o in overlays if o.get('type') != 'text'), None)

            if choice == '1' and text_ov:
                new_val = input(f"Current: {text_ov.get('content')}\nNew Content: ").strip()
                if new_val: text_ov['content'] = new_val

            elif choice == '2':
                all_fonts = self.maker.bangla_fonts + self.maker.english_fonts
                print(f"Detected Fonts: {all_fonts}")
                new_val = input("New Font Name: ").strip()
                if new_val in all_fonts:
                    for ov in overlays: ov['font'] = new_val
                    print(f"✅ Font set to {new_val}")
                else:
                    print(f"⚠️ Warning: '{new_val}' not found in detected assets. Applying anyway...")
                    for ov in overlays: ov['font'] = new_val

            elif choice == '3':
                new_val = input("New Color Hex (e.g. #00FFAB): ").strip()
                if self.validate_color(new_val):
                    for ov in overlays: ov['color'] = new_val
                    print(f"✅ Color set to {new_val}")
                else: print("❌ Invalid Hex Color. Use format #RRGGBB")

            elif choice == '4' and text_ov:
                anims = ["neon_flicker", "glitch_pop", "slideUp", "wordByWord", "cinematicGlow"]
                print(f"Supported: {anims}")
                new_val = input("New Animation: ").strip()
                if new_val in anims:
                    text_ov['animation'] = new_val
                    print(f"✅ Animation set to {new_val}")
                else: print(f"❌ Unsupported animation. Choose from: {anims}")

            elif choice == '5':
                try:
                    x = int(input("New X (0-1920): "))
                    y = int(input("New Y (0-1080): "))
                    for ov in overlays:
                        ov['position'] = {"x": x, "y": y}
                except ValueError: print("⚠️ Invalid numbers")

            elif choice == '6' and text_ov:
                h = text_ov.get('hero_config', {})
                print(f"Current: {h}")
                word = input(f"Hero Word (Current: {h.get('word')}): ").strip() or h.get('word')
                color = input(f"Hero Color (Current: {h.get('color')}): ").strip() or h.get('color')
                anim = input(f"Hero Anim (Current: {h.get('animation')}): ").strip() or h.get('animation')
                start = input(f"Hero Start Frame (Current: {h.get('start')}): ").strip() or h.get('start')
                text_ov['hero_config'] = {
                    "word": word, "color": color, "animation": anim, "start": int(start)
                }

            elif choice == '7' and scene.get('camera', {}).get('shots'):
                shot = scene['camera']['shots'][0]
                styles = [
                    "slow_push", "slow_pull", "push_in", "pull_out", "whip_pan", "dramatic_reveal",
                    "cinematic_drift", "dynamic_orbit", "vertical_sweep", "spiral_vortex", "glitch_snap",
                    "low_angle_hero", "side_strafe_left", "side_strafe_right", "aerial_top_down",
                    "shaky_handheld", "zoom_blur_reveal", "tilt_shift_focus", "power_zoom", "smooth_glide"
                ]
                print(f"Common Styles: {styles[:10]}...")
                new_val = input(f"Current Style: {shot.get('style')}\nNew Style: ").strip()
                if new_val in styles or new_val:
                    shot['style'] = new_val
                    print(f"✅ Camera Style set to {new_val}")

            elif choice == '8' and scene.get('camera', {}).get('shots'):
                shot = scene['camera']['shots'][0]
                try:
                    new_val = float(input(f"Current Zoom: {shot.get('zoom')}\nNew Zoom: "))
                    shot['zoom'] = new_val
                except ValueError: print("⚠️ Invalid number")

            elif choice == '9' and focal_ov:
                print(f"Current: {focal_ov}")
                label = input(f"Label: ").strip() or focal_ov.get('label')
                val = input(f"Value: ").strip() or focal_ov.get('value')
                focal_ov['label'] = label
                focal_ov['value'] = int(val) if str(val).isdigit() else val

            elif choice == '10':
                new_val = input(f"Current: {scene.get('video_path')}\nNew Path: ").strip()
                if new_val: scene['video_path'] = new_val

            confirm = input("\nChange anything else? (y/n): ").lower()
            if confirm != 'y': break

    def find_overlays(self, data: Any) -> List[dict]:
        """Deep search for an overlay list in potentially nested/wrapped Gemini responses."""
        VALID_TYPES = ['text', 'chart', 'data_indicator', 'ui_panel', 'indicator', 'kpi', 'media']
        CAMERA_KEYS = ['targetId', 'style', 'shots', 'motionBlur']

        if isinstance(data, list):
             # Check if it's a list of dicts with common overlay keys
             if len(data) > 0 and isinstance(data[0], dict):
                 first = data[0]
                 # Ensure it's not a camera shot list
                 if any(k in first for k in CAMERA_KEYS) and not any(k in first for k in ['content', 'data']):
                     pass
                 else:
                     if any(k in first for k in ['content', 'kind', 'indicator_type', 'chart_type']):
                         return data
                     if first.get('type') in VALID_TYPES:
                         return data

             # Recurse into list items
             for item in data:
                 res = self.find_overlays(item)
                 if res: return res
        elif isinstance(data, dict):
             # Ensure the dict itself isn't a camera object
             if any(k in data for k in CAMERA_KEYS) and not any(k in data for k in ['content', 'data', 'overlays']):
                 pass
             else:
                 # Check common list keys
                 for k in ['overlays', 'elements', 'layers', 'objects', 'visuals', 'components', 'overlay_list', 'timeline']:
                     if k in data and isinstance(data[k], list):
                         found = self.find_overlays(data[k])
                         if found: return found

                 # Check if the dict ITSELF is an overlay
                 if data.get('type') in VALID_TYPES:
                     return [data]
                 if any(k in data for k in ['content', 'indicator_type', 'chart_type']):
                     # Final check: it must have a type or we must infer it
                     return [data]

             # Recurse into values
             for v in data.values():
                 if isinstance(v, (dict, list)):
                     res = self.find_overlays(v)
                     if res: return res
        return []

    def _is_bangla(self, text: str) -> bool:
        return any('\u0980' <= c <= '\u09FF' for c in text)

    def validate_gemini_output(self, extracted_data: Any, story_text: str, target_lang: str) -> List[str]:
        errors = []

        # 1. Basic Structure
        overlays = self.find_overlays(extracted_data)
        if not overlays:
            errors.append("CRITICAL: No overlays found in AI response.")
            return errors

        # 2. Language Integrity
        if target_lang == "BANGLA":
            has_bangla = False
            for ov in overlays:
                for key in ['content', 'title', 'label']:
                    val = str(ov.get(key, ""))
                    if val and self._is_bangla(val) and "Insight" not in val and "REMOTION" not in val:
                        has_bangla = True
                        break
                if has_bangla: break

            if not has_bangla:
                errors.append("LANGUAGE ERROR: Target is BANGLA but no Bangla script was found in 'content', 'title', or 'label' fields. DO NOT USE ENGLISH.")

        # 3. Narrative Match
        # Expanded stop words for better filtering
        STOP_WORDS = ["এই", "একটি", "হলো", "হচ্ছে", "আর", "কিন্তু", "এবং", "বা", "তবে", "যদি", "যে", "সে", "তারা", "ছিল", "হবে", "করে", "করা", "জন্য", "থেকে", "সাথে", "দ্বারা", "মাধ্যমে", "এক", "দুই", "তিন", "চার", "পাচ", "ছয়", "সাত", "আট", "নয়", "দশ", "কোটি", "লক্ষ", "কোটিরও", "বেশি", "কম", "অনেক", "অল্প", "হলে", "যায়", "গিয়ে", "নিয়ে", "হয়ে", "থাকা", "রাখা", "বলছে", "বলেন", "শুরু", "শেষ", "এখন", "তখন", "যখন", "পর্যন্ত", "প্রতিটি", "প্রতি", "সব", "সবাই", "কেউ", "কেউই", "কিছু", "কোন", "কোনো", "মতো", "মত", "মতোই", "মতই", "নিজেই", "নিজে", "বড়", "ছোট"]

        # Extract meaningful keywords from story_text (Bengali words or English words > 3 chars)
        story_words = re.findall(r'[\u0980-\u09FF]+|[a-zA-Z]{4,}', story_text)
        meaningful_story_words = [w for w in story_words if w not in STOP_WORDS]

        if meaningful_story_words:
            found_match = False
            visual_text = ""
            for ov in overlays:
                for key in ['content', 'title', 'label']:
                    if ov.get(key): visual_text += " " + str(ov[key])

            # Check for matches
            matched_words = [w for w in meaningful_story_words if w in visual_text]
            if len(matched_words) > 0:
                found_match = True

            if not found_match:
                # Provide hints for narrative alignment
                hints = ", ".join(meaningful_story_words[:5])
                errors.append(f"NARRATIVE MISMATCH: Visual content must contain keywords from the narration. PLEASE USE THESE WORDS: {hints}")

        return errors

    def gemini_change(self, scene_num: int, scene: Dict[str, Any]):
        print("\n🤖 Gemini Refinement Mode")
        print("1. Change entire scene (AI logic)")
        print("2. Specific instruction (e.g. 'Make it more aggressive', 'Use a bar chart')")
        print("3. Specified attribute change (e.g. 'Change the color to neon green')")
        choice = input("Choice: ").strip()

        instruction = ""
        if choice == '2' or choice == '3':
            instruction = input("Enter your specific instruction for Gemini: ").strip()

        # Build a refinement prompt
        scene_id = scene.get('scene_id', 'UNKNOWN')

        # Improved Scene ID matching to handle suffixes (e.g., SCENE_01_INTRO -> SCENE_01)
        base_match = re.search(r'SCENE_(\d+)', scene_id)
        base_id = base_match.group(0) if base_match else scene_id
        story_text = self.story_scenes.get(base_id, "No narration context available.")
        lang = "BANGLA" if self._is_bangla(story_text) else "ENGLISH"

        # Simplify JSON to avoid confusing Gemini with internal engine props
        clean_scene = {
            "scene_id": scene.get("scene_id"),
            "overlays": scene.get("overlays", []),
            "camera": scene.get("camera", {})
        }
        current_scene_json = json.dumps(clean_scene, ensure_ascii=False)

        # FILTER FONTS TO REDUCE CONFUSION
        target_fonts = self.maker.bangla_fonts if lang == "BANGLA" else self.maker.english_fonts

        # Get context from original generator (reusing logic)
        self.maker.start_browser()

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

        feedback_context = ""
        for attempt in range(3):
            print(f"\n🔄 Gemini Interaction Attempt {attempt + 1}/3...")

            refine_prompt = (
                f"YOU ARE A REMOTION MASTER. REFINE THIS SPECIFIC SCENE JSON.\n"
                f"SCENE ID: {scene_id}\n"
                f"TARGET LANGUAGE: {lang}\n"
                f"NARRATION AUTHORITY: THE NARRATION BELOW IS THE ONLY SOURCE FOR CONTENT. IGNORE ENGLISH PLACEHOLDERS IN CURRENT JSON.\n"
                f"NARRATION: {story_text}\n"
                f"CURRENT JSON: {current_scene_json}\n"
                f"AVAILABLE {lang} FONTS: {target_fonts}\n"
                f"AVAILABLE HERO ANIMATIONS: {', '.join(hero_anim_list)}\n"
                f"AVAILABLE CAMERA STYLES: {', '.join(camera_style_list)}\n"
                f"INSTRUCTION: {instruction if instruction else 'Enhance the design and visual impact while strictly following the narrative.'}\n"
                f"VISUAL LIBRARY (CHOOSE SLEEK/ULTRA-MODERN PRESETS):\n"
                f"- 'chart_type' (for 'chart'): line, area, forecast, bar, horizontalBar, verticalBar, groupedBar, stackedBar, pie, donut, bump, areaBump, heatmap, radar, radialBar, stream, swarmplot, waffle, funnel, marimekko, circlePacking, calendar, parallelCoordinates, treemap, sunburst, scatter, network, chord, violinPlot.\n"
                f"- 'indicator_type' (for 'data_indicator'): kpiNumber, percentageCounter, comparisonKPI, deltaIndicator, countdown, progressBar, circularProgress, semiGauge, milestoneTracker, dashboardCard, statGrid, techMetric, dataWave, scoreCard, batteryLevel, pulseRadar, multiProgress, speedometer, ringChart, statusBadge, metricRing, floatingTag, stepIndicator, eventTimeline, milestoneTimeline.\n"
                f"- SHADCN LIBRARY (type: 'shadcn_chart' | 'shadcn_indicator'):\n"
                f"  - 'chart_type' (shadcn_chart): glass_area, neon_bar, stacked_line, radial_score, radar_web, composed_tech, pie_donut_glass, scatter_bubble, horizontal_pill_bar, step_area, multi_bar_stack, curved_edge_line, double_radar.\n"
                f"  - 'indicator_type' (shadcn_indicator): metric_tile, tech_badge, activity_ring, crypto_card, server_status, user_profile_stat, weather_glass, storage_pill, upload_cloud, score_board, notification_stack, data_ticker, network_ping, step_indicator_glass.\n"
                f"FEEDBACK FROM PREVIOUS ATTEMPT: {feedback_context if feedback_context else 'None'}\n"
                f"STRICT RULES (STRICT MODE ON):\n"
                f"- OUTPUT A SINGLE JSON OBJECT FOR THIS SCENE ONLY.\n"
                f"- STRICT LANGUAGE RULE: All 'content', 'title', and 'label' fields MUST BE IN {lang}. Do NOT use English if narration is Bangla.\n"
                f"- DO NOT TRANSLATE BANGLA NARRATION TO ENGLISH TEXT. KEEP IT BANGLA.\n"
                f"- MANDATORY KEYS: 'overlays' (List), 'camera' (Object).\n"
                f"- DO NOT USE WRAPPER KEYS like 'sceneId', 'meta', or 'timeline'.\n"
                f"- EVERY TEXT/NIVO LAYER MUST HAVE A VALID 'content' OR 'data' FIELD BASED ON THE NARRATION.\n"
                f"- CONTENT MUST BE MEANINGFUL AND DERIVED FROM THE NARRATION. NO PLACEHOLDERS LIKE 'INSIGHT'.\n"
                f"- DATA INTEGRITY: Ensure 'chart' has 'data' array/object and 'title'. Ensure 'indicator' has 'label' and 'value'.\n"
                f"- YOU MUST UPDATE 'overlays' (animations, content, colors) AND 'camera' (presets, shots) BASED ON THE NARRATION.\n"
                f"- Follow Studio V4 minimalist guidelines.\n"
                f"- USE {lang} appropriate fonts from the provided list. NEVER use English fonts for Bangla text.\n"
                f"- EXAMPLE: If Narration is 'ঢাকা।', content must be 'ঢাকা', font must be a Bangla font.\n"
                f"- Maintain audio sync for hero words.\n"
            )

            print("\n📝 --- FULL PROMPT SENT TO GEMINI ---")
            print(refine_prompt)
            print("-" * 50)

            raw_output = self.maker._interact_with_gemini(refine_prompt)

            print("\n📊 --- RAW GEMINI OUTPUT ---")
            print(raw_output)
            print("-" * 50)

            # Robust JSON extraction and repair
            extracted_data = None
            try:
                # Try both { and [ as start characters for single scene responses
                start_idx = min(i for i in [raw_output.find('{'), raw_output.find('[')] if i != -1) if '{' in raw_output or '[' in raw_output else -1
                end_idx = max(i for i in [raw_output.rfind('}'), raw_output.rfind(']')] if i != -1) if '}' in raw_output or ']' in raw_output else -1

                if start_idx != -1 and end_idx != -1:
                    json_str = raw_output[start_idx:end_idx+1]
                    json_str = "".join(ch for ch in json_str if ch.isprintable() or ch in "\n\r\t")
                    json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)

                    try:
                        extracted_data = json.loads(json_str, strict=False)
                    except:
                        print("⚠️  Primary parse failed. Attempting repair...")
                        extracted_data = self.maker.repair_json(json_str)

                if extracted_data:
                    # Guardrail Validation
                    validation_errors = self.validate_gemini_output(extracted_data, story_text, lang)
                    if validation_errors:
                        print(f"⚠️ Guardrail Attempt {attempt+1} FAILED: {', '.join(validation_errors)}")
                        feedback_context = "CRITICAL ERRORS FOUND: " + ". ".join(validation_errors) + ". PLEASE RE-READ THE NARRATION AND UPDATE CONTENT."
                        continue # Retry

                    print(f"✅ Guardrail Attempt {attempt+1} PASSED: Output matches language and narration.")
                    print(f"🔍 DEBUG: Extracted JSON keys: {list(extracted_data.keys()) if isinstance(extracted_data, dict) else 'Not a dict'}")

                    # Update entire scene if the response is a full scene object
                    if isinstance(extracted_data, dict) and ('overlays' in extracted_data or 'camera' in extracted_data):
                        print("✅ AI returned a full scene object. Merging camera and overlays.")
                        if 'overlays' in extracted_data: scene['overlays'] = extracted_data['overlays']
                        if 'camera' in extracted_data: scene['camera'] = extracted_data['camera']
                    else:
                        # Locate overlays list using deep search
                        overlays = self.find_overlays(extracted_data)
                        if overlays:
                            print(f"✅ Successfully recovered {len(overlays)} overlays from AI response.")
                            scene['overlays'] = overlays

                        # Also try to find camera in the nested response
                        if isinstance(extracted_data, dict):
                             for k in ['camera', 'camera_settings', 'motion']:
                                 if k in extracted_data:
                                     print(f"✅ Recovered camera settings from key '{k}'")
                                     scene['camera'] = extracted_data[k]
                                     break

                    # Apply guardrails to the full scene context
                    temp_data = {"scenes": [scene]}
                    fixed_data = self.maker.finalize_json_durations(temp_data, self.public_dir)

                    # Update main data
                    for i, s in enumerate(self.data['scenes']):
                        if s['scene_id'] == scene['scene_id']:
                            self.data['scenes'][i] = fixed_data['scenes'][0]
                            final_ov_count = len(fixed_data['scenes'][0].get('overlays', []))
                            print(f"🛠️  Scene {scene['scene_id']} updated with {final_ov_count} overlays.")
                            if final_ov_count > 0:
                                print(f"   Visual Content: {fixed_data['scenes'][0]['overlays'][0].get('content') or fixed_data['scenes'][0]['overlays'][0].get('title')}")
                            break
                    print("✨ Gemini refinement applied and validated.")
                    break # Success!
                else:
                    print(f"❌ Gemini Attempt {attempt+1} failed to produce valid JSON.")
                    feedback_context = "Your previous output was not a valid JSON object. Ensure you output ONLY the raw JSON block."
            except Exception as e:
                print(f"❌ Error processing Gemini response (Attempt {attempt+1}): {e}")
                feedback_context = f"Internal error processing your response: {str(e)}"

        if feedback_context and attempt == 2:
            print("\n❌ ALL GEMINI ATTEMPTS FAILED. Keeping original scene content to prevent corruption.")
            print(f"   Final Error: {feedback_context}")
        else:
            print(f"\n📊 --- FINAL MANIFEST SYNC CHECK (SCENE: {scene_id}) ---")
            print(f"   Target Language: {lang}")
            print(f"   Narration: {story_text}")
            ovs = scene.get('overlays', [])
            print(f"   Visual Content ({len(ovs)} Overlays):")
            for ov in ovs:
                content = ov.get('content') or ov.get('title') or ov.get('label') or "EMPTY"
                print(f"     - [{ov.get('type', '???')}] Content: \"{content}\" | Font: {ov.get('font')}")
            print("-" * 50)

        self.maker.stop_browser()

    def render_scene(self, scene_input: Any):
        scene = self.get_scene(scene_input)
        if not scene:
            print(f"⚠️ Could not find scene for input: {scene_input}")
            return
        scene_id = scene.get('scene_id')

        # Standalone architecture: Create a dedicated JSON for just this scene
        standalone_path = "/content/remake_scene.json"

        # Robust context extraction
        global_settings = self.data.get("global_settings", {"width": 1920, "height": 1080, "fps": 30})

        # IMPORTANT: If Gemini changed overlays but they are still inside 'elements' or other keys,
        # we need to ensure finalize_json_durations has a chance to fix them in the standalone manifest.
        standalone_manifest = {
            "project_name": f"Remake_{scene_id}",
            "global_settings": global_settings,
            "scenes": [scene],
            "audio_sfx_manifest": [s for s in self.data.get("audio_sfx_manifest", []) if s.get("scene_id") == scene_id]
        }

        # Double-check guardrails on standalone manifest to ensure schema compliance (handles recovered keys)
        standalone_manifest = self.maker.finalize_json_durations(standalone_manifest, self.public_dir)
        scene = standalone_manifest['scenes'][0] # Refresh scene ref after guardrails

        with open(standalone_path, 'w', encoding='utf-8') as f:
            json.dump(standalone_manifest, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Standalone Manifest Created at {standalone_path}")
        print(f"   Scene: {scene_id}")
        print(f"   Background: {scene.get('video_path')}")
        print(f"   Overlays: {len(scene.get('overlays', []))}")
        for ov in scene.get('overlays', []):
            pos = ov.get('position', {})
            print(f"     - {ov.get('id')} ({ov.get('type')}) at ({pos.get('x')}, {pos.get('y')}) | Font: {ov.get('font')} | Start: {ov.get('start')}")

        if not scene.get('overlays'):
            print("   ⚠️ WARNING: No overlays detected in this scene manifest!")

        # We use the existing render.ts script to ensure environment consistency
        output_rel_path = f"remake/updated_scene_{scene_id}.mp4"

        # Ensure remake folder exists relative to Drive output base
        remake_full_dir = "/content/drive/MyDrive/Counterism_Studio_V4/renders/overlays/remotion/remake"
        os.makedirs(remake_full_dir, exist_ok=True)

        print(f"🎬 Triggering standalone render for {scene_id} via render.ts...")

        # cmd: node --loader ts-node/esm render.ts --template=... --scene=SCENE_01 --output=...
        cmd = [
            "node", "--loader", "ts-node/esm", "render.ts",
            f"--template={standalone_path}",
            f"--scene={scene_id}",
            f"--output={output_rel_path}",
            "--no-resume"
        ]

        try:
            # Change dir to engine root where render.ts is
            cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            subprocess.run(cmd, check=True, cwd=cwd)
            print(f"✅ Standalone Render Complete. Scene saved to remake folder.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Render failed: {e}")

def main():
    # Paths for Colab
    manifest_path = "/content/drive/MyDrive/Counterism_Studio_V4/manifests/remotion_render.json"
    timestamp_path = "/content/drive/MyDrive/Counterism_Studio_V4/manifests/timestamp.txt"
    story_path = "/content/drive/MyDrive/Counterism_Studio_V4/audio/story.txt"
    public_dir = "/content/engine/public"

    remaker = RemotionRemaker(manifest_path, public_dir, timestamp_path, story_path)

    while True:
        try:
            line = input("\n👉 Enter scene number or ID to remake (e.g. 1, SCENE_01_INTRO) or 'q' to quit: ").strip()
            if line.lower() == 'q': break

            scene = remaker.get_scene(line)
            if not scene:
                print(f"⚠️ Scene '{line}' not found in manifest.")
                continue

            print(f"\nOptions for {scene.get('scene_id')}:")
            print("1. Change manually")
            print("2. Change through gemini")
            print("3. Just Render (no changes)")
            mode = input("Select mode: ").strip()

            if mode == '1':
                remaker.manual_change(scene)
            elif mode == '2':
                # Convert input to int if possible for legacy method compatibility, else use string
                scene_ref = int(line) if line.isdigit() else line
                remaker.gemini_change(scene_ref, scene)
            elif mode == '3':
                pass
            else:
                print("⚠️ Invalid option")
                continue

            # Finalize and Save
            remaker.data = remaker.maker.finalize_json_durations(remaker.data, public_dir)
            remaker.save_manifest()

            # Render
            remaker.render_scene(line)

            cont = input("\nRemake another scene? (y/n): ").lower()
            if cont != 'y': break

        except ValueError:
            print("⚠️ Please enter a valid number.")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
