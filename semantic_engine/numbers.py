import regex as re
from typing import List, Any
from .semantic_model import Quantity

class NumberExtractor:
    def __init__(self):
        # Regex for currencies, percentages, and simple numbers
        self.money_pattern = r'([\$£€¥৳])\s?([\d,]+\.?\d*)|([\d,]+\.?\d*)\s?([\$£€¥৳]|dollars|taka|euros|pounds)'
        self.percent_pattern = r'([\d,]+\.?\d*)\s?%'
        self.year_pattern = r'\b(19|20)\d{2}\b'

    def extract(self, text: str) -> List[Quantity]:
        quantities = []

        # Percentages
        for match in re.finditer(self.percent_pattern, text):
            quantities.append(Quantity(
                value=float(match.group(1).replace(',', '')),
                unit="%",
                label=match.group(0)
            ))

        # Money
        for match in re.finditer(self.money_pattern, text):
            val_str = match.group(2) or match.group(3)
            unit_str = match.group(1) or match.group(4)
            quantities.append(Quantity(
                value=float(val_str.replace(',', '')),
                unit=unit_str,
                label=match.group(0)
            ))

        return quantities

    def extract_years(self, text: str) -> List[str]:
        return re.findall(self.year_pattern, text)
