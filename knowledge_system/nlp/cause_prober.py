import urllib.request
import urllib.parse
import json
import re
from typing import List, Optional
from .semantic_model import Entity, Relation

class CauseProber:
    def __init__(self):
        # Semantic domain fallbacks to guarantee 100% stable, fast, non-LLM local cause associations
        self.domain_fallbacks = [
            {
                "keywords": ["city", "dhaka", "megacity", "crowded", "popul", "traffic", "jam", "urban", "ঢাকা", "জনবহুল", "যানজট", "শহর"],
                "causes": [
                    {"label": "Rapid Urbanization", "bn_label": "দ্রুত নগরায়ণ", "english": "Rapid Urbanization"},
                    {"label": "Infrastructure Deficit", "bn_label": "অবকাঠামোগত ঘাটতি", "english": "Infrastructure Deficit"},
                    {"label": "Rural Migration", "bn_label": "গ্রামীণ অভিবাসন", "english": "Rural Migration"},
                    {"label": "Vehicle Overload", "bn_label": "যানবাহন বৃদ্ধি", "english": "Vehicle Overload"}
                ]
            },
            {
                "keywords": ["pollut", "waste", "environ", "air", "water", "climate", "disaster", "flood", "দূষণ", "পরিবেশ", "বায়ু", "বর্জ্য", "দুর্যোগ"],
                "causes": [
                    {"label": "Industrial Emissions", "bn_label": "শিল্প নির্গমন", "english": "Industrial Emissions"},
                    {"label": "Unplanned Disposal", "bn_label": "পরিকল্পনাহীন বর্জ্য", "english": "Unplanned Disposal"},
                    {"label": "Deforestation", "bn_label": "বন উজাড়করণ", "english": "Deforestation"},
                    {"label": "Fossil Fuels", "bn_label": "জীবাশ্ম জ্বালানি", "english": "Fossil Fuels"}
                ]
            },
            {
                "keywords": ["money", "growth", "poverty", "employ", "business", "market", "economy", "crisis", "অর্থ", "প্রবৃদ্ধি", "দারিদ্র্য", "চাকরি", "বাজার"],
                "causes": [
                    {"label": "Resource Allocation", "bn_label": "সম্পদ বরাদ্দ", "english": "Resource Allocation"},
                    {"label": "Market Volatility", "bn_label": "বাজারের অস্থিরতা", "english": "Market Volatility"},
                    {"label": "Inflationary Pressure", "bn_label": "মুদ্রাস্ফীতির চাপ", "english": "Inflationary Pressure"},
                    {"label": "Economic Downturn", "bn_label": "অর্থনৈতিক মন্দা", "english": "Economic Downturn"}
                ]
            }
        ]

    def _is_bangla(self, text: str) -> bool:
        return any("\u0980" <= char <= "\u09FF" for char in str(text))

    def _extract_phrase_from_match(self, match_text: str, is_bn: bool) -> Optional[str]:
        """Cleans up the matched regex group and trims it to a robust 2-3 words phrase."""
        phrase = match_text.strip().strip(",.।;:()\"'-_")
        if not phrase:
            return None

        words = phrase.split()
        if not words:
            return None

        # Filter out common leading English prepositions / determiners
        if not is_bn:
            stop_words = {"the", "a", "an", "of", "and", "in", "on", "at", "to", "for", "with", "by", "from", "that", "which"}
            while words and words[0].lower() in stop_words:
                words.pop(0)

        if not words:
            return None

        # Limit to maximum of 3 words to preserve pristine UI layout
        max_words = min(len(words), 3)
        selected_words = words[:max_words]

        if not is_bn:
            # Clean capitalized nouns
            selected_words = [w.capitalize() for w in selected_words]

        return " ".join(selected_words)

    def _query_wikipedia_causes(self, entity_label: str, is_bn: bool) -> List[str]:
        """Dynamically queries Wikipedia search and extract APIs to extract causes via NLP pattern-matching."""
        lang = "bn" if is_bn else "en"
        causes = []
        try:
            # 1. Search Wikipedia for matching page title
            safe_query = urllib.parse.quote(entity_label)
            search_url = f"https://{lang}.wikipedia.org/w/api.php?action=query&list=search&srsearch={safe_query}&utf8=&format=json"
            req = urllib.request.Request(
                search_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) CRVE-DocumentaryEngine/4.0.0'}
            )
            title = None
            with urllib.request.urlopen(req, timeout=3) as res:
                data = json.loads(res.read().decode('utf-8'))
                search_results = data.get("query", {}).get("search", [])
                if search_results:
                    title = search_results[0]["title"]

            if not title:
                return []

            # 2. Query article extract (lead intro)
            safe_title = urllib.parse.quote(title)
            extract_url = f"https://{lang}.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&titles={safe_title}&format=json"
            req_extract = urllib.request.Request(
                extract_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) CRVE-DocumentaryEngine/4.0.0'}
            )
            extract_text = ""
            with urllib.request.urlopen(req_extract, timeout=3) as res:
                data = json.loads(res.read().decode('utf-8'))
                pages = data.get("query", {}).get("pages", {})
                for pid, pinfo in pages.items():
                    extract_text = pinfo.get("extract", "")
                    break

            if not extract_text:
                return []

            # 3. Segment into sentences and run NLP pattern-matching for causation
            sentences = re.split(r'[.।\n]', extract_text)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                if not is_bn:
                    # Matches "caused by [X]", "due to [X]", etc.
                    m = re.search(r'(?:caused by|due to|because of|result of|arising from|consequence of)\s+([a-zA-Z\s]{3,40})', sentence, re.IGNORECASE)
                    if m:
                        phrase = self._extract_phrase_from_match(m.group(1), is_bn=False)
                        if phrase and phrase not in causes:
                            causes.append(phrase)

                    # Matches "[X] leads to", "[X] causes", etc.
                    m2 = re.search(r'([a-zA-Z\s]{3,40})\s+(?:leads to|causes|contributes to|is a cause of)', sentence, re.IGNORECASE)
                    if m2:
                        phrase = self._extract_phrase_from_match(m2.group(1), is_bn=False)
                        if phrase and phrase not in causes:
                            causes.append(phrase)
                else:
                    # Bangla causal patterns
                    # Matches "[X] কারণে", "[X] ফলে", etc.
                    m = re.search(r'([^\s।]+(?:\s+[^\s।]+){0,2})\s+(?:কারণে|ফলে|দ্বারা সৃষ্ট|কারণে ঘটে)', sentence)
                    if m:
                        phrase = self._extract_phrase_from_match(m.group(1), is_bn=True)
                        if phrase and phrase not in causes:
                            causes.append(phrase)

                    # Matches "কারণসমূহ হলো [X]", "মূল কারণ [X]"
                    m2 = re.search(r'(?:কারণসমূহ|মূল কারণ|কারণ হলো)\s+([^\s।]+(?:\s+[^\s।]+){0,2})', sentence)
                    if m2:
                        phrase = self._extract_phrase_from_match(m2.group(1), is_bn=True)
                        if phrase and phrase not in causes:
                            causes.append(phrase)

        except Exception as e:
            print(f"Warning: Dynamic Wikipedia Cause extraction failed for '{entity_label}': {e}")

        return causes

    def probe_causes(self, scene_text: str, entities: List[Entity], next_scene_text: Optional[str] = None) -> List[dict]:
        """
        Dynamically extracts causing factors for the primary assertions in scene_text.
        No LLMs are used to guarantee high-performance non-blocking executions.
        """
        detected_causes = []
        is_bn = self._is_bangla(scene_text)

        # 1. Identify primary entity candidates in the scene (sort by importance)
        candidates = sorted(entities, key=lambda e: e.importance, reverse=True)
        candidate_labels = [c.label for c in candidates if len(c.label) > 2]

        # 2. Extract dynamically via Wikipedia
        for label in candidate_labels[:2]:  # Query at most top 2 entities to keep it fast
            wiki_causes = self._query_wikipedia_causes(label, is_bn)
            for wc in wiki_causes:
                # Deduplicate and append
                if not any(c["label"].lower() == wc.lower() for c in detected_causes):
                    detected_causes.append({
                        "label": wc,
                        "english": wc,
                        "search_trigger": [wc.lower()]
                    })
            if len(detected_causes) >= 3:
                break

        # 3. Fallback to Local Semantic Domain associations if Wikipedia API yields insufficient causes
        if len(detected_causes) < 3:
            text_lower = scene_text.lower()
            for domain in self.domain_fallbacks:
                if any(kw in text_lower for kw in domain["keywords"]):
                    for fallback in domain["causes"]:
                        lbl = fallback["bn_label"] if is_bn else fallback["label"]
                        if not any(c["label"].lower() == lbl.lower() for c in detected_causes):
                            detected_causes.append({
                                "label": lbl,
                                "english": fallback["english"],
                                "search_trigger": [lbl.lower(), fallback["english"].lower()]
                            })
                    if len(detected_causes) >= 4:
                        break

        # 4. Context-Aware Deduplication (Check against Next Scene text)
        if next_scene_text:
            next_text_lower = next_scene_text.lower()
            filtered_causes = []
            for cause in detected_causes:
                triggers = cause.get("search_trigger", []) + [cause["label"].lower(), cause["english"].lower()]
                already_described = any(trig in next_text_lower for trig in triggers)

                if not already_described:
                    filtered_causes.append(cause)
                else:
                    print(f"💡 Context Deduplicator: Excluded '{cause['label']}' from current scene as next scene describes/contains it.")
            detected_causes = filtered_causes

        # Enforce strict layout constraints: return top 2-4 causes max
        return detected_causes[:4]

    def inject_causes_to_scene(self, scene_idx: int, scene_model: any, next_scene_text: Optional[str] = None) -> None:
        """
        Modifies a SemanticSceneModel by probing and appending new cause Entities and Relations.
        """
        probed_reasons = self.probe_causes(scene_model.narration, scene_model.entities, next_scene_text)
        if not probed_reasons:
            return

        # Find the primary entity (Hero or most important concept) in the scene to connect causes to
        target_entity_id = None
        for entity in scene_model.entities:
            if entity.importance >= 2.0:
                target_entity_id = entity.id
                break

        # Fallback to first entity if no high-importance entity found
        if not target_entity_id and scene_model.entities:
            target_entity_id = scene_model.entities[0].id

        if not target_entity_id:
            root_label = "ঢাকা" if self._is_bangla(scene_model.narration) else "Dhaka"
            root_id = "e_root_baseline"
            scene_model.entities.append(Entity(
                id=root_id,
                label=root_label,
                type="map_marker",
                importance=2.0
            ))
            target_entity_id = root_id

        # Inject each probed cause as a new node and a relation
        entity_start_idx = len(scene_model.entities) + 1
        for i, cause in enumerate(probed_reasons):
            cause_node_id = f"e_cause_{scene_idx}_{entity_start_idx + i}"

            # Inject Cause Node
            scene_model.entities.append(Entity(
                id=cause_node_id,
                label=cause["label"],
                type="danger_core" if i % 2 == 0 else "abstract_core",
                importance=1.5,
                scale=1.0,
                emotion="intense" if i % 2 == 0 else "calm"
            ))

            # Inject Relation Link (with causes relationship type)
            relation_id = f"r_cause_{scene_idx}_{entity_start_idx + i}"
            scene_model.relations.append(Relation(
                id=relation_id,
                source_id=cause_node_id,
                target_id=target_entity_id,
                relationship="causes",
                importance=1.2,
                strength=1.0
            ))

        print(f"✅ Probed & Injected {len(probed_reasons)} cause-and-effect connections into Scene {scene_idx + 1}")
