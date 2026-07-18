import urllib.request
import urllib.parse
import json
import re
from typing import List, Optional
from .semantic_model import Entity, Relation

class CauseProber:
    def __init__(self):
        # High-Fidelity Pre-seeded Semantic Database for deterministic, premium quality Bangla/English causes
        self.preseeded_db = {
            "megacity": {
                "keywords": ["মেগাসিটি", "ক্রাউডেড", "জনবহুল", "ঢাকা", "megacity", "crowded", "popul", "dhaka"],
                "causes": [
                    {"label": "নদী ভাঙন", "english": "River Erosion", "search_trigger": ["নদী", "ভাঙন", "erosion", "river"]},
                    {"label": "কর্মসংস্থান", "english": "Employment", "search_trigger": ["কর্মসংস্থান", "চাকরি", "job", "employment"]},
                    {"label": "উন্নত চিকিৎসা", "english": "Better Healthcare", "search_trigger": ["চিকিৎসা", "হাসপাতাল", "healthcare", "medical"]},
                    {"label": "গ্রামীণ দারিদ্র্য", "english": "Rural Poverty", "search_trigger": ["দারিদ্র্য", "poverty", "rural"]}
                ]
            },
            "pollution": {
                "keywords": ["দূষণ", "পরিবেশ", "বায়ু", "বর্জ্য", "pollution", "air", "waste", "environ"],
                "causes": [
                    {"label": "যানবাহনের ধোঁয়া", "english": "Vehicle Smoke", "search_trigger": ["যানবাহন", "ধোঁয়া", "smoke", "vehicle"]},
                    {"label": "ইটভাটা", "english": "Brick Kilns", "search_trigger": ["ইটভাটা", "ভাটা", "brick", "kiln"]},
                    {"label": "শিল্প বর্জ্য", "english": "Industrial Waste", "search_trigger": ["শিল্প", "বর্জ্য", "industrial", "waste"]},
                    {"label": "প্লাস্টিক ব্যবহার", "english": "Plastic Usage", "search_trigger": ["প্লাস্টিক", "plastic"]}
                ]
            },
            "traffic": {
                "keywords": ["জ্যাম", "যানজট", "রাস্তা", "পথ", "traffic", "jam", "congest", "road"],
                "causes": [
                    {"label": "ত্রুটিপূর্ণ পরিকল্পনা", "english": "Faulty Planning", "search_trigger": ["পরিকল্পনা", "planning"]},
                    {"label": "অতিরিক্ত রিকশা", "english": "Excessive Rickshaws", "search_trigger": ["রিকশা", "rickshaw"]},
                    {"label": "সংকীর্ণ রাস্তা", "english": "Narrow Roads", "search_trigger": ["সংকীর্ণ", "রাস্তা", "narrow", "road"]},
                    {"label": "অবৈধ পার্কিং", "english": "Illegal Parking", "search_trigger": ["পার্কিং", "parking"]}
                ]
            },
            "climate": {
                "keywords": ["জলবায়ু", "দুর্যোগ", "বন্যা", "ঝড়", "climate", "disaster", "flood", "storm"],
                "causes": [
                    {"label": "কার্বন নির্গমন", "english": "Carbon Emission", "search_trigger": ["কার্বন", "emission", "carbon"]},
                    {"label": "বন উজাড়করণ", "english": "Deforestation", "search_trigger": ["বন", "উজাড়", "deforest"]},
                    {"label": "জীবাশ্ম জ্বালানি", "english": "Fossil Fuels", "search_trigger": ["জীবাশ্ম", "জ্বালানি", "fossil", "fuel"]},
                    {"label": "বৈশ্বिक উষ্ণায়ন", "english": "Global Warming", "search_trigger": ["উষ্ণায়ন", "warming", "global"]}
                ]
            }
        }

    def _is_bangla(self, text: str) -> bool:
        return any("\u0980" <= char <= "\u09FF" for char in str(text))

    def _query_wikipedia_opensearch(self, query: str, lang: str = "bn") -> List[str]:
        """
        Dynamically queries Wikipedia API to collect potential keywords if none of the pre-seeded terms match.
        """
        try:
            safe_query = urllib.parse.quote(query)
            url = f"https://{lang}.wikipedia.org/w/api.php?action=opensearch&search={safe_query}&limit=3&namespace=0&format=json"
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) CRVE-DocumentaryEngine/4.0.0'}
            )
            with urllib.request.urlopen(req, timeout=3) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                if len(res_data) > 1:
                    titles = res_data[1]
                    # return titles that have 2-3 words maximum to protect layout
                    filtered_titles = []
                    for t in titles:
                        words = t.split()
                        if 1 <= len(words) <= 3:
                            filtered_titles.append(t)
                    return filtered_titles
        except Exception as e:
            print(f"Warning: Wikipedia query failed: {e}")
        return []

    def probe_causes(self, scene_text: str, next_scene_text: Optional[str] = None) -> List[dict]:
        """
        Probes the causes behind a claim in the scene text.
        Returns a list of cause dicts containing {'label': '...', 'english': '...'}
        """
        detected_causes = []
        text_lower = scene_text.lower()
        is_bn = self._is_bangla(scene_text)

        # 1. Search Pre-seeded high fidelity DB first
        matched_category = None
        for category, config in self.preseeded_db.items():
            if any(kw in text_lower for kw in config["keywords"]):
                matched_category = category
                # Clone causes list
                detected_causes = [dict(c) for c in config["causes"]]
                break

        # 2. Context-Aware Deduplication (Next Scene Check)
        if next_scene_text:
            next_text_lower = next_scene_text.lower()
            filtered_causes = []
            for cause in detected_causes:
                # Check if cause label, english representation, or search triggers appear in the next scene
                triggers = cause.get("search_trigger", []) + [cause["label"].lower(), cause["english"].lower()]
                already_described = any(trig in next_text_lower for trig in triggers)

                if not already_described:
                    filtered_causes.append(cause)
                else:
                    print(f"💡 Context Deduplicator: Excluded '{cause['label']}' from current scene as next scene describes/contains it.")
            detected_causes = filtered_causes

        # 3. Dynamic Wikipedia Fallback if no preseeded match or too few causes left
        if len(detected_causes) < 2:
            # Extract possible noun phrases or words of length > 3 to query wikipedia
            words = [w for w in re.findall(r'\b\w+\b', scene_text) if len(w) > 3]
            lang = "bn" if is_bn else "en"
            for w in words[:2]:
                wiki_matches = self._query_wikipedia_opensearch(w, lang=lang)
                for match in wiki_matches:
                    if not any(c["label"] == match for c in detected_causes):
                        detected_causes.append({
                            "label": match,
                            "english": match,
                            "search_trigger": [match.lower()]
                        })

        # 4. Enforce strict constraints: top 2-4 causes max
        final_causes = detected_causes[:4]

        # Ensure naming is short (2-3 words max)
        for cause in final_causes:
            words = cause["label"].split()
            if len(words) > 3:
                cause["label"] = " ".join(words[:3])

        return final_causes

    def inject_causes_to_scene(self, scene_idx: int, scene_model: any, next_scene_text: Optional[str] = None) -> None:
        """
        Modifies a SemanticSceneModel by probing and appending new cause Entities and Relations.
        """
        probed_reasons = self.probe_causes(scene_model.narration, next_scene_text)
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
            # If no entities exist, create a central baseline concept node
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

            # Inject Cause Node (with customizable dynamic parameters)
            scene_model.entities.append(Entity(
                id=cause_node_id,
                label=cause["label"],
                type="danger_core" if i % 2 == 0 else "abstract_core",
                importance=1.5,
                scale=1.0,
                emotion="intense" if i % 2 == 0 else "calm"
            ))

            # Inject Relation Link (with causes relationship type so it triggers multi-pass electric waves)
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
