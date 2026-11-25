"""End-to-end evidence-first SATYA workflow.

Retrieval is mandatory. LLM drafting is optional and is never allowed to introduce
new evidence IDs. The Java backend must still validate every evidence ID and quote
against its canonical store before displaying a response.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings
from app.retrieval.hybrid_search import HybridRetriever
from app.retrieval.reranker import rerank
from app.verification.claims import make_supported_claims
from app.verification.confidence import retrieval_quality
from app.verification.contradictions import find_potential_conflicts

logger = logging.getLogger("satya.ai.workflow")


def _extractive_claims(matches: list[tuple[dict[str, Any], float]]) -> list[dict[str, Any]]:
    return make_supported_claims(matches, min_score=0.0)


async def answer_question(question: str, corpus_revision: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    settings = get_settings()
    matching_records = [r for r in records if r.get("corpus_revision") == corpus_revision]
    if not matching_records:
        return {
            "schema_version": "satya-chat-v1", "corpus_revision": corpus_revision,
            "status": "refusal", "claims": [], "unanswered_count": 1,
        }

    semantic_model = settings.semantic_model if settings.enable_semantic else None
    try:
        retriever = HybridRetriever(matching_records, semantic_model=semantic_model)
        candidates = retriever.search(question, limit=18)
    except Exception:
        logger.exception("Hybrid retrieval failed; falling back to BM25")
        from app.retrieval.search import EvidenceRetriever
        candidates = EvidenceRetriever(matching_records).search(question, limit=18)

    matches = rerank(question, candidates, limit=6)
    quality = retrieval_quality(matches)
    if not matches or quality["level"] == "none":
        return {
            "schema_version": "satya-chat-v1", "corpus_revision": corpus_revision,
            "status": "refusal", "claims": [], "unanswered_count": 1,
        }

    claims: list[dict[str, Any]]
    if settings.enable_llm:
        try:
            from app.generation.answer_generator import generate_grounded_draft
            passages = [record for record, _score in matches]
            draft = await generate_grounded_draft(question, passages)
            by_id = {str(r.get("paragraph_id")): r for r in passages}
            claims = []
            for idx, item in enumerate(draft.get("claims", []), start=1):
                evidence_ids = [str(x) for x in item.get("evidence_ids", [])]
                if not evidence_ids or any(eid not in by_id for eid in evidence_ids):
                    continue
                # Exact source text is returned as the quote so the Java service can
                # validate it against the canonical paragraph without trusting the LLM.
                for evidence_id in evidence_ids:
                    record = by_id[evidence_id]
                    quote = str(record.get("exact_text", ""))
                    if not quote:
                        continue
                    claims.append({
                        "claim_id": f"llm-claim-{idx}-{len(claims)+1}",
                        "text": str(item.get("text", "")).strip(),
                        "supporting_quotes": [{"evidence_id": evidence_id, "quote": quote}],
                        "support_assessment": "supported",
                    })
            if not claims:
                claims = _extractive_claims(matches)
        except Exception:
            logger.exception("LLM generation failed; using extractive evidence response")
            claims = _extractive_claims(matches)
    else:
        claims = _extractive_claims(matches)

    conflicts = find_potential_conflicts([record for record, _ in matches])
    status = "conflict" if conflicts else ("answered" if claims else "refusal")
    return {
        "schema_version": "satya-chat-v1",
        "corpus_revision": corpus_revision,
        "status": status,
        "claims": claims,
        "unanswered_count": 0 if claims else 1,
    }
