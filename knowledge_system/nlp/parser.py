import stanza
from typing import Any

class Parser:
    def __init__(self, lang='en'):
        # POS and depparse are enough for dependency analysis and entity extraction rules
        self.lang = lang
        self.nlp = None
        try:
            self.nlp = stanza.Pipeline(lang=lang, processors='tokenize,pos,lemma,depparse', verbose=False, use_gpu=False)
        except Exception as e:
            print(f"Stanza Parser initialization failed for {lang}: {e}")
            if lang == 'en':
                print(f"Retrying download for {lang}...")
                try:
                    stanza.download(lang, processors='tokenize,pos,lemma,depparse', verbose=False)
                    self.nlp = stanza.Pipeline(lang=lang, processors='tokenize,pos,lemma,depparse', verbose=False, use_gpu=False)
                except: pass

    def parse(self, text: str) -> Any:
        if self.nlp:
            return self.nlp(text)

        # Fake doc structure for failed parser
        from types import SimpleNamespace
        return SimpleNamespace(sentences=[])
