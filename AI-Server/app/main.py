import logging
from fastapi import FastAPI
from app.api.routes import router
from app.core.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level.upper(), format="%(asctime)s %(levelname)s %(name)s %(message)s")
app = FastAPI(
    title="SATYA Internal AI Service",
    description="Evidence retrieval for Indian law and policy. Responses are extractive and must be checked against canonical evidence by the Java backend.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)
app.include_router(router)
