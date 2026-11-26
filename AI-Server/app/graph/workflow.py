"""Evidence-first SATYA workflow.

Retrieval is mandatory. Claims must pass conservative textual screening.
The Java backend remains responsible for canonical evidence validation.
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
from app.verification.evidence_support import assess_claim_support

logger = logging.getLogger("satya.ai.workflow")


def _extractive_claims(
    matches: list[tuple[dict[str, Any], float]]
) -> list[dict[str, Any]]:
    return make_supported_claims(matches, min_score=0.0)


def _filter_supported_claims(
    claims: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    """Keep only supported claims and count rejected claims."""

    supported = []
    unanswered = 0

    for claim in claims:
        if claim.get("support_assessment") == "supported":
            supported.append(claim)
        else:
            unanswered += 1

    return supported[:12], unanswered


async def answer_question(
    question: str,
    corpus_revision: str,
    records: list[dict[str, Any]],
) -> dict[str, Any]:

    settings = get_settings()

    matching_records = [
        r for r in records
        if r.get("corpus_revision") == corpus_revision
    ]

    if not matching_records:
        return {
            "schema_version": "satya-chat-v1",
            "corpus_revision": corpus_revision,
            "status": "refusal",
            "claims": [],
            "unanswered_count": 1,
        }

    semantic_model = (
        settings.semantic_model
        if settings.enable_semantic
        else None
    )

    try:
        retriever = HybridRetriever(
            matching_records,
            semantic_model=semantic_model,
        )

        candidates = retriever.search(question, limit=18)

    except Exception:
        logger.exception(
            "Hybrid retrieval failed; falling back to BM25"
        )

        from app.retrieval.search import EvidenceRetriever

        candidates = EvidenceRetriever(
            matching_records
        ).search(question, limit=18)

    matches = rerank(question, candidates, limit=6)

    quality = retrieval_quality(matches)

    if not matches or quality["level"] == "none":
        return {
            "schema_version": "satya-chat-v1",
            "corpus_revision": corpus_revision,
            "status": "refusal",
            "claims": [],
            "unanswered_count": 1,
        }

    claims: list[dict[str, Any]] = []
    unanswered_count = 0

    # LLM generation path
    if settings.enable_llm:

        try:
            from app.generation.answer_generator import (
                generate_grounded_draft,
            )

            passages = [
                record for record, _score in matches
            ]

            draft = await generate_grounded_draft(
                question,
                passages,
            )

            by_id = {
                str(r.get("paragraph_id")): r
                for r in passages
            }

            generated_claims = draft.get("claims", [])

            for idx, item in enumerate(
                generated_claims,
                start=1,
            ):

                if len(claims) >= 12:
                    unanswered_count += (
                        len(generated_claims) - idx + 1
                    )
                    break

                evidence_ids = [
                    str(x)
                    for x in item.get("evidence_ids", [])
                ]

                claim_text = str(
                    item.get("text", "")
                ).strip()[:2000]

                if not claim_text or not evidence_ids:
                    unanswered_count += 1
                    continue

                accepted_claim = None

                for evidence_id in evidence_ids:

                    record = by_id.get(evidence_id)

                    if record is None:
                        continue

                    assessment = assess_claim_support(
                        claim_text,
                        record,
                    )

                    if assessment == "supported":

                        quote = str(
                            record.get("exact_text", "")
                        )

                        if not quote:
                            continue

                        accepted_claim = {
                            "claim_id": (
                                f"llm-claim-{idx}"
                            ),
                            "text": claim_text,
                            "supporting_quotes": [
                                {
                                    "evidence_id": evidence_id,
                                    "quote": quote,
                                }
                            ],
                            "support_assessment": "supported",
                        }

                        break

                if accepted_claim:
                    claims.append(accepted_claim)
                else:
                    unanswered_count += 1

            if not claims and unanswered_count == 0:
                unanswered_count = 1

        except Exception:
            logger.exception(
                "LLM generation failed; using extractive evidence"
            )

            claims = _extractive_claims(matches)

    else:
        claims = _extractive_claims(matches)

    # Screen extractive claims and any remaining generated claims.
    supported_claims, rejected_count = (
        _filter_supported_claims(claims)
    )

    unanswered_count += rejected_count

    # Identify potential contradictions for human review.
    conflicts = find_potential_conflicts(
        [record for record, _score in matches]
    )

    if not supported_claims:
        status = "refusal"

    elif conflicts and len(supported_claims) >= 2:
        status = "conflict"

    elif unanswered_count > 0:
        status = "partial"

    else:
        status = "answered"

    return {
        "schema_version": "satya-chat-v1",
        "corpus_revision": corpus_revision,
        "status": status,
        "claims": supported_claims,
        "unanswered_count": unanswered_count,
    }