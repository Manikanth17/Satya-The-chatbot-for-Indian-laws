import re

_STOP_WORDS = {"the", "a", "an", "is", "are", "was", "were", "of", "to", "in", "for", "on", "and", "or", "by", "with", "what", "how", "when", "where", "which", "who", "does", "do", "can", "under", "from", "it", "this", "that"}


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9₹]+", text.lower())
    return [w for w in words if len(w) > 1 and w not in _STOP_WORDS]
