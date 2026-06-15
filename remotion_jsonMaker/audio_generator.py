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
        args = ["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
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
                        if stable_count >= 4: return current_text
                    else:
                        stable_count = 0
                        last_text = current_text
            return last_text
        except Exception as e: return f"Error: {e}"

    def generate_sfx_plan(self, manifest_json):
        simplified_manifest = []
        for scene in manifest_json.get('scenes', []):
            scene_info = {
                "scene_id": scene['scene_id'],
                "duration_in_frames": scene['duration_in_frames'],
                "overlays": []
            }
            for ov in scene.get('overlays', []):
                scene_info['overlays'].append({
                    "id": ov['id'], "type": ov['type'], "start": ov['start'],
                    "duration": ov['duration'], "animation": ov.get('animation')
                })
            simplified_manifest.append(scene_info)

        prompt = (
            f"You are a Professional Sound Designer. Sync SFX precisely with visual transitions.\n\n"
            f"MANIFEST:\n{json.dumps(simplified_manifest, indent=2)}\n\n"
            "TASK: Assign a high-quality SFX query for EVERY overlay entrance/exit.\n"
            "RULES:\n1. MUST sync with 'start' and 'duration'.\n"
            "2. Pick non-copyright queries (e.g. 'tech whoosh sound effect no copyright').\n"
            "RETURN ONLY RAW JSON LIST:\n"
            '[ { "scene_id": "SCENE_01", "start_frame": 10, "end_frame": 40, "query": "cinematic hit", "volume": 0.5, "label": "intro" } ]'
        )
        raw_output = self._interact_with_gemini(prompt)
        json_match = re.search(r'\[.*\]', raw_output, re.DOTALL)
        if json_match:
            try:
                cleaned = json_match.group(0)
                cleaned = re.sub(r',\s*}', '}', cleaned)
                cleaned = re.sub(r',\s*\]', ']', cleaned)
                return json.loads(cleaned)
            except: pass
        return []

    def download_sfx(self, sfx_plan, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        timestamp_entries = []
        # Enhanced yt-dlp config to bypass bot detection/sign-in
        # Use multiple player clients and additional bypass args
        base_cmd = [
            "yt-dlp", "--extract-audio", "--audio-format", "mp3",
            "--no-check-certificates",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "--extractor-args", "youtube:player_client=android,web",
            "--prefer-free-formats", "--limit-rate", "1M",
            "--geo-bypass", "--no-warnings"
        ]

        for i, item in enumerate(sfx_plan):
            clean_label = re.sub(r'[^a-z0-9]', '_', item.get('label', 'sfx').lower())
            filename = f"sfx_{item['scene_id']}_{i:02d}_{clean_label}.mp3"
            filepath = os.path.join(output_dir, filename)

            print(f"🔍 Searching: {item['query']}")
            # Use a slightly broader search to avoid specific sign-in wall videos
            search_query = f"ytsearch1:{item['query']} royalty free"
            cmd = base_cmd + ["--output", filepath, search_query]

            try:
                # Add check for existing file to avoid redundant downloads
                if os.path.exists(filepath):
                    print(f"✅ Already exists: {filename}")
                else:
                    subprocess.run(cmd, check=True, timeout=180)
                    print(f"✅ Saved to {filename}")

                timestamp_entries.append({
                    "scene_id": item['scene_id'], "file": filename,
                    "start": item['start_frame'], "end": item['end_frame'], "volume": item['volume']
                })
            except Exception as e:
                print(f"❌ Failed download: {e}")
                # We still add it to the manifest so the engine knows it was intended,
                # but the file will just be missing during render (handled by AudioEngine)
                timestamp_entries.append({
                    "scene_id": item['scene_id'], "file": filename,
                    "start": item['start_frame'], "end": item['end_frame'], "volume": item['volume'],
                    "status": "failed"
                })
        return timestamp_entries

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-file", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--user-data-dir")
    args = parser.parse_args()

    if not os.path.exists(args.manifest_file):
        print(f"❌ Manifest not found: {args.manifest_file}")
        return

    with open(args.manifest_file, 'r', encoding='utf-8') as f: manifest_json = json.load(f)
    generator = AudioManifestGenerator(user_data_dir=args.user_data_dir)
    try:
        sfx_plan = generator.generate_sfx_plan(manifest_json)
        ts_audio = generator.download_sfx(sfx_plan, args.output_dir)

        with open(os.path.join(args.output_dir, "timestamp_audio.txt"), 'w') as f:
            json.dump(ts_audio, f, indent=2)

        manifest_json['audio_sfx_manifest'] = ts_audio
        with open(args.manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest_json, f, indent=2, ensure_ascii=False)
        print(f"✅ Master JSON updated with SFX manifest.")
    finally: generator.stop_browser()

if __name__ == "__main__": main()
