"""Optional semantic retrieval using sentence-transformers.
Install requirements-advanced.txt to enable this module.
"""
from __future__ import annotations
from typing import Any

class SemanticRetriever:
    def __init__(self, records: list[dict[str, Any]], model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("Semantic retrieval dependencies missing; install requirements-advanced.txt") from exc
        self._np = np
        self.records = records
        self.model = SentenceTransformer(model_name)
        texts = [str(r.get("exact_text", "")) for r in records]
        self.matrix = self.model.encode(texts, normalize_embeddings=True) if texts else np.empty((0, 0))

    def search(self, query: str, limit: int = 8) -> list[tuple[dict[str, Any], float]]:
        if not self.records:
            return []
        q = self.model.encode([query], normalize_embeddings=True)[0]
        scores = self.matrix @ q
        ranked = self._np.argsort(scores)[::-1][:limit]
        return [(self.records[int(i)], float(scores[int(i)])) for i in ranked]
