import os
import json
import argparse
import re
import time
import subprocess
from typing import Dict, Any
from playwright.sync_api import sync_playwright
import playwright_stealth

class RemotionJsonMaker:
    def __init__(self, user_data_dir: str = None, headless: bool = True):
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start_browser(self):
        """Initializes a persistent browser session."""
        if self.page: return

        self.playwright = sync_playwright().start()
        print("🚀 Launching persistent browser...")
        browser_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage"
        ]

        if self.user_data_dir:
            self.context = self.playwright.chromium.launch_persistent_context(
                self.user_data_dir,
                headless=self.headless,
                args=browser_args
            )
        else:
            self.browser = self.playwright.chromium.launch(headless=self.headless, args=browser_args)
            self.context = self.browser.new_context()

        self.page = self.context.new_page()
        playwright_stealth.Stealth().apply_stealth_sync(self.page)
        print("🌐 Navigating to Gemini...")
        self.page.goto("https://gemini.google.com/app", wait_until="networkidle", timeout=60000)

    def stop_browser(self):
        """Closes the browser session."""
        if self.context: self.context.close()
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()
        self.page = None

    def probe_video_duration_and_fps(self, video_path: str):
        """Probes a video file for its duration and FPS using ffprobe."""
        try:
            cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=duration,nb_frames,r_frame_rate",
                "-of", "json", video_path
            ]
            output = subprocess.check_output(cmd).decode("utf-8")
            data = json.loads(output)
            if not data.get('streams'):
                # Fallback for some formats
                cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", video_path]
                output = subprocess.check_output(cmd).decode("utf-8")
                data = json.loads(output)
                return float(data['format'].get('duration', 0)), 30.0

            stream = data['streams'][0]
            duration = float(stream.get('duration', 0))
            if duration == 0:
                # Try format duration
                cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", video_path]
                output = subprocess.check_output(cmd).decode("utf-8")
                data = json.loads(output)
                duration = float(data['format'].get('duration', 0))

            fps_str = stream.get('r_frame_rate', '30/1')
            if '/' in fps_str:
                num, den = map(float, fps_str.split('/'))
                fps = num / den if den != 0 else 30.0
            else:
                fps = float(fps_str)

            return duration, fps
        except Exception as e:
            print(f"⚠️ Warning: Could not probe video stats for {video_path}: {e}")
            return 0.0, 30.0

    def adjust_durations_in_text(self, text: str, public_dir: str = "../public") -> str:
        """
        Scans text for video_path and duration_in_frames and adjusts them if
        the source video FPS is not 30. Uses strict boundary checks to avoid scene mismatch.
        """

        def replacement_logic(match):
            block = match.group(0)
            vpath_match = re.search(r'"video_path":\s*"([^"]+)"', block)
            duration_match = re.search(r'"duration_in_frames"\s*:\s*(\d+)', block)

            if vpath_match:
                rel_vpath = vpath_match.group(1)
                abs_vpath = os.path.join(public_dir, rel_vpath)

                if os.path.exists(abs_vpath):
                    duration_sec, fps = self.probe_video_duration_and_fps(abs_vpath)

                    if duration_sec > 0:
                        # Most accurate way to target 30fps: use real-world duration in seconds
                        new_duration = int(round(duration_sec * 30))

                        if duration_match:
                            orig_duration = int(duration_match.group(1))
                            if new_duration != orig_duration:
                                print(f"⚖️ Adjusting {rel_vpath}: {duration_sec}s ({fps}fps source) -> {new_duration}f (30fps target)")
                                return re.sub(r'"duration_in_frames"\s*:\s*\d+', f'"duration_in_frames": {new_duration}', block)
                        else:
                            # If duration wasn't in this specific match block but video_path was,
                            # we might need to be careful, but the regex patterns below pair them.
                            pass

            return block

        # Find blocks that are likely individual scene definitions or adjacent properties.
        # We look for pairs that don't have another instance of either key between them.
        # This is more robust against scene crossing.

        # Strategy: Match any block that contains both keys within a reasonable range,
        # ensuring we don't skip over another scene.

        # Pattern 1: video_path ... duration_in_frames
        pattern1 = r'("video_path":\s*"[^"]+"(?:(?!"video_path"|"duration_in_frames").){0,300}?"duration_in_frames"\s*:\s*\d+)'
        text = re.sub(pattern1, replacement_logic, text, flags=re.DOTALL)

        # Pattern 2: duration_in_frames ... video_path
        pattern2 = r'("duration_in_frames"\s*:\s*\d+(?:(?!"video_path"|"duration_in_frames").){0,300}?"video_path":\s*"[^"]+")'
        text = re.sub(pattern2, replacement_logic, text, flags=re.DOTALL)

        return text

    def get_local_fonts(self, public_dir: str = "../public") -> str:
        """Scans the public/fonts directory and returns a descriptive string of available fonts."""
        fonts_dir = os.path.join(public_dir, "fonts")
        if not os.path.exists(fonts_dir):
            return "No local fonts detected."

        font_files = []
        for root, dirs, files in os.walk(fonts_dir):
            for file in files:
                if file.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
                    name = os.path.splitext(file)[0]
                    font_files.append(name)

        if not font_files:
            return "No local font files found in public/fonts."

        return ", ".join(sorted(list(set(font_files))))

    def load_guidelines(self, local_guideline_path: str, local_prompt_path: str, drive_prompt_path: str) -> str:
        guidelines = ""

        # Load local guideline.md from the repository root
        if os.path.exists(local_guideline_path):
            with open(local_guideline_path, 'r', encoding='utf-8') as f:
                guidelines += f"\n--- ENGINE SYSTEM GUIDELINES ---\n{f.read()}\n"

        # Load local guideline_prompt.txt from the repository root
        if os.path.exists(local_prompt_path):
            with open(local_prompt_path, 'r', encoding='utf-8') as f:
                guidelines += f"\n--- TECHNICAL SCHEMA & COMPONENTS ---\n{f.read()}\n"

        # Load drive guideline_prompt.txt (this contains story and specific instructions)
        if drive_prompt_path and os.path.exists(drive_prompt_path):
            with open(drive_prompt_path, 'r', encoding='utf-8') as f:
                guidelines += f"\n--- STORY AND DURATION SPECIFICATIONS (DRIVE) ---\n{f.read()}\n"

        return guidelines

    def finalize_json_durations(self, data: Dict[str, Any], public_dir: str = "../public") -> Dict[str, Any]:
        """
        Iterates through scenes and ensures duration_in_frames is perfectly
        aligned with the actual background video duration at 30fps.
        """
        if not data.get('scenes'):
            return data

        for scene in data['scenes']:
            if scene.get('background_type') == 'video' and scene.get('video_path'):
                vpath = scene['video_path']
                abs_vpath = os.path.join(public_dir, vpath)

                if os.path.exists(abs_vpath):
                    duration_sec, fps = self.probe_video_duration_and_fps(abs_vpath)
                    if duration_sec > 0:
                        target_fps = data.get('global_settings', {}).get('fps', 30)
                        new_duration = int(round(duration_sec * target_fps))
                        print(f"🎯 Finalizing {vpath}: {duration_sec}s ({fps}fps) -> {new_duration}f (@{target_fps}fps)")
                        scene['duration_in_frames'] = new_duration

        return data

    def generate_word_timestamps(self, story: str, public_dir: str = "../public") -> str:
        """
        Parses story.txt, maps to videos, and uses Gemini to estimate word-level timestamps for all scenes in one go.
        Returns the content for timestamp.txt.
        """
        print("🎙️  Generating word-level timestamps via Gemini (All Scenes)...")
        self.start_browser()

        # Robust parsing logic for scene-based story supporting Bengali digits
        scene_markers = re.findall(r'দৃশ্য\s+[0-9১-৯]+', story)
        scene_texts = re.split(r'দৃশ্য\s+[0-9১-৯]+', story)
        scene_texts = [s.strip() for s in scene_texts if s.strip()]

        full_ts_prompt = (
            "You are a Voiceover Alignment Assistant. Below is a story with multiple scenes. "
            "For each scene, I will provide the text and the total duration. "
            "Provide word-level timestamps in FRAMES for a 30fps project. Start every scene from frame 0.\n\n"
        )

        for i, scene_text in enumerate(scene_texts):
            scene_num = i + 1
            vpath = f"renders/scene_SC_{scene_num:02d}.mp4"
            abs_vpath = os.path.join(public_dir, vpath)
            duration_sec = 0.0
            if os.path.exists(abs_vpath):
                duration_sec, _ = self.probe_video_duration_and_fps(abs_vpath)
            if duration_sec == 0: duration_sec = 6.0 # Reasonable fallback

            full_ts_prompt += (
                f"--- SCENE {scene_num:02d} ({duration_sec}s / {int(round(duration_sec * 30))} frames) ---\n"
                f"TEXT: {scene_text}\n\n"
            )

        full_ts_prompt += (
            "INSTRUCTIONS:\n"
            "1. Format: SCENE_XX: [Frame X - Frame Y] Word1, [Frame Y - Frame Z] Word2...\n"
            "2. Ensure timestamps are frame-accurate for 30fps.\n"
            "3. Return ONLY the timestamps for all scenes. No conversational text."
        )

        try:
            return self._interact_with_gemini(full_ts_prompt)
        except Exception as e:
            print(f"⚠️ Error generating bulk timestamps: {e}")
            return "Error generating timestamps."

    def _interact_with_gemini(self, prompt: str) -> str:
        """Helper method for raw Gemini browser interaction using persistent page."""
        self.start_browser()
        page = self.page

        try:
            input_selector = "div[contenteditable='true']"
            page.wait_for_selector(input_selector, timeout=45000)
            page.click(input_selector)
            page.fill(input_selector, prompt)
            page.keyboard.press("Enter")

            try:
                send_button = "button[aria-label*='Send'], .send-button, button.send-icon"
                if page.is_visible(send_button, timeout=3000):
                    page.click(send_button)
            except:
                pass

            # Wait for response to START appearing
            response_selectors = [".model-response-text", "message-content", ".markdown.message-content", "div[class*='model-response']", "[data-message-author-role='assistant']", "div[role='log']"]
            found_selector = None

            # Use a loop to check for the LAST message appearing
            initial_count = len(page.query_selector_all("div[class*='model-response'], [data-message-author-role='assistant']"))

            for _ in range(45): # Wait up to 45s for start
                time.sleep(1)
                current_responses = page.query_selector_all("div[class*='model-response'], [data-message-author-role='assistant']")
                if len(current_responses) > initial_count:
                    # New response detected, now find which selector works for it
                    for selector in response_selectors:
                        if page.query_selector(selector):
                            found_selector = selector
                            break
                    if found_selector: break

            if not found_selector:
                print("⚠️ Standard selectors not found, falling back to position-based extraction...")
                found_selector = "div[class*='model-response'], [data-message-author-role='assistant']"

            # Wait for stabilization (streaming to finish)
            last_len = 0
            stable_ticks = 0
            for _ in range(60):
                time.sleep(1)
                responses = page.query_selector_all(found_selector)
                if not responses: continue
                current_text = responses[-1].inner_text()
                if len(current_text) > 0 and len(current_text) == last_len:
                    stable_ticks += 1
                    if stable_ticks >= 3: break
                else:
                    stable_ticks = 0
                last_len = len(current_text)

            responses = page.query_selector_all(found_selector)
            return responses[-1].inner_text() if responses else "Error: Response empty."
        except Exception as e:
            return f"Error during interaction: {e}"

    def generate(self, story: str, guidelines: str, prompt_output_path: str = None, timestamp_context: str = None) -> Dict[str, Any]:
        # Note: We keep the example JSON in guidelines as it provides critical structure for Nivo charts and Camera shots

        print("⚖️ Checking and adjusting video durations in prompt for 30fps target...")
        story = self.adjust_durations_in_text(story)
        guidelines = self.adjust_durations_in_text(guidelines)

        local_fonts = self.get_local_fonts()

        full_prompt = (
            "You are a world-class Motion Graphics Director and Remotion V4 JSON Engineer. "
            "Your task is to generate an ULTRA MODERN, HIGH-END, and VIEWER-CENTRIC cinematic JSON manifest. "
            "The video must be top-notch and catchy, utilizing professional documentary motion design principles.\n\n"
            "CRITICAL TECHNICAL RULES:\n"
            "1. DATA ACCURACY (Nivo Charts):\n"
            "   - 'chart' overlays MUST have a valid 'data' array.\n"
            "   - Line Chart: [ { 'id': 'Metric Name', 'data': [ { 'x': 'Label', 'y': 123 }, ... ] } ]\n"
            "   - Bar Chart: [ { 'id': 'Metric Name', 'data': [ { 'x': 'Label', 'y': 123 }, ... ] } ]\n"
            "   - Ensure all numbers match the story (e.g. 2 crore = 20000000). Use realistic variations for historical data.\n"
            "2. PROFESSIONAL CINEMATOGRAPHY & PACING:\n"
            "   - USE PRESETS: For the best results, use 'preset': 'slow_push' or 'ken_burns' in the camera object.\n"
            "   - NO JUMPS: Every 'shot' in the camera array MUST target an overlay that has 'cameraFocus' defined.\n"
            "   - ZOOM CONSISTENCY: The 'zoom' value in a camera 'shot' MUST EXACTLY MATCH the 'zoom' value in the target overlay's 'cameraFocus' object to prevent visual jumps.\n"
            "   - ZOOM LIMITS: Keep 'zoom' between 1.1 and 1.8 for text, up to 2.2 for data details. NEVER exceed 3.0.\n"
            "   - TRANSITIONS & RESTING: 'inDuration' for shots should be 30-45 frames. CRITICAL: Ensure 'duration' - 'inDuration' is at least 45-60 frames (1.5-2s at 30fps) for the viewer to 'rest' on and read the content.\n"
            "3. DEPTH, LAYERING & POLISH:\n"
            "   - MANDATORY VIDEO BACKGROUNDS: Every scene MUST use 'background_type': 'video'.\n"
            "   - VIDEO PATH CONVENTION: Use 'video_path': 'renders/scene_SC_01.mp4' for the first scene, 'renders/scene_SC_02.mp4' for the second, and so on.\n"
            "   - MANDATORY AUDIO: Every scene MUST have 'audio_enabled': true.\n"
            "   - UNIQUE PROCEDURAL: If using procedural backgrounds, ensure 'procedural_config' is unique and non-repetitive per scene. Use modern, balanced colors.\n"
            "   - OVERLAY DENSITY: Do NOT crowd the screen. Number of overlays must be proportional to scene duration. Shorter scenes (<150 frames) should have fewer (1-2) focal overlays.\n"
            "   - SHAKE OFF: 'camera.shake.enabled' MUST be false by default. Only enable for extreme impact.\n"
            "   - BENGALI SUPPORT: For Bengali text, ALWAYS use 'splitMode': 'word'. NEVER use 'char' to avoid breaking clusters.\n"
            "   - OVERLAY DENSITY & PACING: Do NOT crowd the screen. Use a maximum of 1 focal overlay (Chart/UI/KPI) per 60 frames of scene duration. A scene with 180 frames should have at most 3 focal elements appearing at different times.\n"
            "   - SHOT COVERAGE: Every single focal overlay MUST have its own camera 'shot' in the 'shots' array. The camera must move to cover each element as it becomes active.\n"
            "   - DECORATIVE DEPTH: Use multiple 'shape' and 'graph' overlays at low zIndex (-20 to -40) with subtle animations (pulse, float) to create a dense, tech-forward background.\n"
            "4. CENTER ANCHORING, TYPOGRAPHY & CONCISE TEXT:\n"
            "   - ALL overlays are center-anchored. Position {x: 960, y: 540} is dead center.\n"
            f"   - DETECTED LOCAL FONTS: {local_fonts}\n"
            "   - SCRIPT-SPECIFIC FONTS: You MUST identify which of the detected fonts are Bangla and which are English. Use the Bangla font for all Bengali text and the English font for all English text in the 'font' field.\n"
            "   - CONCISE VIBE TEXT: 'text' overlay 'content' fields MUST be extremely concise (2-3 words maximum). Do NOT summarize the whole story; instead, capture the 'feeling' or 'vibe' of that specific moment.\n\n"
            f"SYSTEM GUIDELINES AND SCHEMA:\n{guidelines}\n\n"
            f"STORY AND SCENE REQUIREMENTS:\n{story}\n\n"
            f"WORD-LEVEL TIMESTAMPS (FRAMES @ 30FPS):\n{timestamp_context or 'No timestamps provided.'}\n\n"
            "3. CONTENT ACCURACY & SYNC:\n"
            "   - CRITICAL: Use the provided frame-based timestamps to set precise 'start' and 'duration' for focal overlays. These frames are already optimized for the 30fps project output.\n"
            "   - Use the story as a reference to pick the most impactful 2-3 words for the 'text' overlays.\n\n"
            "TASK:\nGenerate the complete JSON manifest. Ensure Bengali text is used where appropriate. "
            "Return ONLY the raw JSON object. No markdown, no preamble, no commentary."
        )

        # Save the prompt to a file if requested
        if prompt_output_path:
            os.makedirs(os.path.dirname(prompt_output_path), exist_ok=True)
            with open(prompt_output_path, 'w', encoding='utf-8') as f:
                f.write(full_prompt)
            print(f"📝 Prompt saved to: {prompt_output_path}")

        raw_output = self._interact_with_gemini(full_prompt)
        print(f"✅ Response received (Length: {len(raw_output)}).")

        try:
            # Robust JSON extraction
                # 1. Try to find content between the first { and the last }
                start_idx = raw_output.find('{')
                end_idx = raw_output.rfind('}')

                if start_idx != -1 and end_idx != -1:
                    json_str = raw_output[start_idx:end_idx+1]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        # 2. Try deep cleaning markdown and comments if simple extraction fails
                        cleaned = json_str
                        cleaned = re.sub(r'//.*$', '', cleaned, flags=re.MULTILINE) # Remove single line comments
                        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL) # Remove block comments
                        try:
                            return json.loads(cleaned)
                        except:
                            pass

                # 3. Fallback to regex if indices failed or were messy
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

                # 4. Final attempt: the raw output stripped
                return json.loads(raw_output.strip())

            finally:
                pass

