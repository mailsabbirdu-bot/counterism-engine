import urllib.request
import urllib.parse
import json
import re
import os
from collections import OrderedDict
from typing import List, Dict, Optional

# Attempt to load high-fidelity libraries if running in fully equipped runtimes
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

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


# Minimal schema declarations for graph rendering steps with Pydantic fallback compatibility
try:
    from .semantic_model import Entity, Relation
except ImportError:
    # Standard class fallback for single file system usage
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


class NormalizedKnowledgeEngine:
    def __init__(self, kb_path: str = "knowledge_base.json"):
        print("⚙️ Initializing Production Knowledge Engine on CPU...")

        # 1. Load External Knowledge Base
        self.kb_path = kb_path
        self.knowledge_base = self._load_knowledge_base()

        # 2. Translation Engine Configuration
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

        # Bounded Translation Cache (LRU-based eviction to prevent wiping out data mid-run)
        self.translation_cache = OrderedDict()
        self.translation_cache_max = 2000

        # Dedicated Network and Timeout Failure Cache for Wikipedia API lookups
        self.wikipedia_cache = {}

        # 3. Linguistic Parsers
        if HAS_SPACY:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print("✅ SpaCy en_core_web_sm model initialized successfully.")
            except Exception as e:
                print(f"⚠️ SpaCy model load failed: {e}. Using regex fallback parser.")
                self.nlp = None
        else:
            print("⚠️ SpaCy not available. Using regex fallback parser.")
            self.nlp = None

        # 4. Wikipedia Junk Filtering Parameters
        self.banned_category_keywords = [
            "living people", "articles", "dates", "wikipedia",
            "pages", "cs1", "webarchive", "use dmy"
        ]

        # Standard Offline translation map to guarantee zero-fail local workflows
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
                "চাকরি": "employment"
            },
            "en_to_bn": {
                "rapid urbanization": "দ্রুত নগরায়ণ",
                "rural-urban migration": "গ্রাম-শহর অভিবাসন",
                "centralized administration": "কেন্দ্রেীভূত প্রশাসন",
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
                "rising global temperature": "বৈস্মিক তাপমাত্রা বৃদ্ধি",
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
        """Translates text utilizing performance optimizations and an LRU eviction strategy."""
        text_clean = text.strip()
        if not text_clean:
            return ""

        cache_key = f"{src_lang}:{tgt_lang}:{text_clean.lower()}"
        if cache_key in self.translation_cache:
            # Move key to end to track recent usage
            self.translation_cache.move_to_end(cache_key)
            return self.translation_cache[cache_key]

        # 1. High-Performance Transformer Translation Loop
        translated_text = None
        if self.model and self.tokenizer:
            try:
                self.tokenizer.src_lang = src_lang
                encoded_input = self.tokenizer(text_clean, return_tensors="pt")
                forced_bos_token_id = self.tokenizer.get_lang_id(tgt_lang)

                # inference_mode eliminates autograd overhead and tracking updates completely on CPU
                if HAS_TORCH:
                    import torch
                    with torch.inference_mode():
                        generated_tokens = self.model.generate(**encoded_input, forced_bos_token_id=forced_bos_token_id)
                else:
                    generated_tokens = self.model.generate(**encoded_input, forced_bos_token_id=forced_bos_token_id)

                translated_text = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
            except Exception as e:
                print(f"⚠️ Transformer Translation failed: {e}. Falling back to preloaded map.")

        # 2. Resilient Offline Dictionary Mapping Fallback
        if not translated_text:
            map_key = "bn_to_en" if src_lang == "bn" else "en_to_bn"
            fallback_map = self.fallback_translation_map.get(map_key, {})

            for src_phrase, tgt_phrase in fallback_map.items():
                if src_phrase.lower() in text_clean.lower() or text_clean.lower() in src_phrase.lower():
                    translated_text = tgt_phrase
                    break

        if not translated_text:
            translated_text = text_clean

        # Bounded LRU Cache Management: Evict oldest item if max capacity reached
        if len(self.translation_cache) >= self.translation_cache_max:
            self.translation_cache.popitem(last=False)

        self.translation_cache[cache_key] = translated_text
        return translated_text

    def _extract_ranked_concepts(self, english_text: str) -> List[str]:
        """Extracts technical alphanumeric concepts, noun chunks, and entities from descriptions."""
        candidates = []

        if self.nlp:
            try:
                doc = self.nlp(english_text)
                # Group 1: Named geographic and organizational entities
                for ent in doc.ents:
                    if ent.label_ in ("GPE", "ORG", "LOC"):
                        candidates.append(ent.text.lower())

                # Group 2: Compound Noun Phrases
                for chunk in doc.noun_chunks:
                    clean_chunk = " ".join([t.text.lower() for t in chunk if t.pos_ not in ("DET", "PRON")])
                    if clean_chunk and clean_chunk not in candidates:
                        candidates.append(clean_chunk)

                # Group 3: Core subjects and direct objects
                for token in doc:
                    if token.pos_ in ("NOUN", "PROPN") and token.dep_ in ("nsubj", "attr", "dobj"):
                        lemma = token.lemma_.lower()
                        if lemma not in candidates:
                            candidates.append(lemma)
                return candidates
            except Exception as e:
                print(f"⚠️ High-fidelity extraction failed: {e}. Falling back to regex parser.")

        # Upgraded Alphanumeric Regex Tokenizer: Catches complex metrics (AI, PM2.5, CO2, 5G)
        words = re.findall(r'\b[a-zA-Z0-9\.\-_]{2,25}\b', english_text)
        for w in words:
            w_lower = w.lower()
            if w_lower not in candidates and w_lower not in {"with", "that", "this", "from", "their", "the", "and"}:
                candidates.append(w_lower)

        prop_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', english_text)
        for pn in prop_nouns:
            pn_lower = pn.lower()
            if pn_lower not in candidates:
                candidates.insert(0, pn_lower)

        return candidates

    def _match_local_knowledge(self, search_string: str) -> Optional[Dict]:
        """Performs token-aware exact set and full phrase evaluations to block false matches."""
        search_str_clean = search_string.lower().strip()
        if not search_str_clean:
            return None

        search_tokens = set(re.findall(r'\w+', search_str_clean))
        if not search_tokens:
            return None

        for domain in self.knowledge_base.get("domains", []):
            if domain["id"] == search_str_clean:
                return domain

            for synonym in domain.get("synonyms", []):
                syn_lower = synonym.lower().strip()

                # Check 1: Direct structural phrase equality
                if syn_lower == search_str_clean:
                    return domain

                # Check 2: Token-set equivalence to allow fluid token reordering
                syn_tokens = set(re.findall(r'\w+', syn_lower))
                if search_tokens == syn_tokens:
                    return domain
        return None

    def _query_wikipedia_normalization_tags(self, entity: str) -> List[str]:
        """Queries Wikipedia API with robust performance caching to prevent network stalls."""
        entity_clean = entity.lower().strip()
        if not entity_clean:
            return []

        # Instant return if concept was previously searched, matched, or timed out
        if entity_clean in self.wikipedia_cache:
            return self.wikipedia_cache[entity_clean]

        valid_categories = []
        try:
            safe_query = urllib.parse.quote(entity_clean)
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={safe_query}&format=json"

            req = urllib.request.Request(search_url, headers={'User-Agent': 'CRVE-Engine/5.0.0'})
            title = None

            # Bound search by a strict network timeout
            with urllib.request.urlopen(req, timeout=3) as res:
                data = json.loads(res.read().decode('utf-8'))
                results = data.get("query", {}).get("search", [])
                if results:
                    title = results[0]["title"]

            if title:
                safe_title = urllib.parse.quote(title)
                cat_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=categories&titles={safe_title}&cllimit=20&format=json"
                req_cat = urllib.request.Request(cat_url, headers={'User-Agent': 'CRVE-Engine/5.0.0'})

                with urllib.request.urlopen(req_cat, timeout=3) as res:
                    cat_data = json.loads(res.read().decode('utf-8'))
                    pages = cat_data.get("query", {}).get("pages", {})
                    for _, pinfo in pages.items():
                        for cat in pinfo.get("categories", []):
                            cat_title = cat.get("title", "").lower()
                            if not any(keyword in cat_title for keyword in self.banned_category_keywords):
                                clean_cat = cat_title.replace("category:", "").strip()
                                valid_categories.append(clean_cat)

        except Exception as e:
            print(f"⚠️ Normalization connection exception for '{entity_clean}': {e}. Caching failure state.")
            # Fall through to save an empty list to prevent repeating timeouts on bad tags

        # Cache the result (success dataset or baseline empty failure state)
        self.wikipedia_cache[entity_clean] = valid_categories
        return valid_categories


class CauseProber:
    def __init__(self, kb_path: str = "knowledge_base.json"):
        self.engine = NormalizedKnowledgeEngine(kb_path=kb_path)

    def _is_bangla(self, text: str) -> bool:
        return any("\u0980" <= char <= "\u09FF" for char in str(text))

    def probe_causes(self, scene_text: str, entities: List[Entity], next_scene_text: Optional[str] = None) -> List[dict]:
        """Resolves descriptive narratives into highly contextual conceptual core causes."""
        is_bn = self._is_bangla(scene_text)

        english_text = scene_text
        if is_bn:
            english_text = self.engine._cached_translate(scene_text, src_lang="bn", tgt_lang="en")

        extracted_concepts = self.engine._extract_ranked_concepts(english_text)
        print(f"🔍 Extracted Concepts for Normalization: {extracted_concepts}")

        matched_domain = None

        # Tier 1: Local Knowledge Domain matching
        for concept in extracted_concepts:
            matched_domain = self.engine._match_local_knowledge(concept)
            if matched_domain:
                print(f"🎯 Direct Concept Normalization Hit: Matched '{concept}' -> Domain ID '{matched_domain['id']}'")
                break

        # Tier 2: Wikipedia Semantic Expansion Category Mapping
        if not matched_domain:
            for concept in extracted_concepts[:2]:
                categories = self.engine._query_wikipedia_normalization_tags(concept)
                print(f"📖 Wikipedia Categories for '{concept}': {categories}")
                for category in categories:
                    matched_domain = self.engine._match_local_knowledge(category)
                    if matched_domain:
                        print(f"🎯 Category-Based Normalization Hit: Normalized '{concept}' via category '{category}' -> Domain ID '{matched_domain['id']}'")
                        break
                if matched_domain:
                    break

        # Tier 3: Hard Word-Boundary Fallback Matching (Prevents sub-string trapping like "war" inside "forward")
        if not matched_domain:
            text_lower = english_text.lower()
            for domain in self.engine.knowledge_base.get("domains", []):
                domain_id = domain["id"].lower()

                # Enforce strict word boundaries on the primary Domain ID
                id_match = re.search(r'\b' + re.escape(domain_id) + r'\b', text_lower)

                # Enforce strict word boundaries across custom synonyms
                synonym_match = any(
                    re.search(r'\b' + re.escape(s.lower()) + r'\b', text_lower)
                    for s in domain.get("synonyms", [])
                )

                if id_match or synonym_match:
                    matched_domain = domain
                    print(f"📌 Boundary-Safe Fallback Match: Resolved to Domain '{domain['id']}'")
                    break

        if not matched_domain:
            domains = self.engine.knowledge_base.get("domains", [])
            if domains:
                matched_domain = domains[0]
                print(f"ℹ️ No domain mapped. Using default Domain ID '{matched_domain['id']}'")
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
                else:
                    print(f"💡 Context Deduplicator: Excluded '{cause['label']}' as subsequent scenes describe it.")
            detected_causes = filtered_causes

        return detected_causes[:4]

    def inject_causes_to_scene(self, scene_idx: int, scene_model: any, next_scene_text: Optional[str] = None) -> None:
        """Modifies a scene structure dynamically by appending calculated causal Entities and Relations."""
        probed_reasons = self.probe_causes(scene_model.narration, scene_model.entities, next_scene_text)
        if not probed_reasons:
            return

        target_entity_id = None
        for entity in scene_model.entities:
            if getattr(entity, 'importance', 0) >= 2.0:
                target_entity_id = entity.id
                break

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

        entity_start_idx = len(scene_model.entities) + 1
        for i, cause in enumerate(probed_reasons):
            cause_node_id = f"e_cause_{scene_idx}_{entity_start_idx + i}"

            scene_model.entities.append(Entity(
                id=cause_node_id,
                label=cause["label"],
                type="danger_core" if i % 2 == 0 else "abstract_core",
                importance=1.5,
                scale=1.0,
                emotion="intense" if i % 2 == 0 else "calm"
            ))

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
