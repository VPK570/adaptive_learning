"""Pytest configuration — ChromaDB and SurrealDB."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env first (may set production values), then override to test namespace
# Must happen BEFORE any app. imports since Settings class reads os.getenv() at class body level
dotenv_path = Path(__file__).parent.parent / ".env"
if dotenv_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path)

os.environ["SURREAL_NS"] = "test_ns"
os.environ["SURREAL_DB"] = "test_db"

import pytest_asyncio
from app.db import SurrealDBManager


_CLEANUP_TABLES = ("course", "text_chunk", "image_chunk", "chat_message", "flashcard_set",
                   "quiz", "query_log", "knowledge_state", "topic_prerequisite",
                   "question_log", "document", "curriculum_chunk", "course_topic", "user")


@pytest_asyncio.fixture(scope="function")
async def surreal_db():
    SurrealDBManager._instance = None
    db = await SurrealDBManager.get_db()
    for tbl in _CLEANUP_TABLES:
        try:
            await db.query(f"DELETE {tbl}")
        except Exception:
            pass
    for tbl in ("knowledge_state", "course_topic", "question_log", "curriculum_chunk"):
        try:
            await db.query(f"REMOVE TABLE {tbl}")
        except Exception:
            pass
    from app.db import SurrealDBManager as dbm
    await dbm._init_schema(db)
    yield db
    await db.close()
