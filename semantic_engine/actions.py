from typing import List, Any
from .semantic_model import Action

class ActionExtractor:
    def __init__(self):
        # We focus on main verbs (root and their direct subjects/objects)
        pass

    def extract(self, doc: Any) -> List[Action]:
        actions = []
        action_id_counter = 1

        for sent in doc.sentences:
            for word in sent.words:
                if word.upos == 'VERB':
                    # Find subject and object using dependency relations
                    subject = None
                    obj = None

                    for other in sent.words:
                        if other.head == word.id:
                            if other.deprel in ['nsubj', 'nsubj:pass']:
                                subject = other.text
                            elif other.deprel in ['obj', 'iobj']:
                                obj = other.text

                    actions.append(Action(
                        id=f"a_{action_id_counter}",
                        label=word.lemma,
                        subject_id=subject, # Placeholder for now, ideally linked to Entity ID
                        object_id=obj,
                        importance=1.5 if word.deprel == 'root' else 1.0
                    ))
                    action_id_counter += 1

        return actions
