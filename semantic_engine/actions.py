from typing import List, Any
from .semantic_model import Action

class ActionExtractor:
    def __init__(self):
        # We focus on main verbs (root and their direct subjects/objects)
        pass

    def extract(self, doc: Any, entities: List[Any] = None) -> List[Action]:
        actions = []
        action_id_counter = 1

        for sent in doc.sentences:
            for word in sent.words:
                if word.upos == 'VERB':
                    # Find subject and object using dependency relations
                    subject_label = None
                    obj_label = None

                    for other in sent.words:
                        if other.head == word.id:
                            if other.deprel in ['nsubj', 'nsubj:pass']:
                                subject_label = other.text
                            elif other.deprel in ['obj', 'iobj']:
                                obj_label = other.text

                    sub_id = self._resolve_id(subject_label, entities) if entities else subject_label
                    obj_id = self._resolve_id(obj_label, entities) if entities else obj_label

                    actions.append(Action(
                        id=f"a_{action_id_counter}",
                        label=word.lemma,
                        subject_id=sub_id,
                        object_id=obj_id,
                        importance=1.5 if word.deprel == 'root' else 1.0
                    ))
                    action_id_counter += 1

        return actions

    def _resolve_id(self, label: str, entities: List[Any]) -> str:
        if not label: return None
        label_lower = label.lower()
        for e in entities:
            if label_lower == e.label.lower() or label_lower in e.label.lower():
                return e.id
        return label
