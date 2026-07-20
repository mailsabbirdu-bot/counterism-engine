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
        pattern = r'(?:দৃশ্য\s*[০-৯\d]+|Scene\s*\d+|দৃশ্য\s*[০-৯\d]+:?|Scene\s*\d+:?)'
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
        """Lightweight, offline-first rule-based fallback to populate scenes with exactly 2 to 3 causes."""
        for idx, model in enumerate(all_scene_models):
            is_bn = self._is_bangla(model.narration)

            # Simple Entity Extraction based on Capitalized words or basic Bangla words
            extracted_labels = []
            if is_bn:
                words = [w for w in re.findall(r'[\u0980-\u09FF]+', model.narration) if len(w) > 2]
                extracted_labels = words[:2]
                if not extracted_labels:
                    extracted_labels = ["ঢাকা"]
            else:
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

            # 2. Inject local rule-based causes based on keyword matches (Strictly 2 to 3 causes)
            causes_list = []
            text_lower = model.narration.lower()
            if any(kw in text_lower for kw in ["growth", "revenue", "apple", "প্রবৃদ্ধি", "অর্থ"]):
                causes_list = [
                    {"label": "বাজারের অস্থিরতা" if is_bn else "Market volatility", "english": "Market volatility", "emotion": "intense"},
                    {"label": "মুদ্রাস্ফীতির চাপ" if is_bn else "Inflationary pressures", "english": "Inflationary pressures", "emotion": "calm"},
                    {"label": "অর্থনৈতিক মন্দা" if is_bn else "Economic recession", "english": "Economic recession", "emotion": "calm"}
                ]
            elif any(kw in text_lower for kw in ["city", "dhaka", "populous", "ঢাকা", "জনবহুল", "শহর"]):
                causes_list = [
                    {"label": "দ্রুত নগরায়ণ" if is_bn else "Rapid urbanization", "english": "Rapid urbanization", "emotion": "intense"},
                    {"label": "গ্রাম-শহর অভিবাসন" if is_bn else "Rural-urban migration", "english": "Rural-urban migration", "emotion": "calm"},
                    {"label": "কর্মসংস্থান" if is_bn else "Employment opportunities", "english": "Employment opportunities", "emotion": "calm"}
                ]
            else:
                causes_list = [
                    {"label": "গ্রিনহাউস গ্যাস নির্গমন" if is_bn else "Greenhouse gas emissions", "english": "Greenhouse gas emissions", "emotion": "intense"},
                    {"label": "বন উজাড়করণ" if is_bn else "Deforestation", "english": "Deforestation", "emotion": "calm"},
                    {"label": "সমুদ্রপৃষ্ঠের উচ্চতা বৃদ্ধি" if is_bn else "Rising sea levels", "english": "Rising sea levels", "emotion": "calm"}
                ]

            # Append exactly 2 to 3 causes and relations
            e_start_idx = len(model.entities) + 1
            for c_idx, cause in enumerate(causes_list[:3]): # Strict limit to 3 max
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

                        # Populate Entities with strict dict validation, default coercions, and word-length trimming
                        for ent_idx, ent in enumerate(s_data.get("entities", [])):
                            if not isinstance(ent, dict):
                                continue

                            ent_id = ent.get("id") or f"ent_{target_id}_{ent_idx}"
                            label = ent.get("label") or "Entity"

                            # Trim label strictly to 2-3 words maximum
                            words = str(label).split()
                            if len(words) > 3:
                                label = " ".join(words[:3])

                            # Normalize active_windows to always fall relative within [15, 285] of local scene timeline [0, 300]
                            raw_windows = ent.get("active_windows", [])
                            normalized_windows = []
                            if isinstance(raw_windows, list):
                                for win in raw_windows:
                                    if isinstance(win, list) and len(win) == 2:
                                        s_win = int(win[0]) % 300
                                        e_win = int(win[1]) % 300
                                        # Clamping values to [15, 285]
                                        s_win = max(15, min(285, s_win))
                                        e_win = max(15, min(285, e_win))
                                        if s_win >= e_win:
                                            e_win = min(285, s_win + 120)
                                        normalized_windows.append([s_win, e_win])

                            if not normalized_windows:
                                # Default active window cushion if none defined
                                normalized_windows = [[30, 270]]

                            try:
                                matching_model.entities.append(Entity(
                                    id=str(ent_id),
                                    label=str(label),
                                    type=str(ent.get("type", "concept")),
                                    importance=float(ent.get("importance", 1.0)),
                                    emotion=str(ent.get("emotion")) if ent.get("emotion") else "calm",
                                    scale=float(ent.get("scale", 1.0)),
                                    active_windows=normalized_windows,
                                    attributes=ent.get("attributes", {}) if isinstance(ent.get("attributes"), dict) else {}
                                ))
                            except Exception as e:
                                print(f"⚠️ Skipping invalid entity mapping: {e}")

                        # Populate Actions with strict dict validation and default coercions
                        for act_idx, act in enumerate(s_data.get("actions", [])):
                            if not isinstance(act, dict):
                                continue

                            act_id = act.get("id") or f"act_{target_id}_{act_idx}"
                            label = act.get("label") or "action"

                            try:
                                matching_model.actions.append(Action(
                                    id=str(act_id),
                                    label=str(label),
                                    subject_id=str(act.get("subject_id")) if act.get("subject_id") else None,
                                    object_id=str(act.get("object_id")) if act.get("object_id") else None,
                                    importance=float(act.get("importance", 1.0))
                                ))
                            except Exception as e:
                                print(f"⚠️ Skipping invalid action mapping: {e}")

                        # Populate Quantities with strict dict validation and default coercions
                        for q_idx, q in enumerate(s_data.get("quantities", [])):
                            if not isinstance(q, dict):
                                continue

                            val = q.get("value")
                            try:
                                val = float(val) if val is not None else 0.0
                            except:
                                val = 0.0
                            label = q.get("label") or str(val)

                            try:
                                matching_model.quantities.append(Quantity(
                                    value=val,
                                    unit=str(q.get("unit")) if q.get("unit") else None,
                                    label=str(label),
                                    entity_id=str(q.get("entity_id")) if q.get("entity_id") else None
                                ))
                            except Exception as e:
                                print(f"⚠️ Skipping invalid quantity mapping: {e}")

                        # Populate Temporals with strict dict validation and default coercions
                        for t_idx, t in enumerate(s_data.get("temporal_expressions", [])):
                            if not isinstance(t, dict):
                                continue

                            label = t.get("label")
                            if not label:
                                continue

                            try:
                                matching_model.temporal_expressions.append(TemporalExpression(
                                    label=str(label),
                                    value=str(t.get("value")) if t.get("value") else None,
                                    type=str(t.get("type", "point"))
                                ))
                            except Exception as e:
                                print(f"⚠️ Skipping invalid temporal mapping: {e}")

                        # Populate Relations with strict dict validation, default coercions, and target safety
                        for rel_idx, rel in enumerate(s_data.get("relations", [])):
                            if not isinstance(rel, dict):
                                continue

                            rel_id = rel.get("id") or f"rel_{target_id}_{rel_idx}"
                            src = rel.get("source_id") or rel.get("source")
                            tgt = rel.get("target_id") or rel.get("target")
                            relationship = rel.get("relationship") or "connector"
                            if not src or not tgt:
                                continue

                            try:
                                matching_model.relations.append(Relation(
                                    id=str(rel_id),
                                    source_id=str(src),
                                    target_id=str(tgt),
                                    relationship=str(relationship),
                                    importance=float(rel.get("importance", 1.0)),
                                    strength=float(rel.get("strength", 1.0))
                                ))
                            except Exception as e:
                                print(f"⚠️ Skipping invalid relation mapping: {e}")
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
