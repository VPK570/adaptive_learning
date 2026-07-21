"""Pytest configuration — ChromaDB and SurrealDB."""

import os
import pytest_asyncio
from pathlib import Path
from app.db import SurrealDBManager

os.environ.setdefault("SURREAL_NS", "test_ns")
os.environ.setdefault("SURREAL_DB", "test_db")

dotenv_path = Path(__file__).parent.parent / ".env"
if dotenv_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path)


@pytest_asyncio.fixture(scope="function")
async def surreal_db():
    SurrealDBManager._instance = None
    db = await SurrealDBManager.get_db()
    yield db
    await db.close()


@pytest_asyncio.fixture(autouse=True)
async def cleanup_surreal(surreal_db):
    yield
    for tbl in ("course", "text_chunk", "chat_message", "flashcard_set",
                "quiz", "query_log", "knowledge_state", "topic_prerequisite", "question_log",
                "document", "curriculum_chunk"):
        try:
            await surreal_db.query(f"REMOVE TABLE {tbl}")
        except Exception:
            pass
