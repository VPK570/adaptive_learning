"""Config — all settings from environment variables."""

import os
from functools import lru_cache


@lru_cache
def get_settings() -> "Settings":
    return Settings()


class Settings:
    SURREAL_URL: str = os.getenv("SURREAL_URL", "ws://localhost:8000/rpc")
    SURREAL_NS: str = os.getenv("SURREAL_NS", "adaptive_learning")
    SURREAL_DB: str = os.getenv("SURREAL_DB", "learning_platform")
    SURREAL_USER: str = os.getenv("SURREAL_USER", "root")
    SURREAL_PASS: str = os.getenv("SURREAL_PASS", "root")

    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nvidia/llama-nemotron-embed-vl-1b-v2:free")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free")

    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP_TOKENS: int = int(os.getenv("CHUNK_OVERLAP_TOKENS", "64"))
    IMAGE_MAX_BATCH_SIZE: int = int(os.getenv("IMAGE_MAX_BATCH_SIZE", "5"))
    IMAGE_MAX_PER_PDF: int = int(os.getenv("IMAGE_MAX_PER_PDF", "50"))


settings = get_settings()
