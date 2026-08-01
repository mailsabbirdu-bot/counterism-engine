import json
import os
import time
import re
import math
import hashlib
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field

@dataclass
class KnowledgeItem:
    """Structured knowledge atomic unit."""
    id: str
    content: str
    category: str # layout, typography, motion, logic, variant
    tags: List[str]
    importance: float # 0.0 to 1.0
    frequency: int
    first_seen: str
    last_seen: str
    is_anti_pattern: bool = True
    success_rate_after_fix: float = 0.0
    patch_template: Optional[str] = None

class ProductionMemoryManager:
    """
    v2.0 Cognitive Retrieval Memory System.
    Distills, ranks, and retrieves production intelligence with context awareness.
    """

    CATEGORIES = ['layout', 'typography', 'motion', 'logic', 'variant', 'assets']

    def __init__(self, memory_path: str = "production_knowledge.json"):
        self.memory_path = memory_path
        self.knowledge_base: Dict[str, KnowledgeItem] = self._load_memory()

    def _load_memory(self) -> Dict[str, KnowledgeItem]:
        kb = {}
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for k_id, item in data.get('items', {}).items():
                        kb[k_id] = KnowledgeItem(**item)
            except Exception as e:
                print(f"⚠️ Memory Load Error: {e}")
        return kb

    def save_memory(self):
        export_data = {
            "version": "2.0",
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "items": {k_id: asdict(item) for k_id, item in self.knowledge_base.items()}
        }
        with open(self.memory_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)

    def record_finding(self, success: bool, score: int, errors: List[str], manifest: Optional[Dict[str, Any]] = None):
        """Distills findings into structured knowledge units."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # 1. Distill Failures (Anti-Patterns)
        new_err_patterns = []
        for err in errors:
            # Skip noise or generic info
            if "ASSETS: Video verified" in err or "Processing:" in err: continue
            p_id = self._process_error(err, timestamp)
            if p_id: new_err_patterns.append(p_id)

        # 2. Distill Successes (Reinforcement & Conflict Resolution)
        if success and score >= 90:
            # v2.0: If current run is successful, REDUCE weight of errors that WERE present
            # but are now resolved. This is the Self-Correction mechanism.
            for item in self.knowledge_base.values():
                if item.is_anti_pattern and item.id not in new_err_patterns:
                    # If this error didn't appear in a 90+ score run, it might be fixed.
                    item.success_rate_after_fix = min(1.0, item.success_rate_after_fix + 0.2)
                    item.importance *= 0.8 # Decay importance of "solved" problems

            if manifest:
                self._process_success(manifest, timestamp)

        # 3. Conflict Resolution & Cleanup
        self._prune_low_signal_knowledge()
        self.save_memory()

    def _process_error(self, err_msg: str, timestamp: str) -> Optional[str]:
        """Converts raw error into a structured KnowledgeItem."""
        patch = None
        if "REQUIRED PATCH:" in err_msg:
            parts = err_msg.split("REQUIRED PATCH:")
            err_msg = parts[0].strip()
            patch = parts[1].strip()

        # Normalize: Remove specific IDs/Names to find recurring patterns
        normalized = re.sub(r'\[SCENE_\d+\]', '', err_msg)
        normalized = re.sub(r"Overlay '.*?'", 'An overlay', normalized)
        normalized = re.sub(r"font '.*?'", 'a specific font', normalized)
        normalized = re.sub(r"shot \d+", 'a camera shot', normalized)
        normalized = re.sub(r"CRITICAL|ERROR|WARNING|INFO", '', normalized)
        normalized = normalized.strip(': ')

        if not normalized: return None

        # Categorize
        category = 'logic'
        if any(x in normalized.lower() for x in ['position', 'anchor', 'margin', 'offscreen', 'overlap', 'collision']): category = 'layout'
        elif any(x in normalized.lower() for x in ['font', 'size', 'typography', 'content']): category = 'typography'
        elif any(x in normalized.lower() for x in ['animation', 'motion', 'reveal', 'pacing']): category = 'motion'
        elif any(x in normalized.lower() for x in ['variant', 'type', 'config', 'data']): category = 'variant'

        # Generate unique stable ID for the pattern
        k_id = f"err_{hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:12]}"

        if k_id in self.knowledge_base:
            item = self.knowledge_base[k_id]
            item.frequency += 1
            item.last_seen = timestamp
            if patch: item.patch_template = patch
            # Anti-pattern becomes MORE important the more it happens
            item.importance = min(1.0, 0.4 + (item.frequency * 0.15))
            # But success counter-acts importance
            item.importance *= (1.0 - (item.success_rate_after_fix * 0.5))
            return k_id
        else:
            self.knowledge_base[k_id] = KnowledgeItem(
                id=k_id, content=normalized, category=category,
                tags=self._extract_tags(normalized), importance=0.45,
                frequency=1, first_seen=timestamp, last_seen=timestamp,
                is_anti_pattern=True, patch_template=patch
            )
            return k_id

    def _process_success(self, manifest: Dict[str, Any], timestamp: str):
        """Reinforces successful patterns."""
        # Placeholder for complex pattern extraction (e.g. successful layout clusters)
        pass

    def _extract_tags(self, text: str) -> List[str]:
        # Simple keyword extraction for context retrieval
        keywords = ['chart', 'indicator', 'text', 'hero', 'bangla', 'english', 'collision', 'depth', 'connector']
        return [kw for kw in keywords if kw in text.lower()]

    def _prune_low_signal_knowledge(self):
        """Keeps memory focused by removing low-importance or ancient noise."""
        if len(self.knowledge_base) < 50: return

        # Sort by importance and temporal relevance
        sorted_ids = sorted(
            self.knowledge_base.keys(),
            key=lambda k: self.knowledge_base[k].importance,
            reverse=True
        )
        # Keep top 40 items
        for k in sorted_ids[40:]:
            del self.knowledge_base[k]

    def get_prompt_injection(self, context_tags: List[str] = None) -> str:
        """Retrieves and ranks the most relevant knowledge for the current prompt."""
        if not self.knowledge_base: return ""

        # 1. Ranking Logic: Relevance + Importance + Temporal Decay
        now = time.time()
        ranked_items = []
        for item in self.knowledge_base.values():
            # Base importance
            score = item.importance

            # Temporal Decay (Knowledge from months ago is less relevant than recent failures)
            try:
                last_seen_ts = time.mktime(time.strptime(item.last_seen, "%Y-%m-%d %H:%M:%S"))
                days_since = (now - last_seen_ts) / (24 * 3600)
                decay = math.exp(-days_since / 30.0) # 30-day half-life for errors
                score *= decay
            except: pass

            # Contextual Relevance Boost
            if context_tags:
                matches = set(item.tags).intersection(set(context_tags))
                score += len(matches) * 0.3

            ranked_items.append((score, item))

        ranked_items.sort(key=lambda x: x[0], reverse=True)

        # 2. Retrieval: Select top 8 high-signal items (minimum score 0.2 to avoid noise)
        top_items = [it for s, it in ranked_items if s > 0.2][:8]

        if not top_items: return ""

        injection = "\n--- [PRODUCTION INTELLIGENCE: LEARNED FROM PAST ITERATIONS] ---\n"

        anti_patterns = [it for it in top_items if it.is_anti_pattern]
        if anti_patterns:
            injection += "⚠️ CRITICAL ERRORS TO AVOID (HIGH FREQUENCY):\n"
            for it in anti_patterns:
                line = f"- {it.content}"
                if it.patch_template:
                    line += f" -> [FIX TEMPLATE]: {it.patch_template}"
                injection += line + "\n"

        success_patterns = [it for it in top_items if not it.is_anti_pattern]
        if success_patterns:
            injection += "\n✅ PROVEN SUCCESSFUL PATTERNS:\n"
            for it in success_patterns:
                injection += f"- {it.content}\n"

        return injection
