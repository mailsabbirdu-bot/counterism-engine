import re
from typing import List, Dict, Any
from .semantic_model import Entity, Quantity, TemporalExpression, Action, Relation

class BanglaProcessor:
    def __init__(self):
        self.bn_digits = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')
        self.bn_num_map = {'এক': 1, 'দুই': 2, 'তিন': 3, 'চার': 4, 'পাঁচ': 5, 'ছয়': 6, 'সাত': 7, 'আট': 8, 'নয়': 9, 'দশ': 10}

        self.location_keywords = ['ঢাকা', 'বাংলাদেশ', 'শহর', 'রাজধানী', 'নদী']
        self.org_keywords = ['লিমিটেড', 'কর্পোরেশন', 'অ্যাপল', 'সাম্রাজ্য']
        self.concept_keywords = ['প্ল্যানেট', 'মানুষ', 'মানুষের', 'টাইমবোম্ব', 'জিওলজিক্যাল টাইমবোম্ব', 'জিওলজিক্যাল ক্লক', 'টিকটিক শব্দ', 'ক্লক']
        self.urban_keywords = ['মেগাসিটি', 'মেগাসি']
        self.material_keywords = ['কংক্রিট', 'কংক্রিটের']
        self.metaphor_keywords = ['পাহাড়']

        self.action_keywords = {
            'বাঁচছে': 'live', 'লড়ছে': 'fight', 'বানাচ্ছে': 'build',
            'লুকিয়ে আছে': 'hidden', 'হচ্ছে': 'become', 'রিপোর্ট করেছে': 'report'
        }

    def _to_float(self, val_str: str) -> float:
        clean_str = val_str.translate(self.bn_digits).replace(',', '')
        try:
            return float(clean_str)
        except:
            return 0.0

    def _normalize_label(self, label: str) -> str:
        # Basic normalization for Bangla cases/inflections
        # মানুষের -> মানুষ, বাংলাদেশের -> বাংলাদেশ, সাম্রাজ্যের -> সাম্রাজ্য
        label = label.strip('।!, ')

        # Suffix processing (with semantic safeguards)
        suffixes = ['ের', 'র', 'টি', 'কে', 'টির', 'গুলো', 'গুলোে']

        # Words that should NEVER have their suffix stripped
        protected_roots = ['ঢাকা', 'মেগাসি', 'বিশা', 'মা', 'পা', 'শহ', 'নগ', 'শহর', 'নগর']

        # Sort by length descending to match longest first
        for s in sorted(suffixes, key=len, reverse=True):
            if label.endswith(s):
                root = label[:-len(s)]
                if root in protected_roots:
                     continue
                if len(root) >= 2:
                    label = root
                    break

        # Specific overrides for multi-word
        if label == 'মেগাসি': return 'মেগাসিটি'
        if label == 'বিশা': return 'বিশাল'
        return label

    def extract_entities(self, text: str) -> List[Entity]:
        entities_map = {} # normalized_label -> Entity

        all_kws = [
            (self.location_keywords, 'location'),
            (self.org_keywords, 'organization'),
            (self.concept_keywords, 'concept'),
            (self.urban_keywords, 'urban_concept'),
            (self.material_keywords, 'material'),
            (self.metaphor_keywords, 'metaphor')
        ]

        # 1. Multi-word search (Primary)
        # We search raw text for keywords, then normalize the result
        combined_kws = []
        for kw_list, e_type in all_kws:
            for kw in kw_list:
                combined_kws.append((kw, e_type))
        combined_kws.sort(key=lambda x: len(x[0]), reverse=True)

        for kw, e_type in combined_kws:
            if kw in text:
                norm = self._normalize_label(kw)
                if norm not in entities_map:
                    # Prevent redundant substring matches
                    if any(norm in existing for existing in entities_map):
                        continue

                    importance = 1.0
                    if e_type == 'location': importance = 1.5
                    if norm in ['ঢাকা', 'মেগাসিটি', 'টাইমবোম্ব', 'জিওলজিক্যাল টাইমবোম্ব']: importance = 2.0

                    emotion = 'calm'
                    if norm in ['লড়াই', 'সংকট', 'টাইমবোম্ব', 'জিওলজিক্যাল টাইমবোম্ব', 'তীব্র']: emotion = 'intense'

                    entities_map[norm] = Entity(
                        id=f"bn_e_{len(entities_map)}",
                        label=norm,
                        type=e_type,
                        importance=importance,
                        emotion=emotion,
                        scale=1.5 if norm == 'বিশাল' else 1.0
                    )

        # 2. Contextual word discovery (Fallback)
        # Process every word in the text that wasn't caught by keywords
        words = text.split()
        for word in words:
            clean = word.strip('।!, ')
            if len(clean) < 2: continue

            norm = self._normalize_label(clean)
            if norm in entities_map: continue

            # Check if this concept is meaningful
            is_significant = any(norm in kw for kw in self.location_keywords + self.org_keywords + self.concept_keywords)

            if is_significant:
                if any(norm in existing for existing in entities_map): continue

                entities_map[norm] = Entity(
                    id=f"bn_e_{len(entities_map)}",
                    label=norm,
                    type='concept'
                )
        return list(entities_map.values())

    def extract_actions(self, text: str) -> List[Action]:
        actions = []
        for kw, label in self.action_keywords.items():
            for match in re.finditer(re.escape(kw), text):
                actions.append(Action(
                    id=f"bn_a_{len(actions)}",
                    label=label,
                    importance=1.2
                ))
        return actions

    def extract_relations(self, text: str, entities: List[Entity]) -> List[Relation]:
        relations = []
        rel_id_counter = 1

        # Helper to find entity by partial label
        def find_e(label):
            norm = self._normalize_label(label)
            for e in entities:
                if norm == e.label or e.label in norm: return e
            return None

        # 1. Multi-Scene Logical Relations
        if find_e('ঢাকা') and find_e('মেগাসিটি'):
             relations.append(Relation(id=f"bn_r_{rel_id_counter}", source_id=find_e("ঢাকা").id, target_id=find_e("মেগাসিটি").id, relationship="is_a"))
             rel_id_counter += 1

        if find_e('সাম্রাজ্য') and find_e('টাইমবোম্ব'):
             relations.append(Relation(id=f"bn_r_{rel_id_counter}", source_id=find_e("সাম্রাজ্য").id, target_id=find_e("টাইমবোম্ব").id, relationship="hidden_under"))
             rel_id_counter += 1

        if find_e('মানুষ') and find_e('সাম্রাজ্য'):
             relations.append(Relation(id=f"bn_r_{rel_id_counter}", source_id=find_e("মানুষ").id, target_id=find_e("সাম্রাজ্য").id, relationship="built_by"))
             rel_id_counter += 1

        return relations

    def extract_quantities(self, text: str) -> List[Quantity]:
        quantities = []
        # 1. Digital Numbers
        # Percentage
        for m in re.finditer(r'([\d০-৯]+)\s?(শতাংশ|%)', text):
            quantities.append(Quantity(value=self._to_float(m.group(1)), unit='%', label=m.group(0)))

        # Large numbers (Digital)
        for m in re.finditer(r'([\d০-৯]+)\s?(কোটি|লাখ|বিলিয়ন|মিলিয়ন)', text):
            quantities.append(Quantity(value=self._to_float(m.group(1)), unit=m.group(2), label=m.group(0)))

        # 2. Textual Numbers
        for bn_word, val in self.bn_num_map.items():
            # Check for patterns like "দুই কোটির"
            for m in re.finditer(fr'{bn_word}\s?(কোটি|লাখ|শতাংশ|%)', text):
                quantities.append(Quantity(
                    value=float(val),
                    unit=m.group(1),
                    label=m.group(0)
                ))
        return quantities

    def extract_temporal(self, text: str) -> List[TemporalExpression]:
        temporal = []
        # 1. Years
        for m in re.finditer(r'(?:১৯|২০)[\d০-৯]{2}', text):
            temporal.append(TemporalExpression(
                label=m.group(0),
                value=m.group(0).translate(self.bn_digits),
                type='point'
            ))

        # 2. Key temporal terms
        bn_markers = {
            'প্রতিনিয়ত': 'continuous', 'সময়ের সাথে সাথে': 'dynamic',
            'আরও': 'progressive', 'এখন': 'present', 'আগে': 'past'
        }
        for kw, t_type in bn_markers.items():
            if kw in text:
                temporal.append(TemporalExpression(label=kw, type=t_type))
        return temporal
