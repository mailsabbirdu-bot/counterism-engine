import urllib.request
import urllib.parse
import json
import re
from typing import List, Dict, Optional

# Minimal schema declarations for graph rendering steps with Pydantic fallback compatibility
try:
    from .semantic_model import Entity, Relation, Action, Quantity, TemporalExpression, SemanticSceneModel
except ImportError:
    class Entity:
        def __init__(self, id: str, label: str, type: str, importance: float = 1.0, scale: float = 1.0, emotion: str = "neutral"):
            self.id = id
            self.label = label
            self.type = type
            self.importance = importance
            self.scale = scale
            self.emotion = emotion

    class Relation:
        def __init__(self, id: str, source_id: str, target_id: str, relationship: str, importance: float = 1.0, strength: float = 1.0):
            self.id = id
            self.source_id = source_id
            self.target_id = target_id
            self.relationship = relationship
            self.importance = importance
            self.strength = strength


class CauseProber:
    def __init__(self, kb_path: str = "knowledge_base.json"):
        # Load local KB for fallback mode only
        self.kb_path = kb_path
        self.knowledge_base = self._load_knowledge_base()

    def _load_knowledge_base(self) -> Dict:
        try:
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"domains": []}

    def _is_bangla(self, text: str) -> bool:
        return any("\u0980" <= char <= "\u09FF" for char in str(text))

    def _interact_with_gemini(self, prompt: str) -> str:
        """Interactive prompt-and-paste loop using Google Colab UI or command line input."""
        try:
            from google.colab import output
            import uuid
            u_id = uuid.uuid4().hex[:8]
            header_color = "#2196F3"

            feedback_html = """
            <div style='color: #00FFAB; margin-bottom: 15px; border-left: 4px solid #00FFAB; padding-left: 15px; background: #0c1a12; padding: 10px;'>
                <strong style='font-size: 16px;'>🧠 Gemini NLP Extraction prompt ready</strong>
                <p style='font-size: 13px; margin-top: 4px;'>Copy the prompt below, paste it into Gemini, and copy the resulting JSON back here.</p>
            </div>
            """

            js_code = f"""
                (async () => {{
                    const u_id = "{u_id}";
                    const container = document.createElement('div');
                    container.style = "background: #0a0a0a; color: #fff; padding: 25px; border-radius: 16px; border: 2px solid {header_color}; font-family: 'Segoe UI', Tahoma, sans-serif; max-width: 850px; margin: 20px auto; box-shadow: 0 10px 30px rgba(0,0,0,0.5);";
                    container.innerHTML = `
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                            <h3 style="color: {header_color}; margin: 0; font-size: 22px;">🧠 Studio V4 Knowledge System</h3>
                            <span style="background: {header_color}; color: #000; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 14px;">GEMINI NLP EXTRACTOR</span>
                        </div>
                        {feedback_html}
                        <div style="background: #111; padding: 15px; border-radius: 8px; border: 1px solid #333; margin-bottom: 15px;">
                            <p style="margin: 0 0 10px 0; font-size: 14px; color: #aaa;">1. Copy the dynamically generated NLP extraction prompt.</p>
                            <button id="copy-${{u_id}}" style="background: {header_color}; color: #000; border: none; padding: 12px; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; transition: opacity 0.2s;">📋 COPY PROMPT TO CLIPBOARD</button>
                        </div>
                        <div style="background: #111; padding: 15px; border-radius: 8px; border: 1px solid #333;">
                            <p style="margin: 0 0 10px 0; font-size: 14px; color: #aaa;">2. Paste Gemini's JSON response below.</p>
                            <textarea id="paste-${{u_id}}" style="width: 100%; height: 250px; background: #000; color: #00FFAB; border: 1px solid #444; padding: 12px; font-family: 'Cascadia Code', 'Courier New', monospace; font-size: 13px; border-radius: 6px; resize: vertical;" placeholder="Paste Gemini's JSON block here..."></textarea>
                            <div style="display: flex; gap: 10px; margin-top: 15px;">
                                <button id="submit-${{u_id}}" style="flex: 2; background: #2196F3; color: #fff; border: none; padding: 14px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 16px; box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);">🚀 SUBMIT EXTRACTED KNOWLEDGE</button>
                                <button id="force-${{u_id}}" style="flex: 1; background: #FF3E6C; color: #fff; border: none; padding: 14px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px; box-shadow: 0 4px 15px rgba(255, 62, 108, 0.3);">🛑 USE OFFLINE FALLBACK</button>
                            </div>
                        </div>
                    `;
                    document.body.appendChild(container);
                    document.getElementById('copy-'+u_id).onclick = () => {{
                        navigator.clipboard.writeText({json.dumps(prompt)});
                        document.getElementById('copy-'+u_id).innerText = "COPIED TO CLIPBOARD!";
                    }};
                    return new Promise((resolve) => {{
                        document.getElementById('submit-'+u_id).onclick = () => {{
                            const val = document.getElementById('paste-'+u_id).value.trim();
                            if (!val) {{ alert("Please paste Gemini's response first."); return; }}
                            container.remove(); resolve(val);
                        }};
                        document.getElementById('force-'+u_id).onclick = () => {{
                            container.remove(); resolve("USE_FALLBACK_SIGNAL");
                        }};
                    }});
                }})();
            """
            return output.eval_js(js_code)
        except Exception:
            # Fallback for standard non-Colab terminal
            print("\n" + "="*80)
            print("📋 GEMINI KNOWLEDGE NLP EXTRACTION PROMPT")
            print("="*80)
            print(prompt)
            print("="*80 + "\n")
            print("Please copy the prompt above, paste it into Gemini, and paste the resulting JSON below.")
            print("(Type 'fallback' to use the offline-first rule-based extraction engine instead)\n")
            val = ""
            while not val.strip():
                val = input("Paste Gemini JSON (or 'fallback'): ").strip()
            return val

    def generate_dynamic_prompt(self, scenes_data: List[dict]) -> str:
        """Generates a comprehensive, carefully designed prompt asking Gemini to extract all NLP and causal concepts."""
        prompt = """TASK: HIGH-FIDELITY COGNITIVE NLP & ADVANCED SEMANTIC RELATIONSHIP EXTRACTION FOR CINEMATIC KNOWLEDGE GRAPHS.

You are acting as an expert documentary director, cognitive systems analyst, and senior NLP extraction model.
Your task is to analyze the sequence of scene narrations below, extract their underlying entities, actions, quantities, relationships, and dynamically assign highly specific semantic relation types to create an exceptionally rich, diverse, and non-repetitive visualization plan.

--- THE NARRATIVE STORY CONTEXT ---
"""
        for s in scenes_data:
            prompt += f"Scene [{s['scene_id']}]: \"{s['narration']}\"\n"

        prompt += """
--- RELATIONSHIP SEMANTIC REGISTRY (MANDATORY INJECTION) ---
Choose from these exact semantic relationship keys based on the logical structure of each narration:
1. ENERGY TRANSITIONS (Renders as Pulsing Crimson Electric Lightning):
   - 'cause_effect', 'effect_cause', 'trigger_response', 'action_consequence', 'feedback_loop', 'influence', 'causes', 'produces'.
2. PIPELINE FLOWS (Renders as Cyber Quantum Cyan Pipeline with glowing sliding beads):
   - 'construction_flow', 'builds', 'input_output', 'process_flow', 'supply_chain', 'migration_flow'.
3. LOGIC & DATA (Renders as Gold Schematic Traces with micro marching dot sequences):
   - 'evidence_conclusion', 'claim_evidence', 'fact_explanation', 'reason_result', 'reveal', 'hidden_under'.
4. STRUCTURES & GROUPS (Renders as HUD Double Outlines):
   - 'containment', 'is_a', 'part_whole', 'whole_parts', 'hierarchy', 'membership', 'ownership'.
5. TIME & TRANSFORMATION (Renders as Emerald Gradient Bio-Chemical Fluid flow):
   - 'lifecycle', 'transformation', 'evolution', 'cycle'.
6. CHRONOLOGY & DEPENDENCIES (Renders as Indigo Laser Pulse Trails):
   - 'timeline', 'sequence', 'dependency', 'dependency_chain', 'dependency_network'.
7. TENSION & OPPOSITION (Renders as Double Opposing Red Blazing Laser Sweeps):
   - 'conflict', 'contrast', 'trade_off', 'risk_impact'.
8. ASSOCIATIONS & CONTEXTS (Renders as Broad Glassmorphic Translucent Sankey Conduits):
   - 'grouping', 'classification', 'comparison', 'similarity', 'analogy', 'association', 'correlation', 'context', 'reference', 'semantic_link', 'importance', 'collaboration', 'narrative_flow'.

--- STRUCTURAL CONSTRAINTS & EXTRACTION GUIDELINES (STRICT) ---
For each scene, you must extract:
1. ENTITIES:
   - 'id': Clean ASCII-safe lowercase identifier (e.g. "dhaka", "apple_inc"). Avoid raw non-ASCII Bangla characters for IDs.
   - 'label': In clean Bangla or English matching the narration.
   - 'type': Must be one of: "hero" (central subject, e.g. "dhaka"), "concept", "organization", "location", "metric", "event".
   - 'importance': Float (1.0 to 5.0).
   - 'emotion': One of: "calm", "intense", "growing", "danger", "stable".
   - 'active_windows': A list of frame ranges when the entity is spoken or shown, e.g. [[30, 90]] (scene duration: 0 to 300).
2. ACTIONS, QUANTITIES, TEMPORAL EXPRESSIONS: Extract significant verbs, quantities (with values/units), and chronological points.
3. RELATIONS (CONVERT NARRAIVES TO RICH MAPS):
   - 'source_id' / 'target_id': Match entity IDs.
   - 'relationship': Select the exact matching relationship key from our SEMANTIC REGISTRY (e.g., 'risk_impact', 'process_flow', 'claim_evidence'). Avoid generic 'connector' or 'energy_transfer' where a specific semantic key applies!
   - 'importance': 1.0 to 3.0.
   - 'strength': 1.0 to 3.0.
4. PROBE CAUSAL/CONSEQUENCE FACTORS (2-4 per scene):
   - Identify the primary assertions in each scene, and connect them dynamically to 2 to 4 underlying causes/milestones.
   - 'label' (Bangla): Pristine, premium Bangla. Strictly 2 to 3 words maximum. Never exceed 3 words (to prevent layout wrapping/clipping in UI graph nodes).
   - 'english': Direct English translation. Strictly 2 to 3 words maximum.
   - Connect these using the appropriate relation type (e.g., 'cause_effect', 'risk_impact', 'dependency') to trigger distinct glowing modern connector paths automatically.
5. CONTEXT-AWARE DEDUPLICATION: If a cause/reason is already described or explicitly explained in subsequent scenes, exclude it from the earlier scene to preserve progressive story discovery.
6. SCENE CLASSIFICATION: Classify 'scene_type' (trend | conflict | comparison | historical) and 'emotional_tone' (calm | intense | growing | danger).

--- REQUIRED OUTPUT JSON SCHEMA ---
{
  "scenes": [
    {
      "scene_id": "SCENE_1",
      "scene_type": "trend",
      "emotional_tone": "calm",
      "importance_score": 1.0,
      "entities": [
        {
          "id": "dhaka",
          "label": "ঢাকা",
          "type": "hero",
          "importance": 3.0,
          "emotion": "calm",
          "scale": 1.0,
          "active_windows": [[15, 120]]
        },
        {
          "id": "rapid_urbanization",
          "label": "দ্রুত নগরায়ণ",
          "type": "concept",
          "importance": 1.5,
          "scale": 1.0,
          "emotion": "intense",
          "active_windows": [[45, 150]]
        }
      ],
      "actions": [],
      "quantities": [],
      "temporal_expressions": [],
      "relations": [
        {
          "id": "r_1",
          "source_id": "rapid_urbanization",
          "target_id": "dhaka",
          "relationship": "cause_effect",
          "importance": 1.2,
          "strength": 1.0
        }
      ]
    }
  ]
}

NO PREAMBLE. NO CHATTER. RETURN ONLY THE CORRECT RAW JSON BLOCK.
"""
        return prompt

    def probe_causes_fallback(self, scene_text: str, entities: List[Entity], next_scene_text: Optional[str] = None) -> List[dict]:
        """Resolves descriptive narratives into highly contextual conceptual core causes using local KB fallbacks."""
        is_bn = self._is_bangla(scene_text)

        english_text = scene_text
        if is_bn:
            english_text = self.engine._cached_translate(scene_text, src_lang="bn", tgt_lang="en")

        extracted_concepts = self.engine._extract_ranked_concepts(english_text)
        matched_domain = None

        # Tier 1: Local Knowledge Domain matching
        for concept in extracted_concepts:
            matched_domain = self.engine._match_local_knowledge(concept)
            if matched_domain:
                break

        # Tier 2: Wikipedia Semantic Expansion Category Mapping
        if not matched_domain:
            for concept in extracted_concepts[:2]:
                categories = self.engine._query_wikipedia_normalization_tags(concept)
                for category in categories:
                    matched_domain = self.engine._match_local_knowledge(category)
                    if matched_domain:
                        break
                if matched_domain:
                    break

        # Tier 3: Hard Word-Boundary Fallback Matching
        if not matched_domain:
            text_lower = english_text.lower()
            for domain in self.engine.knowledge_base.get("domains", []):
                domain_id = domain["id"].lower()
                id_match = re.search(r'\b' + re.escape(domain_id) + r'\b', text_lower)
                synonym_match = any(
                    re.search(r'\b' + re.escape(s.lower()) + r'\b', text_lower)
                    for s in domain.get("synonyms", [])
                )
                if id_match or synonym_match:
                    matched_domain = domain
                    break

        if not matched_domain:
            domains = self.engine.knowledge_base.get("domains", [])
            if domains:
                matched_domain = domains[0]
            else:
                return [{
                    "label": "কাঠামোগত পরিবর্তন" if is_bn else "Structural Changes",
                    "english": "structural changes"
                }]

        # Construct mapped operational output models
        detected_causes = []
        causes_en = matched_domain.get("causes", [])
        causes_bn = matched_domain.get("bn_causes", [])

        for idx, en_cause in enumerate(causes_en):
            if is_bn:
                bn_cause = causes_bn[idx] if idx < len(causes_bn) else self.engine._cached_translate(en_cause, src_lang="en", tgt_lang="bn")
                detected_causes.append({
                    "label": bn_cause,
                    "english": en_cause,
                    "search_trigger": [bn_cause.lower(), en_cause.lower()]
                })
            else:
                detected_causes.append({
                    "label": en_cause.capitalize(),
                    "english": en_cause,
                    "search_trigger": [en_cause.lower()]
                })

        # Tier 4: Context-Aware Deduplication via Type Guarding
        if next_scene_text and isinstance(next_scene_text, str):
            next_text_lower = next_scene_text.lower()
            filtered_causes = []
            for cause in detected_causes:
                triggers = cause.get("search_trigger", []) + [cause["label"].lower(), cause["english"].lower()]
                already_described = any(trig in next_text_lower for trig in triggers)
                if not already_described:
                    filtered_causes.append(cause)
            detected_causes = filtered_causes

        return detected_causes[:4]

    def probe_and_inject_all(self, all_scene_models: List[any]) -> dict:
        """
        Coordinates the interactive Gemini loop:
        - Extracts narration from all scenes.
        - Presents the HTML / CLI prompt interface.
        - Recovers and parses the pasted JSON.
        - Gracefully falls back to local rule-based category normalization if needed.
        """
        if not all_scene_models:
            return {}

        scenes_data = []
        for model in all_scene_models:
            scenes_data.append({
                "scene_id": model.scene_id,
                "narration": model.narration
            })

        # Generate prompt and trigger Gemini interaction loop
        prompt = self.generate_dynamic_prompt(scenes_data)
        raw_result = self._interact_with_gemini(prompt)

        pasted_data = None
        use_fallback = False

        if "USE_FALLBACK_SIGNAL" in raw_result or raw_result.strip().lower() == "fallback":
            use_fallback = True
        else:
            try:
                # Sanitize to find JSON block
                json_match = re.search(r'(\{.*\})', raw_result, re.DOTALL)
                if json_match:
                    pasted_data = json.loads(json_match.group(1))
                else:
                    pasted_data = json.loads(raw_result)
            except Exception as e:
                print(f"⚠️ Failed to parse Gemini output: {e}. Falling back to rule-based system.")
                use_fallback = True

        # Process and return
        if use_fallback or not pasted_data or "scenes" not in pasted_data:
            print("🌲 Using offline-first lightweight rule-based parsing fallback.")
            return {"status": "fallback"}
        else:
            print("⚡ Successfully parsed and loaded extracted NLP models from Gemini!")
            return {"status": "success", "data": pasted_data}
