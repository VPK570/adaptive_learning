"""ChromaDB client — no Docker needed, persistent file-based storage."""

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings


def get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(
        path=settings.CHROMA_PATH,
        settings=ChromaSettings(
            anonymized_telemetry=False,
            allow_reset=True,
        ),
    )


def get_collection(name: str = "chunks"):
    client = get_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
        embedding_function=None,
    )


def reset():
    client = get_client()
    for name in ("text_chunks", "image_chunks"):
        try:
            client.delete_collection(name)
        except Exception:
            pass


def init_collection():
    """Ensure the chunks collection exists with the right config."""
    return get_collection("chunks")