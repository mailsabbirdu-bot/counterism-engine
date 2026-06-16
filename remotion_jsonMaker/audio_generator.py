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
        print("🌐 Navigating to Gemini for SFX Planning...")
        self.page.goto("https://gemini.google.com/app", wait_until="networkidle", timeout=60000)

    def stop_browser(self):
        if self.context: self.context.close()
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()
        self.page = None

    def _interact_with_gemini(self, prompt: str, retry_count: int = 2) -> str:
        for attempt in range(retry_count + 1):
            self.start_browser()
            page = self.page
            try:
                response_selectors = ["message-content", ".markdown.message-content", ".model-response-text", "[data-message-author-role='assistant']"]
                def get_msg_count():
                    for sel in response_selectors:
                        msgs = page.query_selector_all(sel)
                        if msgs: return len(msgs)
                    return 0

                initial_count = get_msg_count()
                print(f"⌨️  Attempt {attempt+1}: Initial message count is {initial_count}")

                # Aggressive obstruction dismissal
                overlays = ["button[aria-label='Accept all']", "button:has-text('Accept')", "button:has-text('I agree')", "button:has-text('Got it')", "ins-close-button"]
                for selector in overlays:
                    try:
                        elements = page.query_selector_all(selector)
                        for el in elements:
                            if el.is_visible():
                                print(f"   Dismissing UI blocker: {selector}")
                                el.click(force=True)
                                time.sleep(1)
                    except: pass

                page.evaluate("""() => {
                    const blockers = ['cdk-overlay-container', 'consent-dialog', 'cookie-banner', 'goog-consent-banner'];
                    blockers.forEach(id => {
                        const elements = document.querySelectorAll('.' + id + ', #' + id);
                        elements.forEach(el => el.style.display = 'none');
                    });
                }""")

                input_selector = "div[contenteditable='true']"
                page.wait_for_selector(input_selector, timeout=30000)

                print(f"⌨️  Sending SFX Design prompt to Gemini...")
                page.click(input_selector, force=True)
                time.sleep(1)
                page.fill(input_selector, prompt)
                time.sleep(1)
                page.keyboard.press("Enter")

                try:
                    btn = "button[aria-label*='Send message'], button[aria-label*='Submit']"
                    if page.is_visible(btn, timeout=2000): page.click(btn, force=True)
                except: pass

                print("⏳  Waiting for SFX plan to stabilize...")
                last_text = ""
                stable_count = 0
                for i in range(250):
                    time.sleep(2)
                    current_count = get_msg_count()
                    if current_count <= initial_count:
                        if i % 10 == 0: print(f"   ...still waiting for new message ({i/2}s)")
                        continue

                    current_text = ""
                    for sel in response_selectors:
                        msgs = page.query_selector_all(sel)
                        if msgs:
                            current_text = msgs[-1].inner_text()
                            break

                    if current_text and current_text == last_text:
                        stable_count += 1
                        if stable_count >= 8:
                            print(f"✨ SFX Plan received ({len(current_text)} chars).")
                            return current_text
                    else:
                        stable_count = 0
                        last_text = current_text

                print("🔄  Response taking too long, reloading Gemini...")
                page.reload(wait_until="domcontentloaded")
            except Exception as e:
                print(f"⚠️ Error during Gemini SFX interaction: {e}")
                page.reload(wait_until="domcontentloaded")
        return ""

    def generate_sfx_plan(self, manifest_json):
        simplified = []
        for scene in manifest_json.get('scenes', []):
            scene_info = { "scene_id": scene['scene_id'], "duration": scene['duration_in_frames'], "overlays": [] }
            for ov in scene.get('overlays', []):
                scene_info['overlays'].append({ "id": ov['id'], "type": ov['type'], "start": ov['start'], "duration": ov['duration'], "animation": ov.get('animation') })
            simplified.append(scene_info)
        prompt = (
            f"You are a Professional Sci-Fi Sound Designer. DESIGN sound effects ONLY for visual layer transitions.\n\n"
            f"MANIFEST:\n{json.dumps(simplified, indent=2)}\n\n"
            "TASK: Assign a unique SFX query for EVERY entrance and exit.\n"
            "STYLE: Sci-fi interface. Minimalist, high-tech, futuristic, cybernetic.\n"
            "CRITICAL RULES:\n"
            "1. LAYER TRANSITIONS ONLY: Use sounds only when layers appear (start) or disappear (end).\n"
            "2. SCI-FI TYPES: Use 'sci-fi digital reveal', 'hologram interface ping', 'cyberpunk whoosh', 'futuristic data surge'.\n"
            "3. NO BACKGROUND SOUNDS: Absolutely NO city ambience, wind, music or continuous noise.\n"
            "4. SEARCH QUERIES: Every query MUST end with 'royalty free'.\n"
            "RETURN ONLY RAW JSON LIST:\n"
            '[ { \"scene_id\": \"SCENE_01\", \"start_frame\": 10, \"end_frame\": 40, \"query\": \"sci-fi digital interface reveal royalty free\", \"volume\": 0.3, \"label\": \"layer_in\" } ]'
        )
        raw = self._interact_with_gemini(prompt)
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            try:
                cleaned = re.sub(r'//.*$', '', match.group(0), flags=re.MULTILINE)
                cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
                cleaned = re.sub(r',\s*\}', '}', cleaned)
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
            # Broaden queries
            queries = [item['query'], "sci-fi interface sound effect", "futuristic digital ping", "tech whoosh transition"]

            for q in queries:
                for client in clients:
                    print(f"🔍 [Query: {q} | Client: {client}] Searching...")
                    cmd = [
                        "yt-dlp", "--extract-audio", "--audio-format", "mp3",
                        "--no-check-certificates", "--geo-bypass", "--no-warnings",
                        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                        "--extractor-args", f"youtube:player_client={client}",
                        "--output", filepath, f"ytsearch1:{q}"
                    ]
                    try:
                        subprocess.run(cmd, check=True, timeout=120, capture_output=True)
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
        if not sfx_plan:
            print("⚠️ No SFX plan generated by Gemini.")
        else:
            print(f"✅ Planned {len(sfx_plan)} SFX events. Starting acquisition...")
            ts_audio = generator.download_sfx(sfx_plan, args.output_dir)
            with open(os.path.join(args.output_dir, "timestamp_audio.txt"), 'w') as f: json.dump(ts_audio, f, indent=2)
            manifest_json['audio_sfx_manifest'] = ts_audio
            with open(args.manifest_file, 'w', encoding='utf-8') as f: json.dump(manifest_json, f, indent=2, ensure_ascii=False)
            print(f"✅ SFX acquisition and manifest update complete.")
    finally: generator.stop_browser()

if __name__ == "__main__": main()
