"""Transparent retrieval confidence heuristic, not probability of legal correctness."""
from __future__ import annotations
from typing import Any

def retrieval_quality(matches: list[tuple[dict[str, Any], float]]) -> dict[str, Any]:
    if not matches:
        return {"level": "none", "score": 0.0, "explanation": "No matching passages found."}
    top = max(float(score) for _, score in matches)
    count = len(matches)
    # BM25/RRF scales differ; this is only a relative signal for UI/review.
    level = "low" if count < 2 else "medium" if count < 4 else "high"
    return {"level": level, "score": round(min(count / 6, 1.0), 2), "top_retrieval_score": round(top, 4), "explanation": "Retrieval coverage heuristic only; not a confidence score for legal correctness."}
