import os
import json
import argparse
import torch
import re
from transformers import pipeline
from typing import Dict, Any

class RemotionJsonMaker:
    def __init__(self, model_id: str = "meta-llama/Llama-3.2-1B-Instruct"):
        print(f"Loading local model: {model_id} (CPU optimized)...")
        # Use CPU, fp32 or bfloat16 depending on availability. On Colab CPU, float32 is safest.
        self.pipe = pipeline(
            "text-generation",
            model=model_id,
            torch_dtype=torch.float32,
            device_map="cpu",
            clean_up_tokenization_spaces=True
        )

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
        # Truncate story and guidelines to prevent context bloat on CPU
        # 1.5B/1B models have limited context attention on CPU.
        # We cap at ~3000 tokens (approx 12000 chars) total.
        max_chars = 6000
        truncated_guidelines = guidelines[-max_chars:] # Keep the end (most specific parts)
        truncated_story = story[:max_chars] # Keep the beginning (main story)

        messages = [
            {"role": "system", "content": "You are a specialized JSON generator. Return ONLY raw JSON."},
            {"role": "user", "content": f"{truncated_guidelines}\n\nSTORY:\n{truncated_story}\n\nTASK:\nGenerate 'remotion_render.json' for the story. Use the engine rules. Return ONLY JSON."}
        ]

        # Use the pipeline to generate text
        print("🧠 Running local inference (this usually takes 2-5 minutes on CPU)...")
        outputs = self.pipe(
            messages,
            max_new_tokens=1500,
            do_sample=True,
            temperature=0.1, # Low temperature for consistency
        )

        raw_output = outputs[0]["generated_text"][-1]["content"]

        # Extract JSON from potential markdown blocks
        json_match = re.search(r'(\{.*\})', raw_output, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                # Try cleaning it up if it's slightly messy
                cleaned = raw_output.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                return json.loads(cleaned)
        else:
            return json.loads(raw_output)

def main():
    parser = argparse.ArgumentParser(description="Counterism Studio V4 JSON Maker (Local LLM)")
    parser.add_argument("--story", help="The story or topic for the video")
    parser.add_argument("--story-file", help="Path to a text file containing the story/topic")
    parser.add_argument("--output", required=True, help="Path to save remotion_render.json")
    parser.add_argument("--model", default="meta-llama/Llama-3.2-1B-Instruct", help="HuggingFace Model ID")
    parser.add_argument("--hf-token", help="HuggingFace API Token (optional)")

    args = parser.parse_args()

    if args.hf_token:
        os.environ["HF_TOKEN"] = args.hf_token

    # Determine the story source
    story = args.story
    if args.story_file and os.path.exists(args.story_file):
        with open(args.story_file, 'r') as f:
            story = f.read()

    if not story:
        print("❌ Error: No story provided. Use --story or --story-file.")
        exit(1)

    maker = RemotionJsonMaker(args.model)

    # Paths are hardcoded for the specific Colab environment
    local_guideline = "../guideline.md"
    local_prompt = "../guideline_prompt.txt"
    # Drive prompt is excluded from guidelines if it's the story source to avoid redundancy
    drive_prompt = "/content/drive/MyDrive/Counterism_Studio_V4/manifests/guideline_prompt.txt"

    if args.story_file == drive_prompt:
        drive_prompt = "" # Prevent loading same 11k file twice

    print("📋 Loading guidelines...")
    guidelines = maker.load_guidelines(local_guideline, local_prompt, drive_prompt)

    print(f"✨ Generating JSON for story of length {len(story)}...")
    try:
        render_json = maker.generate(story, guidelines)

        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(render_json, f, indent=2)

        print(f"✅ Master JSON created successfully at: {args.output}")
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        # Log the raw output if failed to help debug
        exit(1)

if __name__ == "__main__":
    main()
