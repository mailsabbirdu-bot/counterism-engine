import os
import json
import argparse
import re
import time
import subprocess
from typing import Dict, Any
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth

class RemotionJsonMaker:
    def __init__(self, user_data_dir: str = None, headless: bool = True):
        self.user_data_dir = user_data_dir
        self.headless = headless

    def probe_video_fps(self, video_path: str) -> float:
        """Probes a video file for its FPS using ffprobe."""
        try:
            cmd = [
                "ffprobe", "-v", "0", "-of", "csv=p=0", "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate", video_path
            ]
            output = subprocess.check_output(cmd).decode("utf-8").strip()
            if "/" in output:
                num, den = map(float, output.split("/"))
                return num / den
            return float(output)
        except Exception as e:
            print(f"⚠️ Warning: Could not probe FPS for {video_path}: {e}")
            return 30.0

    def adjust_durations_in_text(self, text: str, public_dir: str = "../public") -> str:
        """
        Scans text for video_path and duration_in_frames and adjusts them if
        the source video FPS is not 30.
        """
        # Find all scene blocks or at least pairs of video_path and duration_in_frames
        # We'll use a regex that looks for video_path then duration_in_frames or vice-versa

        def replacement_logic(match):
            full_match = match.group(0)
            vpath_match = re.search(r'"video_path":\s*"([^"]+)"', full_match)
            duration_match = re.search(r'"duration_in_frames"\s*:\s*(\d+)', full_match)

            if vpath_match and duration_match:
                rel_vpath = vpath_match.group(1)
                orig_duration_str = duration_match.group(1)
                orig_duration = int(orig_duration_str)

                abs_vpath = os.path.join(public_dir, rel_vpath)
                if os.path.exists(abs_vpath):
                    fps = self.probe_video_fps(abs_vpath)
                    if abs(fps - 30.0) > 0.1:
                        # Recalculate duration for 30fps target
                        new_duration = int(round((orig_duration / fps) * 30))
                        print(f"⚖️ Adjusting {rel_vpath}: {fps}fps, {orig_duration}f -> {new_duration}f (30fps target)")

                        # Replace the duration value safely within the duration_in_frames field
                        new_val = f'"duration_in_frames": {new_duration}'
                        # This regex replaces the entire duration field to be safe
                        return re.sub(r'"duration_in_frames"\s*:\s*\d+', new_val, full_match)

            return full_match

        # Match blocks that contain both video_path and duration_in_frames
        # We look for these pairs within a short distance of each other (e.g. 200 chars)
        # This handles both JSON-like blocks and raw text lists.

        # Pattern 1: video_path followed by duration_in_frames
        pattern = r'("video_path":\s*"[^"]+".{0,200}?"duration_in_frames"\s*:\s*\d+)'
        text = re.sub(pattern, replacement_logic, text, flags=re.DOTALL)

        # Pattern 2: duration_in_frames followed by video_path
        pattern_rev = r'("duration_in_frames"\s*:\s*\d+.{0,200}?"video_path":\s*"[^"]+")'
        text = re.sub(pattern_rev, replacement_logic, text, flags=re.DOTALL)

        return text

    def load_guidelines(self, local_guideline_path: str, local_prompt_path: str, drive_prompt_path: str) -> str:
        guidelines = ""

        # Load local guideline.md from the repository root
        if os.path.exists(local_guideline_path):
            with open(local_guideline_path, 'r') as f:
                guidelines += f"\n--- ENGINE SYSTEM GUIDELINES ---\n{f.read()}\n"

        # Load local guideline_prompt.txt from the repository root
        if os.path.exists(local_prompt_path):
            with open(local_prompt_path, 'r') as f:
                guidelines += f"\n--- TECHNICAL SCHEMA & COMPONENTS ---\n{f.read()}\n"

        # Load drive guideline_prompt.txt (this contains story and specific instructions)
        if drive_prompt_path and os.path.exists(drive_prompt_path):
            with open(drive_prompt_path, 'r') as f:
                guidelines += f"\n--- STORY AND DURATION SPECIFICATIONS (DRIVE) ---\n{f.read()}\n"

        return guidelines

    def generate(self, story: str, guidelines: str, prompt_output_path: str = None) -> Dict[str, Any]:
        # Clean guidelines: Remove the example JSON to prevent hallucination
        guidelines = re.sub(r'## 📝 Comprehensive Reference Example.*', '', guidelines, flags=re.DOTALL)

        full_prompt = (
            "You are a Remotion V4 JSON master. Return ONLY raw JSON. No markdown. No comments. "
            "Ensure the output is a single valid JSON object following the TECHNICAL SCHEMA provided.\n\n"
            f"SYSTEM GUIDELINES AND SCHEMA:\n{guidelines}\n\n"
            f"STORY AND SCENE REQUIREMENTS:\n{story}\n\n"
            "TASK:\nGenerate the complete JSON manifest. Return ONLY the JSON object."
        )

        # Save the prompt to a file if requested
        if prompt_output_path:
            os.makedirs(os.path.dirname(prompt_output_path), exist_ok=True)
            with open(prompt_output_path, 'w') as f:
                f.write(full_prompt)
            print(f"📝 Prompt saved to: {prompt_output_path}")

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
                    print("⚠️ Standard selectors not found, waiting for stabilization...")
                    time.sleep(10)
                    found_selector = ".model-response-text"

                last_len = 0
                stable_count = 0
                for _ in range(60):
                    time.sleep(2)
                    responses = page.query_selector_all(found_selector)
                    if not responses:
                        responses = page.query_selector_all("div[class*='message-content']")

                    if not responses: continue

                    current_text = responses[-1].inner_text()
                    current_len = len(current_text)

                    if current_len > 0 and current_len == last_len:
                        stable_count += 1
                        if stable_count >= 3:
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
                        cleaned = json_match.group(1).strip()
                        cleaned = re.sub(r'^```json\s*', '', cleaned)
                        cleaned = re.sub(r'^```\s*', '', cleaned)
                        cleaned = re.sub(r'\s*```$', '', cleaned)
                        return json.loads(cleaned)
                else:
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
    parser.add_argument("--prompt-output", help="Path to save the generated prompt (remotion_prompt.txt)")
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

    # Paths (relative to the remotion_jsonMaker folder)
    local_guideline = "../guideline.md"
    local_prompt = "../guideline_prompt.txt"
    drive_prompt = args.drive_prompt

    print("📋 Loading guidelines and context...")
    guidelines = maker.load_guidelines(local_guideline, local_prompt, drive_prompt)

    print("⚖️ Checking and adjusting video durations for 30fps target...")
    # Adjust in guidelines (which might contain the story) and the story itself
    story = maker.adjust_durations_in_text(story)
    guidelines = maker.adjust_durations_in_text(guidelines)

    print(f"✨ Generating JSON for story via Gemini...")
    try:
        render_json = maker.generate(story, guidelines, prompt_output_path=args.prompt_output)

        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(render_json, f, indent=2)

        print(f"✅ Master JSON created successfully at: {args.output}")
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        exit(1)

if __name__ == "__main__":
    main()
