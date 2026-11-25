import re
import hashlib
from typing import Any


def make_supported_claims(matches: list[tuple[dict[str, Any], float]], min_score: float = 0.15) -> list[dict[str, Any]]:
    """Create strictly extractive claims. No unsupported legal text is invented."""
    claims = []
    seen: set[str] = set()
    for record, score in matches:
        if score < min_score:
            continue
        paragraph_id = record.get("paragraph_id", "")
        raw_text = record.get("exact_text", "")
        text = re.sub(r"\s+", " ", raw_text).strip()
        if not paragraph_id or not text or paragraph_id in seen:
            continue
        seen.add(paragraph_id)
        # Keep display text manageable; quote remains an exact substring for backend validation.
        claim_text = text[:1200]
        exact_quote = raw_text[:1200].strip()
        if not exact_quote:
            continue
        short_id = hashlib.sha256(paragraph_id.encode("utf-8")).hexdigest()[:24]
        claims.append({
            "claim_id": f"claim-{short_id}",
            "text": claim_text,
            "supporting_quotes": [{"evidence_id": paragraph_id, "quote": exact_quote}],
            "support_assessment": "supported",
        })
    return claims
