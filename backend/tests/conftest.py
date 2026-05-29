"""Pytest configuration — ChromaDB and SurrealDB."""

import os
import asyncio
import pytest
import pytest_asyncio
from pathlib import Path
from app.db import SurrealDBManager

os.environ.setdefault("CHROMA_PATH", "/tmp/test_chroma_db")
# Ensure we point to a test namespace/db if available, or just default
os.environ.setdefault("SURREAL_NS", "test_ns")
os.environ.setdefault("SURREAL_DB", "test_db")

dotenv_path = Path(__file__).parent.parent / ".env"
if dotenv_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path)


@pytest.fixture(autouse=True)
def reset_chroma():
    from app import db
    # db.reset() # This function might not exist in db.py? need to verify later
    yield


@pytest_asyncio.fixture(scope="function")
async def surreal_db():
    # Force a fresh connection each time
    from app.db import SurrealDBManager
    SurrealDBManager._instance = None
    db = await SurrealDBManager.get_db()
    yield db
    # Close it properly
    await db.close()

@pytest_asyncio.fixture(autouse=True)
async def cleanup_surreal(surreal_db):
    """Wipe test database after each test."""
    yield
    # Wipe tables
    await surreal_db.query("REMOVE TABLE course; REMOVE TABLE text_chunk; REMOVE TABLE chat_history; REMOVE TABLE flashcard_set; REMOVE TABLE quiz; REMOVE TABLE query_log;")
