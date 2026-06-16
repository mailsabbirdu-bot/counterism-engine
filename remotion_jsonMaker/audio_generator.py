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
        print("🌐 Navigating to Gemini for Layer SFX Design...")
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
            print("⌨️  Sending Layer SFX Design prompt...")
            page.click(input_selector)
            page.fill(input_selector, prompt)
            time.sleep(1)
            page.keyboard.press("Enter")
            print("⏳  Waiting for SFX plan...")
            response_selectors = ["message-content", ".markdown.message-content", ".model-response-text"]
            last_text = ""
            stable_count = 0
            for i in range(100):
                time.sleep(2)
                current_text = ""
                for sel in response_selectors:
                    msgs = page.query_selector_all(sel)
                    if msgs:
                        current_text = msgs[-1].inner_text()
                        break
                if current_text and current_text == last_text:
                    stable_count += 1
                    if stable_count >= 5: return current_text
                else:
                    stable_count = 0
                    last_text = current_text
            return last_text
        except Exception as e: return f"Error: {e}"

    def generate_sfx_plan(self, manifest_json):
        simplified = []
        for scene in manifest_json.get('scenes', []):
            scene_info = { "scene_id": scene['scene_id'], "duration": scene['duration_in_frames'], "overlays": [] }
            for ov in scene.get('overlays', []):
                scene_info['overlays'].append({ "id": ov['id'], "type": ov['type'], "start": ov['start'], "duration": ov['duration'], "animation": ov.get('animation') })
            simplified.append(scene_info)
        prompt = (
            f"You are a Professional Sound Designer. DESIGN sound effects ONLY for visual layer transitions.\n\n"
            f"MANIFEST:\n{json.dumps(simplified, indent=2)}\n\n"
            "TASK: Assign a unique SFX query for EVERY entrance and exit.\n"
            "CRITICAL RULES:\n"
            "1. NO BACKGROUND SOUNDS: Absolutely NO city ambience, wind, or continuous noise. SFX must be short (< 2s) and layer-specific.\n"
            "2. LAYER TRANSITIONS: Focus on 'start' and 'duration' offsets.\n"
            "3. NO TYPEWRITING: Strictly forbid typewriting sounds. Use 'cinematic transition swell', 'digital pop', or 'tech reveal'.\n"
            "4. UNIQUE & ROYALTY FREE: Query MUST end with 'royalty free'.\n"
            "RETURN ONLY RAW JSON LIST:\n"
            '[ { "scene_id": "SCENE_01", "start_frame": 10, "end_frame": 40, "query": "digital pop reveal", "volume": 0.5, "label": "layer_in" } ]'
        )
        raw = self._interact_with_gemini(prompt)
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            try:
                cleaned = re.sub(r',\s*}', '}', match.group(0))
                cleaned = re.sub(r',\s*\]', ']', cleaned)
                return json.loads(cleaned)
            except: pass
        return []

    def download_sfx(self, sfx_plan, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        timestamp_entries = []
        clients = ["android", "web"]

        for i, item in enumerate(sfx_plan):
            clean_label = re.sub(r'[^a-z0-9]', '_', item.get('label', 'sfx').lower())
            filename = f"sfx_{item['scene_id']}_{i:02d}_{clean_label}.mp3"
            filepath = os.path.join(output_dir, filename)

            if os.path.exists(filepath):
                timestamp_entries.append({ "scene_id": item['scene_id'], "file": filename, "start": item['start_frame'], "end": item['end_frame'], "volume": item['volume'] })
                continue

            success = False
            # Fallback sequence: Original -> Simple -> Simplest
            queries = [item['query'], "pop digital sound effect", "whoosh transition"]

            for q in queries:
                for client in clients:
                    print(f"🔍 [Query: {q} | Client: {client}] Searching...")
                    cmd = [
                        "yt-dlp", "--extract-audio", "--audio-format", "mp3",
                        "--no-check-certificates", "--geo-bypass", "--no-warnings",
                        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                        "--extractor-args", f"youtube:player_client={client}",
                        "--output", filepath, f"ytsearch1:{q} royalty free"
                    ]
                    try:
                        subprocess.run(cmd, check=True, timeout=120)
                        if os.path.exists(filepath):
                            success = True
                            break
                    except: continue
                if success: break

            if success:
                timestamp_entries.append({ "scene_id": item['scene_id'], "file": filename, "start": item['start_frame'], "end": item['end_frame'], "volume": item['volume'] })
            else:
                timestamp_entries.append({ "scene_id": item['scene_id'], "file": filename, "start": item['start_frame'], "end": item['end_frame'], "volume": item['volume'], "status": "failed" })
        return timestamp_entries

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-file", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--user-data-dir")
    args = parser.parse_args()
    if not os.path.exists(args.manifest_file): return
    with open(args.manifest_file, 'r', encoding='utf-8') as f: manifest_json = json.load(f)
    generator = AudioManifestGenerator(user_data_dir=args.user_data_dir)
    try:
        sfx_plan = generator.generate_sfx_plan(manifest_json)
        ts_audio = generator.download_sfx(sfx_plan, args.output_dir)
        with open(os.path.join(args.output_dir, "timestamp_audio.txt"), 'w') as f: json.dump(ts_audio, f, indent=2)
        manifest_json['audio_sfx_manifest'] = ts_audio
        with open(args.manifest_file, 'w', encoding='utf-8') as f: json.dump(manifest_json, f, indent=2, ensure_ascii=False)
    finally: generator.stop_browser()

if __name__ == "__main__": main()
