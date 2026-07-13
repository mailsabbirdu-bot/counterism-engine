import regex as re
from typing import List
from .semantic_model import TemporalExpression

class TimelineExtractor:
    def __init__(self):
        self.markers = {
            'yesterday': 'past',
            'today': 'present',
            'tomorrow': 'future',
            'ago': 'past',
            'since': 'range_start',
            'until': 'range_end',
            'before': 'relative_past',
            'after': 'relative_future',
            'soon': 'near_future'
        }

    def extract(self, text: str) -> List[TemporalExpression]:
        expressions = []
        text_lower = text.lower()

        for word, t_type in self.markers.items():
            if re.search(fr'\b{word}\b', text_lower):
                expressions.append(TemporalExpression(
                    label=word,
                    type=t_type
                ))

        # Also catch years as temporal points
        years = re.findall(r'\b(19|20)\d{2}\b', text)
        for year in years:
            # Re-build the year string since findall with groups returns tuples or partials
            # Actually \b(19|20)\d{2}\b will find the whole 4 digits if we use it right
            pass

        # Refined year search
        years_full = re.findall(r'\b(?:19|20)\d{2}\b', text)
        for year in years_full:
            expressions.append(TemporalExpression(
                label=year,
                value=year,
                type="point"
            ))

        return expressions
