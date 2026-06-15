import os
import json
import argparse
import re
import time
import subprocess
from playwright.sync_api import sync_playwright
import playwright_stealth

class AudioManifestGenerator:
    def __init__(self, user_data_dir=None, headless=True):
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

    def start_browser(self):
        if self.page: return
        self.playwright = sync_playwright().start()
        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage"
        ]
        if self.user_data_dir:
            self.context = self.playwright.chromium.launch_persistent_context(self.user_data_dir, headless=self.headless, args=args)
        else:
            self.browser = self.playwright.chromium.launch(headless=self.headless, args=args)
            self.context = self.browser.new_context()
        self.page = self.context.new_page()
        playwright_stealth.Stealth().apply_stealth_sync(self.page)
        print("🌐 Navigating to Gemini for Audio Orchestration...")
        self.page.goto("https://gemini.google.com/app", wait_until="networkidle", timeout=60000)

    def stop_browser(self):
        if self.context: self.context.close()
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()
        self.page = None

    def _interact_with_gemini(self, prompt: str) -> str:
        self.start_browser()
        page = self.page
        try:
            input_selector = "div[contenteditable='true']"
            page.wait_for_selector(input_selector, timeout=45000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            print("⌨️  Sending Audio Orchestration prompt...")
            page.click(input_selector)
            page.fill(input_selector, prompt)
            time.sleep(1)
            page.keyboard.press("Enter")

            print("⏳  Waiting for Gemini to finalize SFX plan...")
            response_selectors = ["message-content", ".markdown.message-content", ".model-response-text"]
            last_text = ""
            stable_count = 0

            for i in range(100):
                time.sleep(2)
                current_text = ""
                found_msg = False
                for sel in response_selectors:
                    msgs = page.query_selector_all(sel)
                    if msgs:
                        current_text = msgs[-1].inner_text()
                        found_msg = True
                        break

                if found_msg and len(current_text) > 0:
                    if current_text == last_text:
                        stable_count += 1
                        if stable_count >= 4:
                            print(f"✅  SFX plan received.")
                            return current_text
                    else:
                        stable_count = 0
                        last_text = current_text
            return last_text
        except Exception as e:
            return f"Error: {e}"

    def generate_sfx_plan(self, manifest_json):
        # Extract essential info from manifest for the designer
        simplified_manifest = []
        for scene in manifest_json.get('scenes', []):
            scene_info = {
                "scene_id": scene['scene_id'],
                "duration_in_frames": scene['duration_in_frames'],
                "overlays": []
            }
            for ov in scene.get('overlays', []):
                scene_info['overlays'].append({
                    "id": ov['id'],
                    "type": ov['type'],
                    "start": ov['start'],
                    "duration": ov['duration'],
                    "animation": ov.get('animation')
                })
            simplified_manifest.append(scene_info)

        prompt = (
            f"You are a Professional Cinematic Sound Designer. Below is a Remotion Video Manifest JSON structure.\n\n"
            f"MANIFEST:\n{json.dumps(simplified_manifest, indent=2)}\n\n"
            "TASK:\n"
            "Identify EVERY visual entrance and exit in the manifest and assign a high-quality sound effect (SFX).\n\n"
            "RULES:\n"
            "1. PRIORITY: Sound effects MUST be precisely synced with the 'start' and 'duration' of the overlays.\n"
            "2. TYPE-SPECIFIC SOUNDS:\n"
            "   - 'text' with 'slideUp' or 'cinematicGlow' -> Needs a 'cinematic transition whoosh' or 'ethereal swell'.\n"
            "   - 'chart' or 'data_indicator' -> Needs 'digital computer typing', 'high-tech UI glitch', or 'data processing' sounds.\n"
            "   - Camera movements/transitions -> Needs 'deep cinematic bass drop' or 'riser'.\n"
            "3. UNIQUE SELECTION: Do not repeat the same sound too often. Use variants.\n\n"
            "RETURN ONLY A RAW JSON LIST OF SFX OBJECTS:\n"
            '[ { "scene_id": "SCENE_01", "start_frame": 10, "end_frame": 40, "query": "high tech digital glitch sound effect no copyright", "volume": 0.4, "label": "data_reveal" }, ... ]'
        )

        raw_output = self._interact_with_gemini(prompt)
        json_match = re.search(r'\[.*\]', raw_output, re.DOTALL)
        if json_match:
            try:
                # Clean possible trailing commas or markdown
                cleaned = json_match.group(0)
                cleaned = re.sub(r',\s*}', '}', cleaned)
                cleaned = re.sub(r',\s*\]', ']', cleaned)
                return json.loads(cleaned)
            except:
                pass
        return []

    def download_sfx(self, sfx_plan, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        timestamp_entries = []

        print(f"📥 Processing {len(sfx_plan)} SFX downloads via yt-dlp...")
        for i, item in enumerate(sfx_plan):
            clean_label = re.sub(r'[^a-z0-9]', '_', item.get('label', 'sfx').lower())
            filename = f"sfx_{item['scene_id']}_{i:02d}_{clean_label}.mp3"
            filepath = os.path.join(output_dir, filename)

            print(f"🔍 Searching: {item['query']}")
            cmd = [
                "yt-dlp", "--extract-audio", "--audio-format", "mp3",
                "--output", filepath, f"ytsearch1:{item['query']}"
            ]

            try:
                subprocess.run(cmd, check=True, timeout=120)
                print(f"✅ Saved to {filename}")
                timestamp_entries.append({
                    "scene_id": item['scene_id'],
                    "file": filename,
                    "start": item['start_frame'],
                    "end": item['end_frame'],
                    "volume": item['volume']
                })
            except Exception as e:
                print(f"❌ Failed download: {e}")

        return timestamp_entries

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-file", required=True, help="Path to remotion_render.json")
    parser.add_argument("--output-dir", required=True, help="Folder to download SFX into")
    parser.add_argument("--user-data-dir")
    args = parser.parse_args()

    if not os.path.exists(args.manifest_file):
        print(f"❌ Manifest not found: {args.manifest_file}")
        return

    with open(args.manifest_file, 'r', encoding='utf-8') as f:
        manifest_json = json.load(f)

    generator = AudioManifestGenerator(user_data_dir=args.user_data_dir)
    try:
        sfx_plan = generator.generate_sfx_plan(manifest_json)
        timestamp_audio_data = generator.download_sfx(sfx_plan, args.output_dir)

        manifest_path = os.path.join(args.output_dir, "timestamp_audio.txt")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(timestamp_audio_data, indent=2))
        print(f"🎉 Final audio manifest created at {manifest_path}")

        # Post-process: Update manifest with audio data for injection
        manifest_json['audio_sfx_manifest'] = timestamp_audio_data
        with open(args.manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest_json, f, indent=2, ensure_ascii=False)
        print(f"✅ Updated {args.manifest_file} with injected SFX manifest.")

    finally:
        generator.stop_browser()

if __name__ == "__main__":
    main()
