from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AiRequest(StrictModel):
    schema_version: Literal["satya-chat-v1"]
    question: str = Field(min_length=1, max_length=2000)
    corpus_revision: str = Field(min_length=1, max_length=100)


class SupportingQuote(StrictModel):
    evidence_id: str
    quote: str


class AiClaim(StrictModel):
    claim_id: str
    text: str
    supporting_quotes: list[SupportingQuote]
    support_assessment: Literal["supported", "unsupported", "uncertain"]


class AiResponse(StrictModel):
    schema_version: Literal["satya-chat-v1"] = "satya-chat-v1"
    corpus_revision: str
    status: Literal["answered", "partial", "clarification", "refusal", "conflict"]
    claims: list[AiClaim]
    unanswered_count: int = 0


class HealthResponse(StrictModel):
    status: Literal["ok"] = "ok"
    service: Literal["satya-ai"] = "satya-ai"
    mode: Literal["retrieval"] = "retrieval"
