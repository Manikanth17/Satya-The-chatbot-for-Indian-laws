"""Hybrid BM25 + semantic retrieval with a safe lexical fallback."""
from __future__ import annotations
from typing import Any
from app.retrieval.search import EvidenceRetriever

class HybridRetriever:
    def __init__(self, records: list[dict[str, Any]], semantic_model: str | None = None):
        self.records = records
        self.lexical = EvidenceRetriever(records)
        self.semantic = None
        if semantic_model:
            from app.retrieval.semantic_search import SemanticRetriever
            self.semantic = SemanticRetriever(records, semantic_model)

    def search(self, query: str, limit: int = 8) -> list[tuple[dict[str, Any], float]]:
        lexical = self.lexical.search(query, limit=max(limit * 3, 20))
        if self.semantic is None:
            return lexical[:limit]
        semantic = self.semantic.search(query, limit=max(limit * 3, 20))
        # Reciprocal-rank fusion avoids comparing BM25 and cosine score scales directly.
        fused: dict[str, dict[str, Any]] = {}
        for rank, (record, _) in enumerate(lexical, 1):
            key = str(record.get("paragraph_id", ""))
            if key:
                fused.setdefault(key, {"record": record, "score": 0.0})["score"] += 1.0 / (60 + rank)
        for rank, (record, _) in enumerate(semantic, 1):
            key = str(record.get("paragraph_id", ""))
            if key:
                fused.setdefault(key, {"record": record, "score": 0.0})["score"] += 1.0 / (60 + rank)
        ranked = sorted(fused.values(), key=lambda x: x["score"], reverse=True)[:limit]
        return [(x["record"], float(x["score"])) for x in ranked]
