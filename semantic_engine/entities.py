import regex as re
from typing import List, Any
from .semantic_model import Entity

class EntityExtractor:
    def __init__(self):
        # Rule-based patterns for named entities
        self.type_patterns = {
            'location': ['north', 'south', 'east', 'west', 'city', 'country', 'ocean', 'river', 'mountain', 'ঢাকা', 'বাংলাদেশ', 'শহর', 'নগরী', 'গ্রাম', 'বিভাগ'],
            'organization': ['inc', 'corp', 'limited', 'university', 'agency', 'foundation', 'লিমিটেড', 'কর্পোরেশন', 'দল', 'প্রতিষ্ঠান', 'সংস্থা'],
            'metric': ['percent', 'million', 'billion', 'ratio', 'index', 'শতাংশ', 'কোটি', 'লক্ষ', 'হাজার', 'মিটার', 'কিমি', 'কেজি'],
            'event': ['war', 'battle', 'anniversary', 'festival', 'summit', 'যুদ্ধ', 'উৎসব', 'আক্রমণ', 'বিস্ফোরণ', 'ঘটনা'],
            'person': ['mr', 'ms', 'dr', 'prof', 'মন্ত্রী', 'প্রধানমন্ত্রী', 'শেখ', 'মোহাম্মদ'],
            'object': ['tower', 'building', 'bridge', 'vehicle', 'phone', 'ঘড়ি', 'সেতু', 'দালান', 'গাড়ি']
        }

    def extract(self, doc: Any) -> List[Entity]:
        entities = []
        entity_id_counter = 1

        # Extract from Stanza doc using POS tags (PROPN or NOUN as fallback for some langs)
        for sent in doc.sentences:
            current_entity_tokens = []
            for word in sent.words:
                # In Bangla, proper nouns are often tagged as NOUN.
                is_prop = (word.upos == 'PROPN') or (word.upos == 'NOUN' and any("\u0980" <= char <= "\u09FF" for char in word.text) and len(word.text) > 1)

                if is_prop:
                    current_entity_tokens.append(word.text)
                else:
                    if current_entity_tokens:
                        label = " ".join(current_entity_tokens)
                        e_type = self._determine_type(label)
                        entities.append(Entity(
                            id=f"e_{entity_id_counter}",
                            label=label,
                            type=e_type
                        ))
                        entity_id_counter += 1
                        current_entity_tokens = []

            # Catch trailing entity
            if current_entity_tokens:
                label = " ".join(current_entity_tokens)
                entities.append(Entity(
                    id=f"e_{entity_id_counter}",
                    label=label,
                    type=self._determine_type(label)
                ))
                entity_id_counter += 1

        return entities

    def _determine_type(self, label: str) -> str:
        label_lower = label.lower()
        for e_type, patterns in self.type_patterns.items():
            if any(kw in label_lower for kw in patterns):
                return e_type
        return "concept"
