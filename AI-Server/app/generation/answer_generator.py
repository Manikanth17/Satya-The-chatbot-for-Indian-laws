"""Draft an evidence-constrained answer; Java must still validate IDs/quotes."""
from __future__ import annotations
import json
from typing import Any
from app.generation.llm_client import OpenAICompatibleClient
from app.generation.prompts import SYSTEM_PROMPT, build_user_prompt

async def generate_grounded_draft(question: str, passages: list[dict[str, Any]]) -> dict[str, Any]:
    if not passages:
        return {"answer": "I could not find sufficient supporting material in the loaded corpus.", "claims": [], "insufficient_evidence": True}
    client = OpenAICompatibleClient()
    raw = await client.chat(SYSTEM_PROMPT, build_user_prompt(question, passages))
    # Strict JSON parsing; never try to repair malformed model output silently.
    result = json.loads(raw)
    if not isinstance(result, dict) or not isinstance(result.get("claims"), list):
        raise ValueError("LLM response does not match SATYA draft schema")
    allowed = {str(p.get("paragraph_id")) for p in passages}
    for claim in result["claims"]:
        if not isinstance(claim, dict) or not isinstance(claim.get("evidence_ids"), list):
            raise ValueError("Malformed claim in LLM response")
        if not set(map(str, claim["evidence_ids"])).issubset(allowed):
            raise ValueError("LLM referenced evidence outside supplied context")
    return result
