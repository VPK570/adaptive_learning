"""Pytest configuration — ChromaDB (no Docker needed)."""

import os
from pathlib import Path

import pytest

os.environ.setdefault("CHROMA_PATH", "/tmp/test_chroma_db")

dotenv_path = Path(__file__).parent.parent / ".env"
if dotenv_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path)


@pytest.fixture(autouse=True)
def reset_chroma():
    from app import db
    db.reset()
    yield
    db.reset()


@pytest.fixture
def text_collection():
    from app.db import get_collection
    col = get_collection("text_chunks")
    col.delete(where={})
    return col


@pytest.fixture
def image_collection():
    from app.db import get_collection
    col = get_collection("image_chunks")
    col.delete(where={})
    return col
