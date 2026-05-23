"""Config — all settings from environment variables."""

import os
from functools import lru_cache


@lru_cache
def get_settings() -> "Settings":
    return Settings()


class Settings:
    CHROMA_PATH: str = os.getenv("CHROMA_PATH", "./chroma_db")

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

    # Storage paths
    BASE_STORAGE_DIR: str = os.getenv("BASE_STORAGE_DIR", "./backend/storage")
    CHAT_HISTORY_DIR: str = os.path.join(BASE_STORAGE_DIR, "chat_history")
    FLASHCARDS_DIR: str = os.path.join(BASE_STORAGE_DIR, "flashcards")
    QUIZZES_DIR: str = os.path.join(BASE_STORAGE_DIR, "quizzes")
    ANALYTICS_DIR: str = os.path.join(BASE_STORAGE_DIR, "analytics")
    UPLOADS_DIR: str = os.path.join(BASE_STORAGE_DIR, "uploads")


settings = get_settings()