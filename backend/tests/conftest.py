"""Pytest configuration — ChromaDB and SurrealDB."""

import os
import pytest
import pytest_asyncio
from pathlib import Path
from app.db import SurrealDBManager

os.environ.setdefault("CHROMA_PATH", "/tmp/test_chroma_db")
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
    await surreal_db.query(
        "REMOVE TABLE course; REMOVE TABLE text_chunk; "
        "REMOVE TABLE chat_history; REMOVE TABLE flashcard_set; "
        "REMOVE TABLE quiz; REMOVE TABLE query_log;"
    )
