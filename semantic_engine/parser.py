import stanza
from typing import Any

class Parser:
    def __init__(self, lang='en'):
        # POS and depparse are enough for dependency analysis and entity extraction rules
        self.nlp = stanza.Pipeline(lang=lang, processors='tokenize,pos,lemma,depparse', verbose=False, use_gpu=False)

    def parse(self, text: str) -> Any:
        return self.nlp(text)