def main():
    parser = argparse.ArgumentParser(description="Counterism Studio V4 JSON Maker (Playwright Gemini Edition)")
    parser.add_argument("--story", help="The story or topic for the video")
    parser.add_argument("--story-file", help="Path to a text file containing the story/topic")
    parser.add_argument("--output", required=True, help="Path to save remotion_render.json")
    parser.add_argument("--timestamp-output", help="Path to save word-level timestamps")
    parser.add_argument("--prompt-output", help="Path to save the generated prompt (remotion_prompt.txt)")
    parser.add_argument("--user-data-dir", help="Path to Chromium user data directory for persistent session")
    parser.add_argument("--no-headless", action="store_false", dest="headless", help="Run browser in non-headless mode")
    parser.add_argument("--drive-prompt", help="Path to the guideline_prompt.txt on Google Drive")
    parser.set_defaults(headless=True)

    args = parser.parse_args()

    # Determine the story source
    story = args.story
    if args.story_file and os.path.exists(args.story_file):
        with open(args.story_file, 'r', encoding='utf-8') as f:
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

    print(f"✨ Generating JSON for story via Gemini...")
    try:
        # Step 1: Generate word-level timestamps if requested
        timestamp_content = None
        if args.timestamp_output:
            timestamp_content = maker.generate_word_timestamps(story)
            os.makedirs(os.path.dirname(args.timestamp_output), exist_ok=True)
            with open(args.timestamp_output, 'w', encoding='utf-8') as f:
                f.write(timestamp_content)
            print(f"✅ Timestamps saved to: {args.timestamp_output}")

        # Step 2: Generate Manifest with timestamp context
        render_json = maker.generate(story, guidelines, prompt_output_path=args.prompt_output, timestamp_context=timestamp_content)

        # Cleanup browser
        maker.stop_browser()

        print("🛠️  Performing final frame-accurate duration synchronization...")
        render_json = maker.finalize_json_durations(render_json)

        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(render_json, f, indent=2, ensure_ascii=False)

        print(f"✅ Master JSON created successfully at: {args.output}")
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        exit(1)

if __name__ == "__main__":
    main()
