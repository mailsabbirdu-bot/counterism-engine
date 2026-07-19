import sys
import json
import re
from typing import List
from .normalizer import normalize_text
from .semantic_model import SemanticSceneModel, Entity, Action, Quantity, TemporalExpression, Relation
from .graph_builder import GraphBuilder

class SemanticEngine:
    def __init__(self, lang=None):
        self.default_lang = lang

    def _split_scenes(self, text: str) -> List[tuple]:
        # Regex for markers like 'দৃশ্য ১', 'Scene 1', 'দৃশ্য 1'
        pattern = r'(?:दृश्य\s*[০-৯\d]+|Scene\s*\d+|দৃশ্য\s*[০-৯\d]+:?|Scene\s*\d+:?)'
        markers = re.findall(pattern, text)
        segments = re.split(pattern, text)

        scenes = []
        for i, marker in enumerate(markers):
            idx = i + 1
            if idx < len(segments):
                scene_text = segments[idx].strip()
                scene_text = re.sub(r'^[:।\s]+', '', scene_text)
                if scene_text:
                    scenes.append((marker, scene_text))

        if not scenes: # Fallback if no markers found
            scenes.append(("scene_1", text))
        return scenes

    def _is_bangla(self, text: str) -> bool:
        return any("\u0980" <= char <= "\u09FF" for char in text)

    def _run_offline_fallback(self, all_scene_models: List[SemanticSceneModel]) -> None:
        """Lightweight, offline-first rule-based fallback to populate scenes without any external models."""
        for idx, model in enumerate(all_scene_models):
            is_bn = self._is_bangla(model.narration)

            # Simple Entity Extraction based on Capitalized words or basic Bangla words
            extracted_labels = []
            if is_bn:
                # Extract 2-3 significant Bangla words
                words = [w for w in re.findall(r'[\u0980-\u09FF]+', model.narration) if len(w) > 2]
                extracted_labels = words[:2]
                if not extracted_labels:
                    extracted_labels = ["ঢাকা"]
            else:
                # Extract English proper nouns
                pns = re.findall(r'\b[A-Z][a-z]+\b', model.narration)
                extracted_labels = [p for p in pns if p not in {"In", "The", "Because", "On"}]
                if not extracted_labels:
                    extracted_labels = ["Dhaka"]

            # 1. Inject primary entities
            entity_ids = []
            for e_idx, lbl in enumerate(extracted_labels[:2]):
                e_id = f"e_{idx}_{e_idx}"
                model.entities.append(Entity(
                    id=e_id,
                    label=lbl,
                    type="hero" if e_idx == 0 else "concept",
                    importance=2.5 if e_idx == 0 else 1.5,
                    emotion="calm",
                    scale=1.0
                ))
                entity_ids.append(e_id)

            primary_target = entity_ids[0] if entity_ids else "e_root_baseline"
            if not entity_ids:
                root_label = "ঢাকা" if is_bn else "Dhaka"
                model.entities.append(Entity(id="e_root_baseline", label=root_label, type="hero", importance=2.5))

            # 2. Inject local rule-based causes based on keyword matches
            causes_list = []
            text_lower = model.narration.lower()
            if any(kw in text_lower for kw in ["growth", "revenue", "apple", "প্রবৃদ্ধি", "অর্থ"]):
                causes_list = [
                    {"label": "বাজারের অস্থিরতা" if is_bn else "Market volatility", "english": "Market volatility", "emotion": "intense"},
                    {"label": "মুদ্রাস্ফীতির চাপ" if is_bn else "Inflationary pressures", "english": "Inflationary pressures", "emotion": "calm"},
                    {"label": "সম্পদের অপব্যবহার" if is_bn else "Resource misallocation", "english": "Resource misallocation", "emotion": "intense"},
                    {"label": "অর্থনৈতিক মন্দা" if is_bn else "Economic recession", "english": "Economic recession", "emotion": "calm"}
                ]
            elif any(kw in text_lower for kw in ["city", "dhaka", "populous", "ঢাকা", "জনবহুল", "শহর"]):
                causes_list = [
                    {"label": "দ্রুত নগরায়ণ" if is_bn else "Rapid urbanization", "english": "Rapid urbanization", "emotion": "intense"},
                    {"label": "গ্রাম-শহর অভিবাসন" if is_bn else "Rural-urban migration", "english": "Rural-urban migration", "emotion": "calm"},
                    {"label": "কেন্দ্রীভূত প্রশাসন" if is_bn else "Centralized administration", "english": "Centralized administration", "emotion": "intense"},
                    {"label": "কর্মসংস্থান" if is_bn else "Employment opportunities", "english": "Employment opportunities", "emotion": "calm"}
                ]
            else:
                causes_list = [
                    {"label": "গ্রিনহাউস গ্যাস নির্গমন" if is_bn else "Greenhouse gas emissions", "english": "Greenhouse gas emissions", "emotion": "intense"},
                    {"label": "বন উজাড়করণ" if is_bn else "Deforestation", "english": "Deforestation", "emotion": "calm"},
                    {"label": "বৈশ্বিক তাপমাত্রা বৃদ্ধি" if is_bn else "Rising global temperature", "english": "Rising global temperature", "emotion": "intense"},
                    {"label": "সমুদ্রপৃষ্ঠের উচ্চতা বৃদ্ধি" if is_bn else "Rising sea levels", "english": "Rising sea levels", "emotion": "calm"}
                ]

            # Append causes and relations
            e_start_idx = len(model.entities) + 1
            for c_idx, cause in enumerate(causes_list[:4]):
                cause_node_id = f"e_cause_{idx}_{e_start_idx + c_idx}"
                model.entities.append(Entity(
                    id=cause_node_id,
                    label=cause["label"],
                    type="danger_core" if c_idx % 2 == 0 else "abstract_core",
                    importance=1.5,
                    scale=1.0,
                    emotion=cause["emotion"]
                ))
                model.relations.append(Relation(
                    id=f"r_cause_{idx}_{e_start_idx + c_idx}",
                    source_id=cause_node_id,
                    target_id=primary_target,
                    relationship="causes",
                    importance=1.2,
                    strength=1.0
                ))

            # Scene-level metadata fallback
            model.scene_type = "trend" if idx == 0 else "conflict"
            model.emotional_tone = "calm" if idx == 0 else "intense"

    def process(self, text: str) -> dict:
        # 1. Normalization
        text = normalize_text(text)

        # 2. Scene Splitting
        scene_segments = self._split_scenes(text)

        # 3. Process Scene Skeletons
        all_scene_models = []
        for idx, (scene_marker, scene_text) in enumerate(scene_segments):
            s_id = f"SCENE_{idx + 1}"
            model = SemanticSceneModel(
                scene_id=s_id,
                narration=scene_text,
                entities=[],
                actions=[],
                quantities=[],
                temporal_expressions=[],
                relations=[],
                scene_type="trend",
                emotional_tone="calm"
            )
            all_scene_models.append(model)

        # 4. Trigger Unified Gemini NLP Extraction or Fallback
        from .cause_prober import CauseProber
        prober = CauseProber()
        interaction_result = prober.probe_and_inject_all(all_scene_models)

        if interaction_result.get("status") == "success":
            # Map Gemini results back to our Pydantic objects
            data = interaction_result["data"]
            for s_data in data.get("scenes", []):
                s_id = s_data.get("scene_id")
                if s_id:
                    # Clean/normalize scene ID format
                    s_num = re.search(r'(\d+)', str(s_id)).group(1)
                    target_id = f"SCENE_{s_num}"

                    # Find matching model
                    matching_model = next((m for m in all_scene_models if m.scene_id == target_id), None)
                    if matching_model:
                        matching_model.scene_type = s_data.get("scene_type", "trend")
                        matching_model.emotional_tone = s_data.get("emotional_tone", "calm")

                        # Populate Entities with strict dict validation and word-length trimming
                        for ent in s_data.get("entities", []):
                            if not isinstance(ent, dict):
                                continue

                            # Trim label strictly to 2-3 words maximum
                            label = ent.get("label", "")
                            words = label.split()
                            if len(words) > 3:
                                label = " ".join(words[:3])

                            matching_model.entities.append(Entity(
                                id=ent.get("id"),
                                label=label,
                                type=ent.get("type", "concept"),
                                importance=ent.get("importance", 1.0),
                                emotion=ent.get("emotion"),
                                scale=ent.get("scale", 1.0),
                                attributes=ent.get("attributes", {})
                            ))
                        # Populate Actions with strict dict validation
                        for act in s_data.get("actions", []):
                            if not isinstance(act, dict):
                                continue
                            matching_model.actions.append(Action(
                                id=act.get("id"),
                                label=act.get("label"),
                                subject_id=act.get("subject_id"),
                                object_id=act.get("object_id"),
                                importance=act.get("importance", 1.0)
                            ))
                        # Populate Quantities with strict dict validation
                        for q in s_data.get("quantities", []):
                            if not isinstance(q, dict):
                                continue
                            matching_model.quantities.append(Quantity(
                                value=q.get("value", 0.0),
                                unit=q.get("unit"),
                                label=q.get("label", ""),
                                entity_id=q.get("entity_id")
                            ))
                        # Populate Temporals with strict dict validation
                        for t in s_data.get("temporal_expressions", []):
                            if not isinstance(t, dict):
                                continue
                            matching_model.temporal_expressions.append(TemporalExpression(
                                label=t.get("label"),
                                value=t.get("value"),
                                type=t.get("type", "point")
                            ))
                        # Populate Relations with strict dict validation
                        for rel in s_data.get("relations", []):
                            if not isinstance(rel, dict):
                                continue
                            matching_model.relations.append(Relation(
                                id=rel.get("id"),
                                source_id=rel.get("source_id"),
                                target_id=rel.get("target_id"),
                                relationship=rel.get("relationship"),
                                importance=rel.get("importance", 1.0),
                                strength=rel.get("strength", 1.0)
                            ))
        else:
            # Run our lightweight, high-speed, zero-fail offline fallback
            self._run_offline_fallback(all_scene_models)

        # 5. Build Unified Multi-Scene graph and enforce word constraints on fallback labels too
        for model in all_scene_models:
            for ent in model.entities:
                words = ent.label.split()
                if len(words) > 3:
                    ent.label = " ".join(words[:3])

        self.graph_builder = GraphBuilder()
        G = self.graph_builder.build_multi(all_scene_models)
        graph_data = self.graph_builder.to_json(G)

        return {
            "scenes": [m.dict() for m in all_scene_models],
            "graph": graph_data
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m semantic_engine.main \"Your narration text here\"")
        return

    text = sys.argv[1]
    engine = SemanticEngine()
    result = engine.process(text)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
