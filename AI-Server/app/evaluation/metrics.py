"""Small offline retrieval evaluation helpers."""
from __future__ import annotations
from typing import Iterable

def recall_at_k(ranked_ids: list[str], relevant_ids: Iterable[str], k: int = 5) -> float:
    relevant = set(relevant_ids)
    if not relevant:
        return 1.0
    return len(set(ranked_ids[:k]) & relevant) / len(relevant)

def reciprocal_rank(ranked_ids: list[str], relevant_ids: Iterable[str]) -> float:
    relevant = set(relevant_ids)
    for rank, item in enumerate(ranked_ids, 1):
        if item in relevant:
            return 1.0 / rank
    return 0.0
