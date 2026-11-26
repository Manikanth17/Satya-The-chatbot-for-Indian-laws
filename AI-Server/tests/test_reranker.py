
from app.retrieval.reranker import rerank


def test_keeps_direct_application_fee_evidence():
    direct = {
        "paragraph_id": "fee-001",
        "exact_text": (
            "An application shall be accompanied by a fee "
            "of rupees ten."
        ),
    }

    results = rerank(
        "What is the RTI application fee?",
        [(direct, 5.0)],
    )

    assert len(results) == 1
    assert results[0][0]["paragraph_id"] == "fee-001"


def test_preserves_relevant_bpl_fee_exception():
    exception = {
        "paragraph_id": "fee-002",
        "exact_text": (
            "No fee shall be charged from a person below "
            "poverty line along with the application."
        ),
    }

    results = rerank(
        "What is the RTI application fee?",
        [(exception, 4.0)],
    )

    assert len(results) == 1
    assert results[0][0]["paragraph_id"] == "fee-002"


def test_filters_weak_application_only_match():
    irrelevant = {
        "paragraph_id": "form-001",
        "exact_text": (
            "The application must contain the applicant's "
            "name and address."
        ),
    }

    results = rerank(
        "What is the RTI application fee?",
        [(irrelevant, 5.0)],
    )

    assert results == []


def test_filters_weak_fee_only_match():
    irrelevant = {
        "paragraph_id": "inspection-001",
        "exact_text": (
            "A fee of five rupees shall be charged "
            "for every subsequent hour of inspection."
        ),
    }

    results = rerank(
        "What is the RTI application fee?",
        [(irrelevant, 5.0)],
    )

    assert results == []


def test_empty_query_returns_no_results():
    record = {
        "paragraph_id": "fee-001",
        "exact_text": "Application fee is ten rupees.",
    }

    assert rerank("", [(record, 5.0)]) == []


def test_empty_candidates_return_no_results():
    assert rerank("What is the application fee?", []) == []


def test_single_term_query():
    record = {
        "paragraph_id": "fee-001",
        "exact_text": "The application fee is ten rupees.",
    }

    results = rerank("application", [(record, 2.0)])

    assert len(results) == 1