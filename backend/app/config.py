import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache
def get_settings() -> "Settings":
    return Settings()


class Settings:
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    SURREAL_URL: str = os.getenv("SURREAL_URL", "ws://localhost:8000/rpc")
    SURREAL_NS: str = os.getenv("SURREAL_NS", "adaptive_learning")
    SURREAL_DB: str = os.getenv("SURREAL_DB", "learning_platform")
    SURREAL_USER: str = os.getenv("SURREAL_USER", "root")
    SURREAL_PASS: str = os.getenv("SURREAL_PASS", "root")

    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nvidia/llama-nemotron-embed-vl-1b-v2:free")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free")

    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP_TOKENS: int = int(os.getenv("CHUNK_OVERLAP_TOKENS", "64"))
    IMAGE_MAX_BATCH_SIZE: int = int(os.getenv("IMAGE_MAX_BATCH_SIZE", "5"))
    IMAGE_MAX_PER_PDF: int = int(os.getenv("IMAGE_MAX_PER_PDF", "50"))
    RRF_K: int = int(os.getenv("RRF_K", "60"))
    HNSW_EF_SEARCH: int = int(os.getenv("HNSW_EF_SEARCH", "40"))
    MAX_HISTORY_TURNS: int = int(os.getenv("MAX_HISTORY_TURNS", "8"))
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    CURRICULUM_K: int = int(os.getenv("CURRICULUM_K", "3"))
    CURRICULUM_EF: int = int(os.getenv("CURRICULUM_EF", "40"))
    CURRICULUM_THRESHOLD: float = float(os.getenv("CURRICULUM_THRESHOLD", "0.6"))
    RAG_MIN_SIMILARITY: float = float(os.getenv("RAG_MIN_SIMILARITY", "0.4"))

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/adaptive_learning")
    DB_ECHO_SQL: bool = os.getenv("DB_ECHO_SQL", "false").lower() == "true"
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))

    def __init__(self):
        if not self.JWT_SECRET or self.JWT_SECRET == "":
            logger.warning("JWT_SECRET is not set — auth tokens cannot be verified. Set it in .env")
        if not self.OPENROUTER_API_KEY or "your_" in self.OPENROUTER_API_KEY:
            logger.warning("OPENROUTER_API_KEY is not set — LLM calls will fail. Set it in .env")


settings = get_settings()
