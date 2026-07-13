import regex as re
from typing import List, Any
from .semantic_model import Quantity

class NumberExtractor:
    def __init__(self):
        # Bangla numeral map
        self.bn_digits = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')
        # Regex for currencies, percentages, and simple numbers (including Bangla)
        self.money_pattern = r'([\$£€¥৳])\s?([\d,০-৯]+\.?[\d০-৯]*)|([\d,০-৯]+\.?[\d০-৯]*)\s?([\$£€¥৳]|dollars|taka|euros|pounds|টাকা|ডলার)'
        self.percent_pattern = r'([\d,০-৯]+\.?[\d০-৯]*)\s?([%]|শতাংশ|পারসেন্ট)'
        self.year_pattern = r'\b(?:19|20)[\d০-৯]{2}\b'
        self.scale_pattern = r'([\d,০-৯]+\.?[\d০-৯]*)\s?(কোটি|লাখ|বিলিয়ন|মিলিয়ন|million|billion|crore|lakh)'

    def _to_float(self, val_str: str) -> float:
        # Convert Bangla digits to English
        clean_str = val_str.translate(self.bn_digits).replace(',', '')
        try:
            return float(clean_str)
        except:
            return 0.0

    def extract(self, text: str) -> List[Quantity]:
        quantities = []

        # Percentages
        for match in re.finditer(self.percent_pattern, text):
            quantities.append(Quantity(
                value=self._to_float(match.group(1)),
                unit="%",
                label=match.group(0)
            ))

        # Money
        for match in re.finditer(self.money_pattern, text):
            val_str = match.group(2) or match.group(3)
            unit_str = match.group(1) or match.group(4)
            quantities.append(Quantity(
                value=self._to_float(val_str),
                unit=unit_str,
                label=match.group(0)
            ))

        # Scaled numbers (Crore, Million etc)
        for match in re.finditer(self.scale_pattern, text):
            val_str = match.group(1)
            unit_str = match.group(2)
            quantities.append(Quantity(
                value=self._to_float(val_str),
                unit=unit_str,
                label=match.group(0)
            ))

        return quantities

    def extract_years(self, text: str) -> List[str]:
        return re.findall(self.year_pattern, text)
