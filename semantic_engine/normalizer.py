import re

def normalize_text(text: str) -> str:
    if not text:
        return ""
    # Basic cleaning
    text = text.strip()
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    # Note: For some visualization purposes we might want to keep case,
    # but for NLP processing we often lower it.
    return text
