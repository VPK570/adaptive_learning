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
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-3.6-flash")
    TOPIC_EXTRACTION_MODEL: str = os.getenv("TOPIC_EXTRACTION_MODEL", "google/gemma-4-26b-a4b-it:free")
    QUIZ_MODEL: str = os.getenv("QUIZ_MODEL", "google/gemma-4-26b-a4b-it:free")

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemma-4-31b-it")
    GEMINI_VISION_MODEL: str = os.getenv("GEMINI_VISION_MODEL", "gemma-4-31b-it")
    GEMINI_BASE_URL: str = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")

    @property
    def GEMINI_API_KEYS(self) -> list[str]:
        return self._parse_csv("GEMINI_API_KEYS", self.GEMINI_API_KEY)

    @property
    def OPENROUTER_API_KEYS(self) -> list[str]:
        return self._parse_csv("OPENROUTER_API_KEYS", self.OPENROUTER_API_KEY)

    @staticmethod
    def _parse_csv(env_name: str, fallback: str) -> list[str]:
        val = os.getenv(env_name, "")
        if val:
            return [k.strip() for k in val.split(",") if k.strip()]
        if fallback:
            return [fallback]
        return []

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
    GATEKEEPER_ENABLED: bool = os.getenv("GATEKEEPER_ENABLED", "false").lower() == "true"
    BLOOM_VALIDATION_ENABLED: bool = os.getenv("BLOOM_VALIDATION_ENABLED", "false").lower() == "true"
    QUERY_ENHANCER_ENABLED: bool = os.getenv("QUERY_ENHANCER_ENABLED", "true").lower() == "true"
    QUERY_ENHANCER_NUM_QUERIES: int = int(os.getenv("QUERY_ENHANCER_NUM_QUERIES", "3"))

    DKT_ACTIVE: bool = os.getenv("DKT_ACTIVE", "false").lower() == "true"
    MASTERY_THRESHOLD: float = float(os.getenv("MASTERY_THRESHOLD", "0.7"))
    BKT_LEARNING_RATE: float = float(os.getenv("BKT_LEARNING_RATE", "0.15"))
    BKT_P_INIT: float = float(os.getenv("BKT_P_INIT", "0.15"))
    BKT_P_LEARN: float = float(os.getenv("BKT_P_LEARN", "0.15"))
    BKT_P_GUESS: float = float(os.getenv("BKT_P_GUESS", "0.15"))
    BKT_P_SLIP: float = float(os.getenv("BKT_P_SLIP", "0.10"))

    def __init__(self):
        if not self.JWT_SECRET or self.JWT_SECRET == "":
            logger.warning("JWT_SECRET is not set — auth tokens cannot be verified. Set it in .env")
        if not self.OPENROUTER_API_KEY and not self.OPENROUTER_API_KEYS:
            logger.warning("No OpenRouter API key set — embeddings will fail. Set OPENROUTER_API_KEY or OPENROUTER_API_KEYS in .env")
        if not self.GEMINI_API_KEY and not self.GEMINI_API_KEYS:
            logger.warning("No Gemini API key set — LLM calls will fail. Set GEMINI_API_KEY or GEMINI_API_KEYS in .env")


settings = get_settings()
