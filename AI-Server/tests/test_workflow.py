import asyncio
from types import SimpleNamespace

import pytest

from app.graph import workflow


def make_record(paragraph_id, text):
    return {
        "paragraph_id": paragraph_id,
        "document_id": "rti-act",
        "corpus_revision": "test-v1",
        "exact_text": text,
    }


@pytest.fixture
def setup_workflow(monkeypatch):
    record = make_record(
        "rti-act-p0001",
        "The application fee shall be rupees ten.",
    )

    monkeypatch.setattr(
        workflow,
        "get_settings",
        lambda: SimpleNamespace(
            enable_semantic=False,
            semantic_model=None,
            enable_llm=True,
        ),
    )

    monkeypatch.setattr(
        workflow,
        "HybridRetriever",
        lambda *args, **kwargs: SimpleNamespace(
            search=lambda *a, **k: [(record, 1.0)]
        ),
    )

    monkeypatch.setattr(
        workflow,
        "rerank",
        lambda question, candidates, limit: candidates,
    )

    monkeypatch.setattr(
        workflow,
        "retrieval_quality",
        lambda matches: {"level": "high"},
    )

    monkeypatch.setattr(
        workflow,
        "find_potential_conflicts",
        lambda records: [],
    )

    return record


def test_exact_llm_claim_is_answered(setup_workflow, monkeypatch):
    record = setup_workflow

    async def fake_generate(question, passages):
        return {
            "claims": [{
                "text": record["exact_text"],
                "evidence_ids": [record["paragraph_id"]],
            }]
        }

    from app.generation import answer_generator

    monkeypatch.setattr(
        answer_generator,
        "generate_grounded_draft",
        fake_generate,
    )

    result = asyncio.run(
        workflow.answer_question(
            "What is the application fee?",
            "test-v1",
            [record],
        )
    )

    assert result["status"] == "answered"
    assert len(result["claims"]) == 1


def test_unsupported_llm_claim_is_refused(setup_workflow, monkeypatch):
    record = setup_workflow

    async def fake_generate(question, passages):
        return {
            "claims": [{
                "text": "The photocopying fee is two rupees per page.",
                "evidence_ids": [record["paragraph_id"]],
            }]
        }

    from app.generation import answer_generator

    monkeypatch.setattr(
        answer_generator,
        "generate_grounded_draft",
        fake_generate,
    )

    result = asyncio.run(
        workflow.answer_question(
            "What is the photocopying fee?",
            "test-v1",
            [record],
        )
    )

    assert result["status"] == "refusal"
    assert result["claims"] == []
    assert result["unanswered_count"] == 1


def test_supported_and_unsupported_claims_return_partial(
    setup_workflow,
    monkeypatch,
):
    record = setup_workflow

    async def fake_generate(question, passages):
        return {
            "claims": [
                {
                    "text": record["exact_text"],
                    "evidence_ids": [record["paragraph_id"]],
                },
                {
                    "text": "The photocopying fee is two rupees per page.",
                    "evidence_ids": [record["paragraph_id"]],
                },
            ]
        }

    from app.generation import answer_generator

    monkeypatch.setattr(
        answer_generator,
        "generate_grounded_draft",
        fake_generate,
    )

    result = asyncio.run(
        workflow.answer_question(
            "Tell me about RTI fees.",
            "test-v1",
            [record],
        )
    )

    assert result["status"] == "partial"
    assert len(result["claims"]) == 1
    assert result["unanswered_count"] == 1


def test_conflicting_evidence_returns_conflict(
    setup_workflow,
    monkeypatch,
):
    first = make_record(
        "rti-act-p0001",
        "The application fee shall be rupees ten.",
    )

    second = make_record(
        "rti-act-p0002",
        "The application fee shall be rupees twenty.",
    )

    monkeypatch.setattr(
        workflow,
        "HybridRetriever",
        lambda *args, **kwargs: SimpleNamespace(
            search=lambda *a, **k: [
                (first, 1.0),
                (second, 0.9),
            ]
        ),
    )

    monkeypatch.setattr(
        workflow,
        "find_potential_conflicts",
        lambda records: [{"type": "potential_conflict"}],
    )

    async def fake_generate(question, passages):
        return {
            "claims": [
                {
                    "text": first["exact_text"],
                    "evidence_ids": [first["paragraph_id"]],
                },
                {
                    "text": second["exact_text"],
                    "evidence_ids": [second["paragraph_id"]],
                },
            ]
        }

    from app.generation import answer_generator

    monkeypatch.setattr(
        answer_generator,
        "generate_grounded_draft",
        fake_generate,
    )

    result = asyncio.run(
        workflow.answer_question(
            "What is the application fee?",
            "test-v1",
            [first, second],
        )
    )

    assert result["status"] == "conflict"
    assert len(result["claims"]) == 2