import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from semantic_engine.main import SemanticEngine

def test_engine():
    engine = SemanticEngine()

    test_cases = [
        "In 2024, Apple Inc reported a 15% growth in revenue, reaching 50 billion dollars.",
        "The city of New York is part of the USA, and it is located on the East Coast.",
        "Because of the intense crisis, the population decreased by 20% in just one year."
    ]

    for i, text in enumerate(test_cases):
        print(f"\n--- Test Case {i+1} ---")
        print(f"Narration: {text}")
        result = engine.process(text, scene_id=f"test_scene_{i+1}")
        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_engine()
