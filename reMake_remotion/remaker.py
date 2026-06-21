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
    def __init__(self, manifest_path: str, public_dir: str, timestamp_file: str = None):
        self.manifest_path = manifest_path
        self.public_dir = os.path.abspath(public_dir)
        self.data = self.load_manifest()
        self.maker = RemotionJsonMaker(headless=True)
        self.maker.scan_assets(self.public_dir)
        if timestamp_file and os.path.exists(timestamp_file):
            print(f"📂 Loading timestamps for audio sync: {timestamp_file}")
            with open(timestamp_file, 'r', encoding='utf-8') as f:
                self.maker.raw_timestamps = f.read()

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

    def get_scene(self, scene_num: int) -> Dict[str, Any]:
        scene_id = f"SCENE_{scene_num:02d}"
        for scene in self.data.get('scenes', []):
            if scene.get('scene_id') == scene_id:
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
                print(f"Bangla: {self.maker.bangla_fonts}")
                print(f"English: {self.maker.english_fonts}")
                new_val = input("New Font Name: ").strip()
                if new_val:
                    for ov in overlays: ov['font'] = new_val

            elif choice == '3':
                new_val = input("New Color Hex (e.g. #00FFAB): ").strip()
                if self.validate_color(new_val):
                    for ov in overlays: ov['color'] = new_val
                else: print("⚠️ Invalid Hex Color")

            elif choice == '4' and text_ov:
                print("Options: neon_flicker, glitch_pop, slideUp, wordByWord, cinematicGlow")
                new_val = input("New Animation: ").strip()
                if new_val: text_ov['animation'] = new_val

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
                new_val = input(f"Current Style: {shot.get('style')}\nNew Style: ").strip()
                if new_val: shot['style'] = new_val

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

        # Get context from original generator (reusing logic)
        self.maker.start_browser()

        refine_prompt = (
            f"YOU ARE A REMOTION MASTER. REFINE THIS SPECIFIC SCENE JSON.\n"
            f"CURRENT JSON: {current_scene_json}\n"
            f"INSTRUCTION: {instruction if instruction else 'Enhance the design and visual impact while keeping the narrative.'}\n"
            f"STRICT RULES:\n"
            f"- Output RAW MINIFIED JSON for THIS SCENE ONLY.\n"
            f"- Follow Studio V4 minimalist guidelines.\n"
            f"- Maintain audio sync for hero words.\n"
        )

        raw_output = self.maker._interact_with_gemini(refine_prompt)
        self.maker.stop_browser()

        # Parse and Update
        try:
            # Simple extraction
            start_idx, end_idx = raw_output.find('{'), raw_output.rfind('}')
            if start_idx != -1 and end_idx != -1:
                new_scene_data = json.loads(raw_output[start_idx:end_idx+1])
                # Merge or replace? User says "redo everything of a particular scene"
                # We'll replace the scene data but ensure ID remains consistent
                new_scene_data['scene_id'] = scene['scene_id']

                # Apply guardrails
                temp_data = {"scenes": [new_scene_data]}
                fixed_data = self.maker.finalize_json_durations(temp_data, self.public_dir)

                # Update main data
                for i, s in enumerate(self.data['scenes']):
                    if s['scene_id'] == scene['scene_id']:
                        self.data['scenes'][i] = fixed_data['scenes'][0]
                        break
                print("✨ Gemini refinement applied.")
            else:
                print("❌ Gemini failed to produce valid JSON.")
        except Exception as e:
            print(f"❌ Error parsing Gemini response: {e}")

    def render_scene(self, scene_num: int):
        scene_id = f"SCENE_{scene_num:02d}"

        # We use the existing render.ts script to ensure environment consistency (fonts, assets, etc.)
        # and to utilize its chunking/resume capabilities if needed.
        output_rel_path = f"remake/updated_scene_{scene_id}.mp4"

        # Ensure remake folder exists relative to Drive output base
        remake_full_dir = "/content/drive/MyDrive/Counterism_Studio_V4/renders/overlays/remotion/remake"
        os.makedirs(remake_full_dir, exist_ok=True)

        print(f"🎬 Triggering render for {scene_id} via render.ts...")

        # cmd: node --loader ts-node/esm render.ts --template=... --scene=SCENE_01 --output=...
        cmd = [
            "node", "--loader", "ts-node/esm", "render.ts",
            f"--template={self.manifest_path}",
            f"--scene={scene_id}",
            f"--output={output_rel_path}"
        ]

        try:
            # Change dir to engine root where render.ts is
            cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            subprocess.run(cmd, check=True, cwd=cwd)
            print(f"✅ Render Complete. Scene saved to remake folder.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Render failed: {e}")

def main():
    # Paths for Colab
    manifest_path = "/content/drive/MyDrive/Counterism_Studio_V4/manifests/remotion_render.json"
    timestamp_path = "/content/drive/MyDrive/Counterism_Studio_V4/manifests/timestamp.txt"
    public_dir = "/content/engine/public"

    remaker = RemotionRemaker(manifest_path, public_dir, timestamp_path)

    while True:
        try:
            line = input("\n👉 Enter scene number to remake (e.g. 1) or 'q' to quit: ").strip()
            if line.lower() == 'q': break
            scene_num = int(line)

            scene = remaker.get_scene(scene_num)
            if not scene:
                print(f"⚠️ Scene {scene_num} not found in manifest.")
                continue

            print("\nOptions:")
            print("1. Change manually")
            print("2. Change through gemini")
            mode = input("Select mode: ").strip()

            if mode == '1':
                remaker.manual_change(scene)
            elif mode == '2':
                remaker.gemini_change(scene_num, scene)
            else:
                print("⚠️ Invalid option")
                continue

            # Finalize and Save
            remaker.data = remaker.maker.finalize_json_durations(remaker.data, public_dir)
            remaker.save_manifest()

            # Render
            remaker.render_scene(scene_num)

            cont = input("\nRemake another scene? (y/n): ").lower()
            if cont != 'y': break

        except ValueError:
            print("⚠️ Please enter a valid number.")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
