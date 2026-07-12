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
            'inside': 'spatial_containment',
            'located in': 'located_in',
            'built by': 'built_by',
            'owned by': 'owned_by',
            'increases': 'amplifies',
            'decreases': 'diminishes',
            'কারণে': 'caused_by',
            'ফলে': 'results_in',
            'অংশ': 'membership',
            'ভিতরে': 'spatial_containment',
            'তৈরি': 'built_by',
            'অবস্থিত': 'located_in'
        }

    def extract(self, text: str, entities: List[Any], actions: List[Any]) -> List[Relation]:
        relations = []
        rel_id_counter = 1
        text_lower = text.lower()

        # 1. Action-based relations (Subject -> Action -> Object)
        for action in actions:
            if action.subject_id and action.object_id:
                # subject_id and object_id might be labels if not resolved, or e_ids
                src_id = action.subject_id if action.subject_id.startswith('e_') or action.subject_id.startswith('bn_e_') else self._find_entity_id(action.subject_id, entities)
                tgt_id = action.object_id if action.object_id.startswith('e_') or action.object_id.startswith('bn_e_') else self._find_entity_id(action.object_id, entities)

                if src_id and tgt_id:
                    relations.append(Relation(
                        id=f"r_{rel_id_counter}",
                        source_id=src_id,
                        target_id=tgt_id,
                        relationship=action.label
                    ))
                    rel_id_counter += 1

        # 2. Keyword-based relations (Proximity search)
        for kw, rel_type in self.rel_keywords.items():
            if kw in text_lower:
                # Find entities closest to this keyword
                parts = text_lower.split(kw)
                if len(parts) >= 2:
                    left_text = parts[0]
                    right_text = parts[1]

                    src_id = self._find_entity_id_in_text(left_text, entities, last=True)
                    tgt_id = self._find_entity_id_in_text(right_text, entities, last=False)

                    if src_id and tgt_id and src_id != tgt_id:
                        relations.append(Relation(
                            id=f"r_{rel_id_counter}",
                            source_id=src_id,
                            target_id=tgt_id,
                            relationship=rel_type
                        ))
                        rel_id_counter += 1

        return relations

    def _find_entity_id_in_text(self, text: str, entities: List[Any], last: bool = False) -> str:
        found = []
        for e in entities:
            if e.label.lower() in text:
                pos = text.rfind(e.label.lower()) if last else text.find(e.label.lower())
                found.append((pos, e.id))

        if not found: return None
        found.sort(key=lambda x: x[0], reverse=last)
        return found[0][1]

    def _find_entity_id(self, label: str, entities: List[Any]) -> str:
        if not label: return None
        for e in entities:
            if label.lower() in e.label.lower():
                return e.id
        return None
