import json
import os
import time
from typing import Dict, Any, List, Optional

class ProductionMemoryManager:
    """
    Handles persistent knowledge distillation for the Cinematic Perception Engine.
    Converts iteration history into actionable 'Lessons Learned' for future prompts.
    """

    def __init__(self, memory_path: str = "production_knowledge.json"):
        self.memory_path = memory_path
        self.knowledge = self._load_memory()

    def _load_memory(self) -> Dict[str, Any]:
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass

        return {
            "version": "1.0",
            "last_updated": None,
            "anti_patterns": [], # Common AI mistakes (hallucinated variants, wrong keys)
            "best_practices": [], # Successful patterns (good composition, timing)
            "style_lessons": {}, # Project-specific style refinements
            "error_stats": {} # Track frequency of specific QA errors
        }

    def save_memory(self):
        self.knowledge['last_updated'] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.memory_path, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge, f, indent=2)

    def record_finding(self, success: bool, score: int, errors: List[str], manifest: Optional[Dict[str, Any]] = None):
        """Distills knowledge from a generation iteration."""
        if not errors and success and score >= 90:
            self._distill_success(manifest)
        elif errors:
            self._distill_failure(errors)

        self.save_memory()

    def _distill_failure(self, errors: List[str]):
        """Converts QA errors into Anti-Patterns."""
        for err in errors:
            # Clean error string (remove scene IDs and specific IDs to generalize)
            clean_err = re.sub(r'\[SCENE_\d+\]', '', err).strip()
            clean_err = re.sub(r"Overlay '.*?'", 'An overlay', clean_err)

            # Update stats
            self.knowledge['error_stats'][clean_err] = self.knowledge['error_stats'].get(clean_err, 0) + 1

            # If error is frequent, promote to anti-pattern
            if self.knowledge['error_stats'][clean_err] >= 2:
                if clean_err not in self.knowledge['anti_patterns']:
                    self.knowledge['anti_patterns'].append(clean_err)

        # Keep only top 15 anti-patterns to stay concise
        self.knowledge['anti_patterns'] = self.knowledge['anti_patterns'][-15:]

    def _distill_success(self, manifest: Dict[str, Any]):
        """Reinforces successful patterns from high-scoring manifests."""
        if not manifest: return

        # Extract generalized best practices (e.g. typical font sizes used for success)
        # This is a placeholder for more complex analysis if needed
        pass

    def get_prompt_injection(self) -> str:
        """Returns a string formatted for Gemini prompt injection."""
        if not self.knowledge['anti_patterns'] and not self.knowledge['best_practices']:
            return ""

        injection = "\n--- [PAST PRODUCTION MEMORY: DO NOT REPEAT THESE MISTAKES] ---\n"
        if self.knowledge['anti_patterns']:
            injection += "CRITICAL: Past attempts failed due to these errors. Ensure you avoid them:\n"
            for ap in self.knowledge['anti_patterns']:
                injection += f"- {ap}\n"

        if self.knowledge['best_practices']:
            injection += "\nSUCCESSFUL PATTERNS TO FOLLOW:\n"
            for bp in self.knowledge['best_practices']:
                injection += f"- {bp}\n"

        return injection

import re # Needed for distill_failure
