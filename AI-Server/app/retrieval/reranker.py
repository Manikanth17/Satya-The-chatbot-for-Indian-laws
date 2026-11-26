"""Deterministic relevance reranker for SATYA.

This module improves retrieval relevance. It does not verify
legal correctness or establish that evidence entails a claim.
"""

from __future__ import annotations

import re
from typing import Any

from app.retrieval.tokenizer import tokenize


def rerank(
    query: str,
    candidates: list[tuple[dict[str, Any], float]],
    limit: int = 6,
) -> list[tuple[dict[str, Any], float]]:
    """Filter weak matches and rank relevant evidence passages."""

    query_terms = set(tokenize(query))

    if not query_terms or not candidates:
        return []

    # Require at least two matching terms for multi-term questions.
    # For a one-term question, require that one term.
    minimum_matches = min(2, len(query_terms))

    scored: list[tuple[dict[str, Any], float]] = []

    for record, base_score in candidates:
        text = str(record.get("exact_text", ""))
        paragraph_terms = set(tokenize(text))

        matched_terms = query_terms.intersection(paragraph_terms)
        match_count = len(matched_terms)

        # Remove passages that match too few question terms.
        if match_count < minimum_matches:
            continue

        coverage = match_count / len(query_terms)

        # Reward passages that cover more of the question.
        relevance_bonus = coverage * 0.5

        # Small bonus for an exact phrase match.
        phrase_bonus = 0.15 if (
            query.strip()
            and re.search(re.escape(query.strip()), text, re.IGNORECASE)
        ) else 0.0

        final_score = float(base_score) + relevance_bonus + phrase_bonus

        scored.append((record, final_score))

    scored.sort(key=lambda item: item[1], reverse=True)

    return scored[:limit]