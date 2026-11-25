import secrets
from fastapi import Header, HTTPException
from app.core.config import get_settings


def require_internal_token(supplied_token: str | None = Header(default=None, alias="X-Internal-Token")) -> None:
    expected = get_settings().internal_token
    if len(expected) < 32:
        raise HTTPException(status_code=503, detail={"code": "INTERNAL_AUTH_NOT_CONFIGURED", "message": "Configure SATYA_INTERNAL_TOKEN with at least 32 characters."})
    if supplied_token is None or not secrets.compare_digest(supplied_token, expected):
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "A valid internal service token is required."})
