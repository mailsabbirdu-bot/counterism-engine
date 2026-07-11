import stanza
from typing import List

# Pre-download minimal models if needed, but in production we'd assume they are cached
# stanza.download('en', processors='tokenize', verbose=False)

class Tokenizer:
    def __init__(self, lang='en'):
        self.nlp = stanza.Pipeline(lang=lang, processors='tokenize', verbose=False, use_gpu=False)

    def split_sentences(self, text: str) -> List[str]:
        doc = self.nlp(text)
        return [sent.text for sent in doc.sentences]

    def tokenize(self, text: str) -> List[str]:
        doc = self.nlp(text)
        tokens = []
        for sent in doc.sentences:
            for token in sent.tokens:
                tokens.append(token.text)
        return tokens
