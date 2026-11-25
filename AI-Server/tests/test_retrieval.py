import asyncio
from app.graph.workflow import answer_question


def test_answer_contains_only_retrieved_evidence():
    record = {
        "paragraph_id": "rti-act-p0001-para000001",
        "document_id": "rti-act",
        "corpus_revision": "test-v1",
        "exact_text": "A public authority shall provide information in accordance with this Act.",
    }
    result = asyncio.run(answer_question("What must a public authority provide under this Act?", "test-v1", [record]))
    assert result["status"] == "answered"
    assert result["claims"][0]["support_assessment"] == "supported"
    assert result["claims"][0]["supporting_quotes"][0]["quote"] in record["exact_text"]


def test_unknown_question_refuses_without_making_up_answer():
    record = {
        "paragraph_id": "rti-act-p0001-para000001",
        "document_id": "rti-act",
        "corpus_revision": "test-v1",
        "exact_text": "A public authority shall provide information in accordance with this Act.",
    }
    result = asyncio.run(answer_question("What is the weather on Mars?", "test-v1", [record]))
    assert result["status"] == "refusal"
    assert result["claims"] == []


def test_revision_isolation():
    record = {
        "paragraph_id": "rti-act-p0001-para000001",
        "document_id": "rti-act",
        "corpus_revision": "old-v1",
        "exact_text": "A public authority shall provide information in accordance with this Act.",
    }
    result = asyncio.run(answer_question("public authority information", "new-v1", [record]))
    assert result["status"] == "refusal"
