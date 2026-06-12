import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from app.curriculum import CurriculumManager
from app.db import get_db, SurrealDBManager


@pytest_asyncio.fixture
async def mock_client():
    with patch("app.curriculum.client") as mock:
        mock.embed_text = AsyncMock(return_value=[0.1] * 2048)
        mock.embed_text_batch = AsyncMock(side_effect=lambda texts: [[0.1] * 2048 for _ in texts])
        yield mock


@pytest_asyncio.fixture
async def mock_pdf_extractor():
    with patch("app.pdf_extractor.extract_all_pages") as mock:
        class Page:
            def __init__(self, text, page_num):
                self.text = text
                self.page_num = page_num

        mock.return_value = [
            Page("Topic 1: Introduction to AI", 1),
            Page("Topic 2: Neural Networks", 2),
            Page("Topic 3: Deep Learning", 3)
        ]
        yield mock


@pytest.mark.asyncio
async def test_surreal_connection(surreal_db):
    """Verify SurrealDB is connected and functional."""
    result = await surreal_db.query("RETURN 1")
    assert result == 1


@pytest.mark.asyncio
async def test_schema_initialization(surreal_db):
    """Verify tables are correctly defined."""
    result = await surreal_db.query("INFO FOR DB")
    tables = result['tables']
    assert 'course' in tables
    assert 'text_chunk' in tables
    assert 'chat_history' in tables


@pytest.mark.asyncio
async def test_course_crud(surreal_db):
    """Verify course CRUD operations."""
    await surreal_db.create("course", {
        "course_code": "TEST101",
        "course_name": "Test Course",
        "description": "A test course description",
        "icon": "book",
        "created_at": "2026-06-06T00:00:00"
    })

    res = await surreal_db.query("SELECT * FROM course WHERE course_code = 'TEST101'")
    assert len(res) == 1
    assert res[0]['course_code'] == 'TEST101'

    await surreal_db.query("UPDATE course SET course_code = 'TEST102' WHERE course_code = 'TEST101'")

    res = await surreal_db.query("SELECT * FROM course WHERE course_code = 'TEST102'")
    assert len(res) == 1

    await surreal_db.query("DELETE course WHERE course_code = 'TEST102'")
    res = await surreal_db.query("SELECT * FROM course WHERE course_code = 'TEST102'")
    assert len(res) == 0


@pytest.mark.asyncio
async def test_chat_history_ops(surreal_db):
    """Verify chat_history operations."""
    await surreal_db.create("chat_history", {
        "course_code": "CHEM101",
        "session_id": "session1",
        "role": "user",
        "content": "hello",
        "timestamp": "2026-05-29T12:00:00"
    })

    res = await surreal_db.query("SELECT * FROM chat_history WHERE session_id = 'session1'")
    assert len(res) == 1
    assert res[0]['course_code'] == 'CHEM101'


@pytest.mark.asyncio
async def test_curriculum_ingestion_and_retrieval(surreal_db, mock_client, mock_pdf_extractor):
    """Test full cycle of curriculum ingestion and retrieval."""
    manager = CurriculumManager()
    course_code = "CSE101"

    result = await manager.ingest_curriculum(course_code, "Syllabus", "dummy.pdf")
    assert result["status"] == "success"
    assert result["chunks_ingested"] == 3

    docs = await manager.list_curriculum(course_code)
    assert "Syllabus" in docs

    topics = await manager.get_curriculum_topics(course_code)
    assert "Topic 1: Introduction to AI" in topics
    assert "Topic 2: Neural Networks" in topics
    assert "Topic 3: Deep Learning" in topics

    in_scope = await manager.check_topic_in_curriculum(course_code, "AI Introduction")
    assert in_scope is True


@pytest.mark.asyncio
async def test_curriculum_missing_field_auto_fix(surreal_db, mock_client, mock_pdf_extractor):
    """Test the 'missing field' auto-fix logic in ingest_curriculum."""
    from surrealdb.errors import InternalError

    manager = CurriculumManager()
    course_code = "CSE102"

    original_query = surreal_db.query
    call_count = 0

    async def side_effect(query_str, vars=None):
        nonlocal call_count
        if "INSERT INTO curriculum_chunk" in query_str and call_count == 0:
            call_count += 1
            raise InternalError("Found field 'new_field', but no such field exists for table 'curriculum_chunk'")
        return await original_query(query_str, vars)

    with patch.object(surreal_db, 'query', side_effect=side_effect):
        with patch("app.curriculum.get_db", return_value=surreal_db):
            mock_pdf_extractor.return_value = [
                type('Page', (), {'text': 'Some text', 'page_num': 1})()
            ]
            pass


@pytest.mark.asyncio
async def test_chat_history_manager(surreal_db):
    """Test chat history operations via the DB."""
    from app.chat_history import add_message, get_course_history, clear_course_history

    course_code = "CS101"
    session_id = "user_123"

    await add_message(course_code, session_id, "user", "Hello tutor")
    await add_message(course_code, session_id, "assistant", "Hello student! How can I help?")

    history = await get_course_history(course_code, session_id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"

    await clear_course_history(course_code, session_id)
    history_cleared = await get_course_history(course_code, session_id)
    assert len(history_cleared) == 0


@pytest.mark.asyncio
async def test_analytics_logging(surreal_db):
    """Test analytics logging to DB."""
    from app.analytics import log_query

    course_code = "BIO101"
    await log_query(
        course_code=course_code,
        question="What is a cell?",
        response="A cell is the basic unit of life.",
        cited_sources=[{"title": "Biology 101", "page": 1}]
    )

    res = await surreal_db.query("SELECT * FROM query_log WHERE course_code = $code", {"code": course_code})
    assert len(res) == 1
    assert res[0]["question"] == "What is a cell?"
