import math
from collections import Counter
from typing import Any
from app.retrieval.tokenizer import tokenize


class EvidenceRetriever:
    """Small, dependency-light BM25 retriever over reviewed paragraph records."""
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self.records = records
        self.tokens = [tokenize(r.get("exact_text", "")) for r in records]
        self.avgdl = sum(map(len, self.tokens)) / max(len(self.tokens), 1)
        self.df: Counter[str] = Counter()
        for doc in self.tokens:
            self.df.update(set(doc))

    def search(self, query: str, limit: int = 6) -> list[tuple[dict[str, Any], float]]:
        qtokens = set(tokenize(query))
        if not qtokens or not self.records:
            return []
        n = len(self.records)
        scored: list[tuple[dict[str, Any], float]] = []
        k1, b = 1.5, 0.75
        for record, terms in zip(self.records, self.tokens):
            if not terms:
                continue
            counts = Counter(terms)
            dl = len(terms)
            score = 0.0
            for term in qtokens:
                tf = counts.get(term, 0)
                if not tf:
                    continue
                df = self.df.get(term, 0)
                idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
                denom = tf + k1 * (1 - b + b * dl / max(self.avgdl, 1))
                score += idf * (tf * (k1 + 1)) / denom
            if score > 0:
                scored.append((record, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:limit]
