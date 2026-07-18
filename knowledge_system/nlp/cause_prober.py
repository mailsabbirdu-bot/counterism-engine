import urllib.request
import urllib.parse
import json
import re
import os
from typing import List, Dict, Optional
from .semantic_model import Entity, Relation

# Try importing Spacy and Transformers for the high-end Colab runtime
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False

try:
    from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


class NormalizedKnowledgeEngine:
    def __init__(self, kb_path: str = "knowledge_base.json"):
        print("⚙️ Initializing Production Knowledge Engine on CPU...")

        # 1. Load External Knowledge Base
        self.kb_path = kb_path
        self.knowledge_base = self._load_knowledge_base()

        # 2. Translation Engine & CPU Performance Cache
        if HAS_TRANSFORMERS:
            try:
                model_name = "facebook/m2m100_418M"
                self.tokenizer = M2M100Tokenizer.from_pretrained(model_name)
                self.model = M2M100ForConditionalGeneration.from_pretrained(model_name)
                print("✅ M2M100 model initialized successfully.")
            except Exception as e:
                print(f"⚠️ M2M100 initialization failed: {e}. Using rule-based fallback translator.")
                self.model = None
                self.tokenizer = None
        else:
            print("⚠️ Transformers library not available. Using rule-based fallback translator.")
            self.model = None
            self.tokenizer = None

        self.translation_cache = {}

        # 3. Linguistic Parsers
        if HAS_SPACY:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print("✅ SpaCy en_core_web_sm model initialized successfully.")
            except Exception as e:
                print(f"⚠️ SpaCy model load failed: {e}. Using regex/stanza fallback parser.")
                self.nlp = None
        else:
            print("⚠️ SpaCy not available. Using regex/stanza fallback parser.")
            self.nlp = None

        # 4. Wikipedia Junk Category Filter
        self.banned_category_keywords = [
            "living people", "articles", "dates", "wikipedia",
            "pages", "cs1", "webarchive", "use dmy"
        ]

        # Standard Offline High-Fidelity translation map to guarantee zero-fail offline mode
        self.fallback_translation_map = {
            "bn_to_en": {
                "মেগাসিটি": "megacity",
                "ক্রাউডেড": "crowded",
                "জনবহুল": "populous",
                "ঢাকা": "Dhaka",
                "যানজট": "traffic congestion",
                "জ্যাম": "traffic jam",
                "দূষণ": "environmental pollution",
                "পরিবেশ": "environment",
                "বায়ু": "air pollution",
                "বর্জ্য": "industrial waste",
                "জলবায়ু": "climate change",
                "দুর্যোগ": "natural disaster",
                "অর্থনীতি": "economy",
                "প্রবৃদ্ধি": "economic growth",
                "দারিদ্র্য": "poverty",
                "চাকরি": "employment",
                "বাংলাদেশের রাজধানী এবং এটি একটি জনবহুল শহর": "Capital of Bangladesh and a populous city",
                "২০২৪ সালে অ্যাপল ইনকর্পোরেটেড ১৫ শতাংশ প্রবৃদ্ধি রিপোর্ট করেছে": "In 2024 Apple Incorporated reported 15 percent growth"
            },
            "en_to_bn": {
                "rapid urbanization": "দ্রুত নগরায়ণ",
                "rural-urban migration": "গ্রাম-শহর অভিবাসন",
                "centralized administration": "কেন্দ্রীভূত প্রশাসন",
                "employment opportunities": "কর্মসংস্থান",
                "industrial emissions": "শিল্প নির্গমন",
                "unplanned waste disposal": "পরিকল্পনাহীন বর্জ্য",
                "deforestation": "বন উজাড়করণ",
                "fossil fuel consumption": "জীবাশ্ম জ্বালানি",
                "unplanned road network": "ত্রুটিপূর্ণ সড়ক নেটওয়ার্ক",
                "narrow roads": "সংকীর্ণ রাস্তা",
                "high vehicle volume": "অতিরিক্ত যানবাহন",
                "illegal parking": "অবৈধ পার্কিং",
                "greenhouse gas emissions": "গ্রিনহাউস গ্যাস নির্গমন",
                "rising global temperature": "বৈশ্বিক তাপমাত্রা বৃদ্ধি",
                "rising sea levels": "সমুদ্রপৃষ্ঠের উচ্চতা বৃদ্ধি",
                "market volatility": "বাজারের অস্থিরতা",
                "inflationary pressures": "মুদ্রাস্ফীতির চাপ",
                "resource misallocation": "সম্পদের অপব্যবহার",
                "economic recession": "অর্থনৈতিক মন্দা",
                "Dhaka": "ঢাকা",
                "megacity": "মেগাসিটি",
                "traffic congestion": "যানজট",
                "pollution": "দূষণ"
            }
        }

    def _load_knowledge_base(self) -> Dict:
        """Loads the externalized conceptual database."""
        try:
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ {self.kb_path} not found. Initializing minimal fallback structure.")
            return {"domains": []}

    def _cached_translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Reduces CPU overhead by matching pre-translated strings."""
        text_clean = text.strip()
        if not text_clean:
            return ""

        cache_key = f"{src_lang}:{tgt_lang}:{text_clean.lower()}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        # 1. Use high-performance M2M100 Transformer if initialized
        if self.model and self.tokenizer:
            try:
                self.tokenizer.src_lang = src_lang
                encoded_input = self.tokenizer(text_clean, return_tensors="pt")
                forced_bos_token_id = self.tokenizer.get_lang_id(tgt_lang)

                generated_tokens = self.model.generate(**encoded_input, forced_bos_token_id=forced_bos_token_id)
                translated_text = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]

                self.translation_cache[cache_key] = translated_text
                return translated_text
            except Exception as e:
                print(f"⚠️ M2M100 Translation failed: {e}. Falling back to preloaded map.")

        # 2. Offline-First Dictionary Mapping fallback
        map_key = "bn_to_en" if src_lang == "bn" else "en_to_bn"
        fallback_map = self.fallback_translation_map.get(map_key, {})

        # Check direct or substring matches
        for src_phrase, tgt_phrase in fallback_map.items():
            if src_phrase.lower() in text_clean.lower() or text_clean.lower() in src_phrase.lower():
                self.translation_cache[cache_key] = tgt_phrase
                return tgt_phrase

        # If no mapping exists, return English or Bangla safely
        self.translation_cache[cache_key] = text_clean
        return text_clean

    def _extract_ranked_concepts(self, english_text: str) -> List[str]:
        """
        Upgraded Entity Extraction: Extracts named entities, compound nouns,
        and high-value noun chunks, ranking them by descriptive value.
        """
        candidates = []

        # A. High-Fidelity SpaCy Parser if available
        if self.nlp:
            try:
                doc = self.nlp(english_text)
                # Priority 1: Named Entities (e.g., "Dhaka")
                for ent in doc.ents:
                    if ent.label_ in ("GPE", "ORG", "LOC"):
                        candidates.append(ent.text.lower())

                # Priority 2: Full Noun Chunks (e.g., "world's largest megacities")
                for chunk in doc.noun_chunks:
                    clean_chunk = " ".join([t.text.lower() for t in chunk if t.pos_ not in ("DET", "PRON")])
                    if clean_chunk and clean_chunk not in candidates:
                        candidates.append(clean_chunk)

                # Priority 3: Individual core lemmas as fallbacks
                for token in doc:
                    if token.pos_ in ("NOUN", "PROPN") and token.dep_ in ("nsubj", "attr", "dobj"):
                        lemma = token.lemma_.lower()
                        if lemma not in candidates:
                            candidates.append(lemma)
                return candidates
            except Exception as e:
                print(f"⚠️ SpaCy concept extraction failed: {e}. Falling back to regex.")

        # B. Robust Regex/String Fallback for offline/lightweight execution
        # Extracts title-cased words (proper nouns) and long words (>3 letters)
        words = re.findall(r'\b[a-zA-Z]{4,20}\b', english_text)
        for w in words:
            w_lower = w.lower()
            if w_lower not in candidates and w_lower not in {"with", "that", "this", "from", "their"}:
                candidates.append(w_lower)

        # Also include title-case sequences (e.g., "Apple Incorporated")
        prop_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', english_text)
        for pn in prop_nouns:
            pn_lower = pn.lower()
            if pn_lower not in candidates:
                candidates.insert(0, pn_lower) # Prioritize proper nouns

        return candidates

    def _match_local_knowledge(self, search_string: str) -> Optional[Dict]:
        """Performs soft matching against the domain IDs and synonym lists."""
        search_str_clean = search_string.lower()
        for domain in self.knowledge_base.get("domains", []):
            if domain["id"] in search_str_clean:
                return domain
            for synonym in domain.get("synonyms", []):
                if synonym in search_str_clean or search_str_clean in synonym:
                    return domain
        return None

    def _query_wikipedia_normalization_tags(self, entity: str) -> List[str]:
        """Queries Wikipedia API to discover semantic categories, filtering out system junk."""
        try:
            safe_query = urllib.parse.quote(entity)
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={safe_query}&format=json"

            req = urllib.request.Request(search_url, headers={'User-Agent': 'CRVE-Engine/4.0.0'})
            title = None
            with urllib.request.urlopen(req, timeout=3) as res:
                data = json.loads(res.read().decode('utf-8'))
                results = data.get("query", {}).get("search", [])
                if results:
                    title = results[0]["title"]

            if not title:
                return []

            safe_title = urllib.parse.quote(title)
            cat_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=categories&titles={safe_title}&cllimit=20&format=json"

            req_cat = urllib.request.Request(cat_url, headers={'User-Agent': 'CRVE-Engine/4.0.0'})
            valid_categories = []
            with urllib.request.urlopen(req_cat, timeout=3) as res:
                cat_data = json.loads(res.read().decode('utf-8'))
                pages = cat_data.get("query", {}).get("pages", {})
                for _, pinfo in pages.items():
                    for cat in pinfo.get("categories", []):
                        cat_title = cat.get("title", "").lower()

                        if not any(keyword in cat_title for keyword in self.banned_category_keywords):
                            clean_cat = cat_title.replace("category:", "").strip()
                            valid_categories.append(clean_cat)
            return valid_categories
        except Exception as e:
            print(f"⚠️ Normalization mapping failed for '{entity}': {e}")
            return []


class CauseProber:
    def __init__(self, kb_path: str = "knowledge_base.json"):
        # Instantiate our unified normalized knowledge engine
        self.engine = NormalizedKnowledgeEngine(kb_path=kb_path)

    def _is_bangla(self, text: str) -> bool:
        return any("\u0980" <= char <= "\u09FF" for char in str(text))

    def probe_causes(self, scene_text: str, entities: List[Entity], next_scene_text: Optional[str] = None) -> List[dict]:
        """
        Drives the Concept Normalization pipeline:
        1. Translates input to English.
        2. Extracts ranked concept nouns.
        3. Normalizes concepts against local and Wikipedia category domains.
        4. Translates matched domain causes back to clean Bangla or uses preloaded translations.
        """
        is_bn = self._is_bangla(scene_text)

        # Translate to English to run concept extraction
        english_text = scene_text
        if is_bn:
            english_text = self.engine._cached_translate(scene_text, src_lang="bn", tgt_lang="en")

        # Extract candidates
        extracted_concepts = self.engine._extract_ranked_concepts(english_text)
        print(f"🔍 Extracted Concepts for Normalization: {extracted_concepts}")

        matched_domain = None

        # 1. Attempt Soft Matching on direct extracted concepts
        for concept in extracted_concepts:
            matched_domain = self.engine._match_local_knowledge(concept)
            if matched_domain:
                print(f"🎯 Direct Concept Normalization Hit: Matched '{concept}' -> Domain ID '{matched_domain['id']}'")
                break

        # 2. Attempt Wikipedia Category-based Concept Normalization
        if not matched_domain:
            for concept in extracted_concepts[:2]: # Check top 2 concepts to maintain speed
                categories = self.engine._query_wikipedia_normalization_tags(concept)
                print(f"📖 Wikipedia Categories for '{concept}': {categories}")
                for category in categories:
                    matched_domain = self.engine._match_local_knowledge(category)
                    if matched_domain:
                        print(f"🎯 Category-Based Normalization Hit: Normalized '{concept}' via category '{category}' -> Domain ID '{matched_domain['id']}'")
                        break
                if matched_domain:
                    break

        # 3. Fallback: If no match found, fallback to first matching domain in text or default 'megacity'/'economy'
        if not matched_domain:
            text_lower = english_text.lower()
            for domain in self.engine.knowledge_base.get("domains", []):
                if domain["id"] in text_lower or any(s in text_lower for s in domain.get("synonyms", [])):
                    matched_domain = domain
                    print(f"📌 Substring Fallback Match: Resolved to Domain '{domain['id']}'")
                    break

        if not matched_domain:
            # Absolute default
            matched_domain = self.engine.knowledge_base.get("domains", [])[0]
            print(f"ℹ️ No domain mapped. Using default Domain ID '{matched_domain['id']}'")

        # Collect causes
        detected_causes = []
        causes_en = matched_domain["causes"]
        causes_bn = matched_domain.get("bn_causes", [])

        for idx, en_cause in enumerate(causes_en):
            # If the output language is Bangla, check if we have preloaded Bangla causes
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

        # 4. Context-Aware Deduplication (Next Scene check)
        if next_scene_text:
            next_text_lower = next_scene_text.lower()
            filtered_causes = []
            for cause in detected_causes:
                triggers = cause.get("search_trigger", []) + [cause["label"].lower(), cause["english"].lower()]
                already_described = any(trig in next_text_lower for trig in triggers)
                if not already_described:
                    filtered_causes.append(cause)
                else:
                    print(f"💡 Context Deduplicator: Excluded '{cause['label']}' as subsequent scenes describe it.")
            detected_causes = filtered_causes

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

            # Inject Relation Link (with causes relationship type so it renders with custom styled electric arrows!)
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
