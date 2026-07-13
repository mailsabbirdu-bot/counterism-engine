import os
import subprocess
import json
import sys

# Dhaka Megacity Script
STORY = """
দৃশ্য ১: আকাশ থেকে ঢাকা শহরকে দেখা যাচ্ছে। এটি বিশ কোটির এক মেগাসিটি।
দৃশ্য ২: বিশ কোটি মানুষ প্রতিনিয়ত কংক্রিটের পাহাড় বানাচ্ছে।
দৃশ্য ৩: মানুষের এই বিশাল সাম্রাজ্যের নিচে লুকিয়ে আছে এক ভয়ঙ্কর বিপদ। একে বলা হয় 'জিওলজিক্যাল টাইমবোম্ব'।
দৃশ্য ৪: জিওলজিক্যাল ক্লক টিকটিক শব্দ করে চলছে। আমাদের পায়ের নিচের মাটি ধীরে ধীরে সরে যাচ্ছে।
"""

def run_cmd(cmd, name):
    print(f"\n🚀 STEP: {name}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED: {name}")
        print(e.stderr)
        sys.exit(1)

def main():
    # Setup directories
    os.makedirs("semantic_visualizer/input", exist_ok=True)
    os.makedirs("semantic_visualizer/output", exist_ok=True)

    # 1. RUN SEMANTIC ENGINE
    # We use grep to filter out non-JSON log lines from main.py output
    output = run_cmd(f'python3 -m semantic_engine.main "{STORY}" | grep -v "Initializing" | grep -v "Stanza" | grep -v "PydanticDeprecated"', "Semantic NLP Extraction")

    try:
        data = json.loads(output)
        with open("semantic_visualizer/input/semantic_model.json", "w", encoding="utf-8") as f:
            json.dump(data['scenes'], f, indent=2, ensure_ascii=False)
        with open("semantic_visualizer/input/knowledge_graph.json", "w", encoding="utf-8") as f:
            json.dump(data['graph'], f, indent=2, ensure_ascii=False)
        print("✅ NLP data saved to semantic_visualizer/input/")
    except Exception as e:
        print(f"❌ Failed to parse NLP output: {e}")
        print("Output was:", output)
        sys.exit(1)

    # 2. RUN SEMANTIC VISUALIZER (DIRECTOR BRAIN)
    run_cmd("PYTHONPATH=. python3 semantic_visualizer/main.py", "Cinematic Planning (Director Brain)")
    print("✅ Visualization plan generated: semantic_visualizer/output/visualization_plan.json")

    # 3. RUN REMOTION ADAPTER (FINAL MANIFEST)
    run_cmd("PYTHONPATH=. python3 semantic_visualizer/core/remotion_adapter.py", "Remotion Manifest Adaptation")
    print("✅ Remotion manifest generated: remotion_render_crve.json")

    # 4. SUMMARY
    print("\n" + "="*50)
    print("🏆 FULL PIPELINE DEMO COMPLETE")
    print("="*50)
    print("Next steps:")
    print("- Read 'TESTING.md' for Remotion rendering instructions.")
    print("- Inspect 'semantic_visualizer/output/visualization_plan.json' for directorial decisions.")

if __name__ == "__main__":
    main()
