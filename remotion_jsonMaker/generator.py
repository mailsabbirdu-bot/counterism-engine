import os
import json
import argparse
import re
import time
from typing import Dict, Any
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth

class RemotionJsonMaker:
    def __init__(self, user_data_dir: str = None, headless: bool = True):
        self.user_data_dir = user_data_dir
        self.headless = headless

    def load_guidelines(self, local_guideline_path: str, local_prompt_path: str, drive_prompt_path: str) -> str:
        guidelines = ""

        # Load local guideline.md
        if os.path.exists(local_guideline_path):
            with open(local_guideline_path, 'r') as f:
                guidelines += f"\n--- ENGINE GUIDELINES ---\n{f.read()}\n"

        # Load local guideline_prompt.txt
        if os.path.exists(local_prompt_path):
            with open(local_prompt_path, 'r') as f:
                guidelines += f"\n--- TECHNICAL SCHEMA ---\n{f.read()}\n"

        # Load drive guideline_prompt.txt (if exists)
        if os.path.exists(drive_prompt_path):
            with open(drive_prompt_path, 'r') as f:
                guidelines += f"\n--- DRIVE SPECIFIC INSTRUCTIONS ---\n{f.read()}\n"

        return guidelines

    def generate(self, story: str, guidelines: str) -> Dict[str, Any]:
        # Clean guidelines: Remove the example JSON to prevent hallucination
        guidelines = re.sub(r'## 📝 Comprehensive Reference Example.*', '', guidelines, flags=re.DOTALL)

        full_prompt = (
            "You are a Remotion V4 JSON master. Return ONLY raw JSON. No markdown. No comments. "
            "Ensure the output is a single valid JSON object following the TECHNICAL SCHEMA provided.\n\n"
            f"GUIDELINES:\n{guidelines}\n\n"
            f"STORY AND SCENE REQUIREMENTS:\n{story}\n\n"
            "TASK:\nGenerate the complete JSON manifest. Return ONLY the JSON object."
        )

        with sync_playwright() as p:
            print("🚀 Launching browser...")
            if self.user_data_dir:
                context = p.chromium.launch_persistent_context(
                    self.user_data_dir,
                    headless=self.headless,
                    args=["--disable-blink-features=AutomationControlled"]
                )
            else:
                browser = p.chromium.launch(headless=self.headless, args=["--disable-blink-features=AutomationControlled"])
                context = browser.new_context()

            page = context.new_page()
            stealth(page)

            print("🌐 Navigating to Gemini...")
            page.goto("https://gemini.google.com/app", wait_until="networkidle")

            try:
                # Wait for the text area - Gemini uses a contenteditable div
                print("📝 Waiting for input area...")
                input_selector = "div[contenteditable='true']"
                page.wait_for_selector(input_selector, timeout=30000)

                print("⌨️ Injecting prompt...")
                page.fill(input_selector, full_prompt)

                # Press Enter to send
                page.keyboard.press("Enter")

                print("⏳ Waiting for Gemini to generate response...")
                # Gemini responses are contained in elements with class 'message-content' or similar.
                # We wait for the 'stop' button (interrupt) to disappear or the response to stabilize.
                # A more reliable way: wait for the next model-response element and wait for it to stop changing.

                response_selector = ".model-response-text"
                page.wait_for_selector(response_selector, timeout=120000)

                # Give it some time to finish streaming
                last_len = 0
                for _ in range(20): # Max 20 seconds wait for stabilization
                    time.sleep(2)
                    responses = page.query_selector_all(response_selector)
                    if not responses: continue
                    current_len = len(responses[-1].inner_text())
                    if current_len == last_len and current_len > 0:
                        break
                    last_len = current_len

                responses = page.query_selector_all(response_selector)
                if not responses:
                    raise Exception("Failed to find Gemini response.")

                raw_output = responses[-1].inner_text()
                print("✅ Response received.")

                # Extract JSON from potential markdown blocks
                json_match = re.search(r'(\{.*\})', raw_output, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        # Try cleaning up markdown if re failed to be precise
                        cleaned = raw_output.strip()
                        if cleaned.startswith("```json"):
                            cleaned = cleaned[7:]
                        if cleaned.startswith("```"):
                            cleaned = cleaned[3:]
                        if cleaned.endswith("```"):
                            cleaned = cleaned[:-3]
                        return json.loads(cleaned.strip())
                else:
                    return json.loads(raw_output.strip())

            finally:
                if self.user_data_dir:
                    context.close()
                else:
                    browser.close()

def main():
    parser = argparse.ArgumentParser(description="Counterism Studio V4 JSON Maker (Playwright Gemini Edition)")
    parser.add_argument("--story", help="The story or topic for the video")
    parser.add_argument("--story-file", help="Path to a text file containing the story/topic")
    parser.add_argument("--output", required=True, help="Path to save remotion_render.json")
    parser.add_argument("--user-data-dir", help="Path to Chromium user data directory for persistent session")
    parser.add_argument("--no-headless", action="store_false", dest="headless", help="Run browser in non-headless mode")
    parser.set_defaults(headless=True)

    args = parser.parse_args()

    # Determine the story source
    story = args.story
    if args.story_file and os.path.exists(args.story_file):
        with open(args.story_file, 'r') as f:
            story = f.read()

    if not story:
        print("❌ Error: No story provided. Use --story or --story-file.")
        exit(1)

    maker = RemotionJsonMaker(user_data_dir=args.user_data_dir, headless=args.headless)

    # Paths
    local_guideline = "../guideline.md"
    local_prompt = "../guideline_prompt.txt"
    # Updated to 'google audio' as requested by user
    drive_prompt = "/content/drive/MyDrive/google audio/manifests/guideline_prompt.txt"

    if args.story_file == drive_prompt:
        drive_prompt = ""

    print("📋 Loading guidelines...")
    guidelines = maker.load_guidelines(local_guideline, local_prompt, drive_prompt)

    print(f"✨ Generating JSON for story via Gemini...")
    try:
        render_json = maker.generate(story, guidelines)

        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(render_json, f, indent=2)

        print(f"✅ Master JSON created successfully at: {args.output}")
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        exit(1)

if __name__ == "__main__":
    main()
