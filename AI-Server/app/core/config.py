from functools import lru_cache
from pathlib import Path
import os


class Settings:
    def __init__(self) -> None:
        self.internal_token = os.getenv("SATYA_INTERNAL_TOKEN", "")
        self.data_dir = Path(os.getenv("SATYA_AI_DATA_DIR", "./data")).resolve()
        self.index_path = self.data_dir / "index.json"
        self.log_level = os.getenv("SATYA_AI_LOG_LEVEL", "INFO")
        self.enable_semantic = os.getenv("SATYA_ENABLE_SEMANTIC", "false").lower() in {"1", "true", "yes"}
        self.semantic_model = os.getenv("SATYA_SEMANTIC_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.enable_llm = os.getenv("SATYA_ENABLE_LLM", "false").lower() in {"1", "true", "yes"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
