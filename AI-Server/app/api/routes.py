import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from app.core.config import get_settings
from app.core.security import require_internal_token
from app.schemas.chat import AiRequest, AiResponse, HealthResponse
from app.graph.workflow import answer_question

router = APIRouter()
logger = logging.getLogger("satya.ai")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.post("/internal/chat", response_model=AiResponse, dependencies=[Depends(require_internal_token)])
async def chat(request: AiRequest) -> AiResponse:
    settings = get_settings()
    index_path = settings.index_path
    if not index_path.is_file():
        raise HTTPException(status_code=503, detail={"code": "CORPUS_NOT_LOADED", "message": "No indexed legal corpus is available. Ingest and review official documents first."})
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        records = payload.get("paragraphs", [])
    except (OSError, json.JSONDecodeError):
        logger.exception("Unable to read AI evidence index")
        raise HTTPException(status_code=503, detail={"code": "CORPUS_INDEX_INVALID", "message": "The evidence index is unavailable or invalid."})
    result = await answer_question(request.question, request.corpus_revision, records)
    return AiResponse.model_validate(result)
