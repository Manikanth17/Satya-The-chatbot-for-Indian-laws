# SATYA AI — remaining modules handoff

This ZIP is an **add-on overlay** for the previously supplied `SATYA-AI-Service` package. Copy/merge its `app/` and `tests/` folders into that service; do not replace the existing `main.py`, `routes.py`, `schemas/chat.py`, `workflow.py`, or base `requirements.txt` blindly.

## Added modules

- `retrieval/semantic_search.py`: optional sentence-transformers semantic retrieval.
- `retrieval/hybrid_search.py`: BM25 + semantic reciprocal-rank fusion.
- `retrieval/reranker.py`: deterministic second-stage ranking.
- `generation/`: OpenAI-compatible LLM client and strict evidence-context prompt/output parser.
- `verification/contradictions.py`: conservative potential-conflict flagging for human review.
- `verification/confidence.py`: retrieval coverage heuristic (not legal confidence).
- `ingestion/ocr_loader.py`: optional scanned-PDF OCR helper.
- `evaluation/`: Recall@K and reciprocal-rank metrics.

## Install

Base service remains runnable with `requirements.txt`. For semantic retrieval and LLM modules:

```bash
pip install -r requirements-advanced.txt
```

For OCR (also install the Tesseract and Poppler system binaries separately):

```bash
pip install -r requirements-ocr.txt
```

Copy `.env.advanced.example` values into your local `.env`; never commit API keys.

## Integration warning

The current Java contract is `satya-chat-v1`: claims must include `claim_id`, `text`, `supporting_quotes[{evidence_id, quote}]`, and `support_assessment`. The current main workflow intentionally returns **extractive source claims**, not a free-form LLM answer. The new LLM module produces a separate draft object and is not wired into `/internal/chat` automatically. Before wiring it, implement a mapper that:

1. Accepts only evidence IDs from retrieved passages.
2. Resolves every ID to the exact canonical paragraph text.
3. Creates quote strings as exact substrings of that paragraph.
4. Marks a claim supported only after deterministic checks pass.
5. Returns refusal/partial when evidence is absent, conflicting, stale, or insufficient.
6. Leaves final canonical validation to the Java backend.

Do not let an LLM invent quotes or paragraph IDs. A valid JSON response is not proof of legal correctness. Conflict detection here is heuristic and must never decide legal conflicts automatically. Check currentness, amendments, jurisdiction, commencement dates and source authority using official sources and human review.

## Suggested Antigravity integration order

1. Review the current base service and this overlay together.
2. Add optional settings and tests.
3. Integrate hybrid retrieval behind a feature flag; retain BM25 fallback.
4. Add LLM drafting as a separate internal stage; keep existing response contract stable.
5. Build canonical quote validation and tests before enabling generated claims.
6. Add OCR only for scanned PDFs and manually verify OCR output.
7. Run the full test suite and test against a reviewed sample corpus.

## Environment variables

- `SATYA_LLM_BASE_URL`
- `SATYA_LLM_API_KEY`
- `SATYA_LLM_MODEL`
- `SATYA_LLM_TIMEOUT_SECONDS`
- `SATYA_EMBEDDING_MODEL`

No real Indian legal corpus or API credentials are included in this package.
