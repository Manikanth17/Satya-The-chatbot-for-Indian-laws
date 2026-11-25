"""Lightweight deterministic reranker; does not assert legal correctness."""
from __future__ import annotations
import re
from typing import Any
from app.retrieval.tokenizer import tokenize

def rerank(query: str, candidates: list[tuple[dict[str, Any], float]], limit: int = 6) -> list[tuple[dict[str, Any], float]]:
    q = set(tokenize(query))
    scored = []
    for record, base in candidates:
        text = str(record.get("exact_text", ""))
        terms = set(tokenize(text))
        overlap = len(q & terms) / max(len(q), 1)
        phrase_bonus = 0.15 if re.search(re.escape(query.strip()), text, re.I) and query.strip() else 0.0
        scored.append((record, float(base) + overlap * 0.25 + phrase_bonus))
    return sorted(scored, key=lambda x: x[1], reverse=True)[:limit]
