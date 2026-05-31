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
        if drive_prompt_path and os.path.exists(drive_prompt_path):
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
            browser_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage"
            ]

            if self.user_data_dir:
                context = p.chromium.launch_persistent_context(
                    self.user_data_dir,
                    headless=self.headless,
                    args=browser_args
                )
            else:
                browser = p.chromium.launch(headless=self.headless, args=browser_args)
                context = browser.new_context()

            page = context.new_page()
            stealth(page)

            print("🌐 Navigating to Gemini...")
            # Use a longer timeout for navigation
            page.goto("https://gemini.google.com/app", wait_until="networkidle", timeout=60000)

            try:
                # Wait for the text area - Gemini uses a contenteditable div
                print("📝 Waiting for input area...")
                input_selector = "div[contenteditable='true']"
                page.wait_for_selector(input_selector, timeout=45000)

                print("⌨️ Injecting prompt...")
                page.fill(input_selector, full_prompt)

                # Press Enter to send
                page.keyboard.press("Enter")

                print("⏳ Waiting for Gemini to generate response...")

                # Try multiple possible selectors for the response
                response_selectors = [
                    ".model-response-text",
                    "message-content",
                    ".markdown.message-content",
                    "div[class*='model-response']"
                ]

                found_selector = None
                for selector in response_selectors:
                    try:
                        page.wait_for_selector(selector, timeout=10000)
                        found_selector = selector
                        break
                    except:
                        continue

                if not found_selector:
                    # Fallback: wait for the stop button to disappear if it appeared, or just wait a bit
                    print("⚠️ Standard selectors not found, waiting for stabilization...")
                    time.sleep(10)
                    # Try to find the last message by role or class pattern
                    found_selector = ".model-response-text" # Default back to this

                # Wait for response to stabilize (streaming to finish)
                last_len = 0
                stable_count = 0
                for _ in range(60): # Max 120 seconds wait
                    time.sleep(2)
                    responses = page.query_selector_all(found_selector)
                    if not responses:
                        # Try to find any message content if the specific selector failed
                        responses = page.query_selector_all("div[class*='message-content']")

                    if not responses: continue

                    current_text = responses[-1].inner_text()
                    current_len = len(current_text)

                    if current_len > 0 and current_len == last_len:
                        stable_count += 1
                        if stable_count >= 3: # Stable for 6 seconds
                            break
                    else:
                        stable_count = 0

                    last_len = current_len

                responses = page.query_selector_all(found_selector)
                if not responses:
                    responses = page.query_selector_all("div[class*='message-content']")

                if not responses:
                    raise Exception("Failed to find Gemini response after waiting.")

                raw_output = responses[-1].inner_text()
                print(f"✅ Response received (Length: {len(raw_output)}).")

                # Extract JSON from potential markdown blocks
                json_match = re.search(r'(\{.*\})', raw_output, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        # Try cleaning up markdown if re failed to be precise
                        cleaned = json_match.group(1).strip()
                        # Deep cleaning
                        cleaned = re.sub(r'^```json\s*', '', cleaned)
                        cleaned = re.sub(r'^```\s*', '', cleaned)
                        cleaned = re.sub(r'\s*```$', '', cleaned)
                        return json.loads(cleaned)
                else:
                    # Try cleaning the whole output
                    cleaned = raw_output.strip()
                    if cleaned.startswith("```json"):
                        cleaned = cleaned[7:]
                    if cleaned.startswith("```"):
                        cleaned = cleaned[3:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                    return json.loads(cleaned.strip())

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
    parser.add_argument("--drive-prompt", help="Path to the guideline_prompt.txt on Google Drive")
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
    drive_prompt = args.drive_prompt or "/content/drive/MyDrive/google audio/manifests/guideline_prompt.txt"

    # Avoid loading the same file as guidelines if it's the story source
    if args.story_file == drive_prompt:
        drive_prompt = None

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
