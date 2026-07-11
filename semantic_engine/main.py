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

class SemanticEngine:
    def __init__(self, lang='en'):
        self.tokenizer = Tokenizer(lang=lang)
        self.parser = Parser(lang=lang)
        self.entity_extractor = EntityExtractor()
        self.number_extractor = NumberExtractor()
        self.timeline_extractor = TimelineExtractor()
        self.action_extractor = ActionExtractor()
        self.relation_extractor = RelationExtractor()
        self.scene_classifier = SceneClassifier()
        self.graph_builder = GraphBuilder()

    def process(self, text: str, scene_id: str = "scene_1") -> dict:
        # 1. Normalization
        text = normalize_text(text)

        # 2. Parsing (Stanza doc)
        doc = self.parser.parse(text)

        # 3. Extraction
        entities = self.entity_extractor.extract(doc)
        quantities = self.number_extractor.extract(text)
        temporal = self.timeline_extractor.extract(text)
        actions = self.action_extractor.extract(doc)
        relations = self.relation_extractor.extract(text, entities, actions)
        classification = self.scene_classifier.classify(text)

        # 4. Build Model
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

        # 5. Build Graph
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
