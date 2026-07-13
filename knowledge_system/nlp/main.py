import sys
import json
import re
from typing import List
from .normalizer import normalize_text
from .tokenizer import Tokenizer
from .parser import Parser
from .entities import EntityExtractor
from .numbers import NumberExtractor
from .timeline import TimelineExtractor
from .actions import ActionExtractor
from .relations import RelationExtractor
from .scene_classifier import SceneClassifier
from .semantic_model import SemanticSceneModel
from .graph_builder import GraphBuilder
from .bn_processor import BanglaProcessor

class SemanticEngine:
    def __init__(self, lang=None):
        self.default_lang = lang
        self._engines = {} # Cache for language-specific engines

    def _get_lang_engines(self, lang):
        if lang not in self._engines:
            print(f"Initializing NLP engines for: {lang}")
            self._engines[lang] = {
                'tokenizer': Tokenizer(lang=lang),
                'parser': Parser(lang=lang),
            }
        return self._engines[lang]

    def _detect_lang(self, text: str) -> str:
        if self.default_lang: return self.default_lang
        # Simple check for Bangla characters
        if any("\u0980" <= char <= "\u09FF" for char in text):
            return 'bn'
        return 'en'

    def _split_scenes(self, text: str) -> List[tuple]:
        # Regex for markers like 'দৃশ্য ১', 'Scene 1', 'দৃশ্য 1'
        pattern = r'(?:দৃশ্য\s*[০-৯\d]+|Scene\s*\d+)'
        markers = re.findall(pattern, text)
        segments = re.split(pattern, text)

        # segments[0] is usually empty or intro before first scene marker
        # pair markers with their following segments
        scenes = []
        for i, marker in enumerate(markers):
            idx = i + 1
            if idx < len(segments):
                scene_text = segments[idx].strip()
                if scene_text:
                    scenes.append((marker, scene_text))

        if not scenes: # Fallback if no markers found
            scenes.append(("scene_1", text))
        return scenes

    def process(self, text: str) -> dict:
        # 1. Normalization
        text = normalize_text(text)

        # 2. Scene Splitting
        scene_segments = self._split_scenes(text)

        # 3. Process Each Scene
        all_scene_models = []

        for scene_marker, scene_text in scene_segments:
            # A. Language Detection
            lang = self._detect_lang(scene_text)
            engines = self._get_lang_engines(lang)

            # B. Parsing (Stanza doc)
            doc = engines['parser'].parse(scene_text)

            # C. Extraction
            if lang == 'bn':
                bn_proc = BanglaProcessor()
                entities = bn_proc.extract_entities(scene_text)
                quantities = bn_proc.extract_quantities(scene_text, entities=entities)
                temporal = bn_proc.extract_temporal(scene_text)
                actions = bn_proc.extract_actions(scene_text, entities)
                relations = bn_proc.extract_relations(scene_text, entities)
            else:
                self.entity_extractor = EntityExtractor()
                entities = self.entity_extractor.extract(doc)

                self.number_extractor = NumberExtractor()
                quantities = self.number_extractor.extract(scene_text)

                self.timeline_extractor = TimelineExtractor()
                temporal = self.timeline_extractor.extract(scene_text)

                self.action_extractor = ActionExtractor()
                actions = self.action_extractor.extract(doc, entities=entities)

                self.relation_extractor = RelationExtractor()
                relations = self.relation_extractor.extract(scene_text, entities, actions)

            self.scene_classifier = SceneClassifier()
            classification = self.scene_classifier.classify(scene_text)

            # D. Build Scene Model
            model = SemanticSceneModel(
                scene_id=scene_marker.replace(" ", "_"),
                narration=scene_text,
                entities=entities,
                actions=actions,
                quantities=quantities,
                temporal_expressions=temporal,
                relations=relations,
                scene_type=classification['scene_type'],
                emotional_tone=classification['emotional_tone']
            )
            all_scene_models.append(model)

        # 4. Build Unified Multi-Scene Model
        # (For now we return a list, but we could build a master graph)
        self.graph_builder = GraphBuilder()
        # Build graph from ALL scenes merged or first scene for legacy
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
