import os
import json
import argparse
import google.generativeai as genai
from typing import Dict, Any

class RemotionJsonMaker:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Using gemini-1.5-flash for speed and high context window (perfect for JSON generation)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

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
        prompt = f"""
{guidelines}

--- USER STORY/TOPIC ---
{story}

--- TASK ---
Generate a 'remotion_render.json' based on the story above.
Follow all engine rules:
- ALL overlays centered at (960, 540).
- Use 'shots' for camera movement.
- Depth values for parallax (-500 to 500).
- Valid overlay types: text, ui_panel, chart, graph, shape, video, image.
- Ensure 'scene_id' is unique.

Return ONLY valid JSON.
"""
        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            )
        )

        return json.loads(response.text)

def main():
    parser = argparse.ArgumentParser(description="Counterism Studio V4 JSON Maker")
    parser.add_argument("--story", required=True, help="The story or topic for the video")
    parser.add_argument("--api-key", required=True, help="Gemini API Key")
    parser.add_argument("--output", required=True, help="Path to save remotion_render.json")

    args = parser.parse_args()

    maker = RemotionJsonMaker(args.api_key)

    # Paths are hardcoded for the specific Colab environment requested
    local_guideline = "../guideline.md"
    local_prompt = "../guideline_prompt.txt"
    drive_prompt = "/content/drive/MyDrive/Counterism_Studio_V4/manifests/guideline_prompt.txt"

    print("📋 Loading guidelines...")
    guidelines = maker.load_guidelines(local_guideline, local_prompt, drive_prompt)

    print(f"🧠 Generating JSON for story: {args.story[:50]}...")
    try:
        render_json = maker.generate(args.story, guidelines)

        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(render_json, f, indent=2)

        print(f"✅ Master JSON created successfully at: {args.output}")
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        exit(1)

if __name__ == "__main__":
    main()
