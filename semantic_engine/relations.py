from typing import List, Any
from .semantic_model import Relation

class RelationExtractor:
    def __init__(self):
        self.rel_keywords = {
            'because': 'causes',
            'therefore': 'results_in',
            'due to': 'caused_by',
            'depends on': 'dependency',
            'part of': 'membership',
            'inside': 'spatial_containment'
        }

    def extract(self, text: str, entities: List[Any], actions: List[Any]) -> List[Relation]:
        relations = []
        rel_id_counter = 1
        text_lower = text.lower()

        # Keyword-based relations between sentences or concepts
        for kw, rel_type in self.rel_keywords.items():
            if kw in text_lower:
                # This is a simplification. Ideally we find the entities around the keyword.
                pass

        # Structural relations from actions (Subject -> Action -> Object)
        for action in actions:
            if action.subject_id and action.object_id:
                # Find entity IDs for subject and object
                src_id = self._find_entity_id(action.subject_id, entities)
                tgt_id = self._find_entity_id(action.object_id, entities)

                if src_id and tgt_id:
                    relations.append(Relation(
                        id=f"r_{rel_id_counter}",
                        source_id=src_id,
                        target_id=tgt_id,
                        relationship=action.label
                    ))
                    rel_id_counter += 1

        return relations

    def _find_entity_id(self, label: str, entities: List[Any]) -> str:
        for e in entities:
            if label.lower() in e.label.lower():
                return e.id
        return None
