import sys
import json
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

    def process(self, text: str, scene_id: str = "scene_1") -> dict:
        # 1. Normalization
        text = normalize_text(text)

        # 2. Language Detection
        lang = self._detect_lang(text)
        engines = self._get_lang_engines(lang)

        # 3. Parsing (Stanza doc)
        doc = engines['parser'].parse(text)

        # 4. Extraction
        if lang == 'bn':
            bn_proc = BanglaProcessor()
            entities = bn_proc.extract_entities(text)
            quantities = bn_proc.extract_quantities(text)
            temporal = bn_proc.extract_temporal(text)
            actions = bn_proc.extract_actions(text)
            relations = bn_proc.extract_relations(text, entities)
        else:
            self.entity_extractor = EntityExtractor()
            entities = self.entity_extractor.extract(doc)

            self.number_extractor = NumberExtractor()
            quantities = self.number_extractor.extract(text)

            self.timeline_extractor = TimelineExtractor()
            temporal = self.timeline_extractor.extract(text)

            self.action_extractor = ActionExtractor()
            actions = self.action_extractor.extract(doc)

            self.relation_extractor = RelationExtractor()
            relations = self.relation_extractor.extract(text, entities, actions)

        self.scene_classifier = SceneClassifier()
        classification = self.scene_classifier.classify(text)

        # 5. Build Model
        model = SemanticSceneModel(
            scene_id=scene_id,
            narration=text,
            entities=entities,
            actions=actions,
            quantities=quantities,
            temporal_expressions=temporal,
            relations=relations,
            scene_type=classification['scene_type'],
            emotional_tone=classification['emotional_tone']
        )

        # 6. Build Graph
        self.graph_builder = GraphBuilder()
        G = self.graph_builder.build(model)
        graph_data = self.graph_builder.to_json(G)

        return {
            "model": model.dict(),
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
