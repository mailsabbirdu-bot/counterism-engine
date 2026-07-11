import re
from typing import List, Dict, Any
from .semantic_model import Entity, Quantity, TemporalExpression

class BanglaProcessor:
    def __init__(self):
        self.bn_digits = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')
        self.location_keywords = ['ঢাকা', 'বাংলাদেশ', 'শহর', 'রাজধানী', 'নদী', 'পাহাড়']
        self.org_keywords = ['লিমিটেড', 'কর্পোরেশন', 'অ্যাপল']

    def _to_float(self, val_str: str) -> float:
        clean_str = val_str.translate(self.bn_digits).replace(',', '')
        try:
            return float(clean_str)
        except:
            return 0.0

    def extract_entities(self, text: str) -> List[Entity]:
        entities = []
        # Fallback keyword-based entity extraction for Bangla
        words = text.split()
        for i, word in enumerate(words):
            e_type = None
            if any(kw in word for kw in self.location_keywords):
                e_type = 'location'
            elif any(kw in word for kw in self.org_keywords):
                e_type = 'organization'

            if e_type:
                entities.append(Entity(
                    id=f"bn_e_{i}",
                    label=word.strip('।,'),
                    type=e_type
                ))
        return entities

    def extract_quantities(self, text: str) -> List[Quantity]:
        quantities = []
        # Percentage
        matches = re.finditer(r'([\d০-৯]+)\s?(শতাংশ|%)', text)
        for i, m in enumerate(matches):
            quantities.append(Quantity(
                value=self._to_float(m.group(1)),
                unit='%',
                label=m.group(0)
            ))
        # Large numbers
        matches = re.finditer(r'([\d০-৯]+)\s?(কোটি|লাখ)', text)
        for i, m in enumerate(matches):
            quantities.append(Quantity(
                value=self._to_float(m.group(1)),
                unit=m.group(2),
                label=m.group(0)
            ))
        return quantities

    def extract_temporal(self, text: str) -> List[TemporalExpression]:
        temporal = []
        # Years
        matches = re.finditer(r'(?:১৯|২০)[\d০-৯]{2}', text)
        for m in matches:
            temporal.append(TemporalExpression(
                label=m.group(0),
                value=m.group(0).translate(self.bn_digits),
                type='point'
            ))
        return temporal
