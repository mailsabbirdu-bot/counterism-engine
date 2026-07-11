import stanza
from typing import List

# Pre-download minimal models if needed, but in production we'd assume they are cached
# stanza.download('en', processors='tokenize', verbose=False)

class Tokenizer:
    def __init__(self, lang='en'):
        self.lang = lang
        self.nlp = None
        try:
            self.nlp = stanza.Pipeline(lang=lang, processors='tokenize', verbose=False, use_gpu=False)
        except Exception as e:
            print(f"Stanza Tokenizer initialization failed for {lang}: {e}")
            if lang == 'en':
                print(f"Retrying download for {lang}...")
                try:
                    stanza.download(lang, processors='tokenize', verbose=False)
                    self.nlp = stanza.Pipeline(lang=lang, processors='tokenize', verbose=False, use_gpu=False)
                except: pass

    def split_sentences(self, text: str) -> List[str]:
        if self.nlp:
            try:
                doc = self.nlp(text)
                return [sent.text for sent in doc.sentences]
            except: pass

        # Fallback: simple split on punctuation
        import re
        return [s.strip() for s in re.split(r'[।\.!?]', text) if s.strip()]

    def tokenize(self, text: str) -> List[str]:
        if self.nlp:
            try:
                doc = self.nlp(text)
                tokens = []
                for sent in doc.sentences:
                    for token in sent.tokens:
                        tokens.append(token.text)
                return tokens
            except: pass

        # Fallback: simple white-space split
        return text.split()
