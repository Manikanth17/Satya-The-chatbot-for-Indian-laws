from app.evaluation.metrics import recall_at_k, reciprocal_rank
from app.verification.contradictions import find_potential_conflicts
from app.retrieval.reranker import rerank

def test_retrieval_metrics():
    assert recall_at_k(["a", "b"], ["b", "c"], 2) == 0.5
    assert reciprocal_rank(["x", "b"], ["b"]) == 0.5

def test_reranker_returns_candidates():
    rows = [({"paragraph_id": "p1", "exact_text": "Right to information application"}, 0.2)]
    assert rerank("right to information", rows)[0][0]["paragraph_id"] == "p1"

def test_conflict_flag_is_only_a_review_flag():
    rows = [
        {"paragraph_id": "a", "exact_text": "The authority shall provide the requested information."},
        {"paragraph_id": "b", "exact_text": "The authority shall not provide the requested information."},
    ]
    assert find_potential_conflicts(rows)
