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
                # Split by दृश्य (Scene) markers
                parts = re.split(r' দৃশ্য\s+[0-9০-৯]+', content)
                for i, text in enumerate(parts[1:], 1):
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
        if isinstance(data, list):
             # Check if it's a list of dicts with common overlay keys
             if len(data) > 0 and isinstance(data[0], dict) and any(k in data[0] for k in ['type', 'id', 'content', 'kind']):
                 return data
             # Recurse into list items
             for item in data:
                 res = self.find_overlays(item)
                 if res: return res
        elif isinstance(data, dict):
             # Check common list keys
             for k in ['overlays', 'elements', 'layers', 'objects', 'visuals', 'components', 'overlay_list']:
                 if k in data and isinstance(data[k], list):
                     return data[k]
             # Check if the dict ITSELF is an overlay (has 'type' but no scenes/overlays list)
             if 'type' in data and not any(k in data for k in ['scenes', 'overlays', 'elements']):
                 return [data]
             # Recurse into values
             for v in data.values():
                 res = self.find_overlays(v)
                 if res: return res
        return []

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
        current_scene_json = json.dumps(scene, ensure_ascii=False)
        scene_id = scene.get('scene_id', 'UNKNOWN')
        story_text = self.story_scenes.get(scene_id, "No narration context available.")

        # Get context from original generator (reusing logic)
        self.maker.start_browser()

        refine_prompt = (
            f"YOU ARE A REMOTION MASTER. REFINE THIS SPECIFIC SCENE JSON.\n"
            f"SCENE ID: {scene_id}\n"
            f"NARRATION: {story_text}\n"
            f"CURRENT JSON: {current_scene_json}\n"
            f"INSTRUCTION: {instruction if instruction else 'Enhance the design and visual impact while keeping the narrative.'}\n"
            f"STRICT RULES:\n"
            f"- Output RAW MINIFIED JSON for THIS SCENE ONLY.\n"
            f"- Follow Studio V4 minimalist guidelines.\n"
            f"- Maintain audio sync for hero words.\n"
        )

        raw_output = self.maker._interact_with_gemini(refine_prompt)
        self.maker.stop_browser()
        print(f"📊 Raw response sample: {raw_output[:200]}...")

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
                # Locate overlays list using deep search
                overlays = self.find_overlays(extracted_data)

                if overlays:
                    print(f"✅ Successfully recovered {len(overlays)} overlays from AI response.")
                    # We update the scene's overlays but keep its other metadata (duration, etc)
                    scene['overlays'] = overlays

                    # Apply guardrails to the full scene context
                    temp_data = {"scenes": [scene]}
                    fixed_data = self.maker.finalize_json_durations(temp_data, self.public_dir)

                    # Update main data
                    for i, s in enumerate(self.data['scenes']):
                        if s['scene_id'] == scene['scene_id']:
                            self.data['scenes'][i] = fixed_data['scenes'][0]
                            break
                    print("✨ Gemini refinement applied and validated.")
                else:
                    print("❌ Could not find valid overlays list in Gemini response.")
            else:
                print("❌ Gemini failed to produce valid JSON.")
        except Exception as e:
            print(f"❌ Error processing Gemini response: {e}")

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
