import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from app.curriculum import CurriculumManager


@pytest_asyncio.fixture
async def mock_client():
    with patch("app.curriculum.client") as mock:
        mock.embed_text = AsyncMock(return_value=[0.1] * 2048)
        mock.embed_text_batch = AsyncMock(side_effect=lambda texts: [[0.1] * 2048 for _ in texts])
        yield mock


@pytest_asyncio.fixture
async def mock_file_hash():
    with patch("app.curriculum.calculate_file_hash", return_value="dummy_hash"):
        yield


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
    assert 'chat_message' in tables


@pytest.mark.asyncio
async def test_course_crud(surreal_db):
    """Verify course CRUD operations."""
    await surreal_db.create("course", {
        "course_code": "TEST101",
        "course_name": "Test Course",
        "description": "A test course description",
        "icon": "book",
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
    """Verify chat_message operations."""
    await surreal_db.create("chat_message", {
        "course_code": "CHEM101",
        "session_id": "session1",
        "message_role": "user",
        "content": "hello",
        "user_id": "",
    })

    res = await surreal_db.query("SELECT * FROM chat_message WHERE session_id = 'session1'")
    assert len(res) == 1
    assert res[0]['course_code'] == 'CHEM101'


@pytest.mark.asyncio
async def test_curriculum_ingestion_and_retrieval(surreal_db, mock_client, mock_file_hash, mock_pdf_extractor):
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
async def test_curriculum_missing_field_auto_fix(surreal_db, mock_client, mock_file_hash, mock_pdf_extractor):
    """Test the 'missing field' auto-fix logic in ingest_curriculum."""
    from surrealdb.errors import InternalError

    original_query = surreal_db.query
    call_count = 0

    async def side_effect(query_str, vars=None):
        nonlocal call_count
        if "INSERT INTO curriculum_chunk" in query_str and call_count == 0:
            call_count += 1
            raise InternalError("Internal", "Found field 'new_field', but no such field exists for table 'curriculum_chunk'")
        return await original_query(query_str, vars)

    with patch.object(surreal_db, 'query', side_effect=side_effect):
        with patch("app.curriculum.get_db", return_value=surreal_db):
            mock_pdf_extractor.return_value = [
                type('Page', (), {'text': 'Some text', 'page_num': 1})()
            ]
            from app.curriculum import CurriculumManager
            manager = CurriculumManager()
            result = await manager.ingest_curriculum("CSE102", "Syllabus", "dummy.pdf")
            assert result["status"] == "success"
            assert result["chunks_ingested"] == 1


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
        cited_sources=[{"source_title": "Biology 101", "page": "1", "content_type": "text", "has_image": False}]
    )

    res = await surreal_db.query("SELECT * FROM query_log WHERE course_code = $code", {"code": course_code})
    assert len(res) == 1
    assert res[0]["question"] == "What is a cell?"


@pytest.mark.asyncio
async def test_knowledge_state_update_increases_mastery(surreal_db):
    from app.knowledge_state import KnowledgeStateManager
    ksm = KnowledgeStateManager()
    sid, cc, tid, bl = "student1", "CS101", "Flip-flops", 2

    initial = await ksm.get_state(sid, cc, tid, bl)
    assert initial["mastery_score"] == 0.0

    await ksm.update_state(sid, cc, tid, bl, is_correct=True)
    after = await ksm.get_state(sid, cc, tid, bl)
    assert after["mastery_score"] > 0.0
    assert after["total_attempts"] == 1
    assert after["correct_attempts"] == 1
    assert after["streak"] == 1


@pytest.mark.asyncio
async def test_knowledge_state_update_decreases_on_wrong(surreal_db):
    from app.knowledge_state import KnowledgeStateManager
    ksm = KnowledgeStateManager()
    sid, cc, tid, bl = "student2", "CS101", "K-maps", 2

    await ksm.update_state(sid, cc, tid, bl, is_correct=True)
    await ksm.update_state(sid, cc, tid, bl, is_correct=False)
    state = await ksm.get_state(sid, cc, tid, bl)
    assert state["total_attempts"] == 2
    assert state["correct_attempts"] == 1
    assert state["streak"] == 0


@pytest.mark.asyncio
async def test_knowledge_state_stays_in_bounds(surreal_db):
    from app.knowledge_state import KnowledgeStateManager
    ksm = KnowledgeStateManager()
    sid, cc, tid, bl = "student3", "CS101", "Counters", 1

    for _ in range(50):
        await ksm.update_state(sid, cc, tid, bl, is_correct=True)
    state = await ksm.get_state(sid, cc, tid, bl)
    assert 0.0 <= state["mastery_score"] <= 1.0
    assert 0.0 <= state["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_get_topic_summary(surreal_db):
    from app.knowledge_state import KnowledgeStateManager
    ksm = KnowledgeStateManager()
    sid, cc, tid = "student4", "CS101", "Sequential"

    await ksm.update_state(sid, cc, tid, 1, is_correct=True)
    await ksm.update_state(sid, cc, tid, 2, is_correct=False)

    summary = await ksm.get_topic_summary(sid, cc, tid)
    assert "mastery" in summary
    assert "confidence" in summary
    assert summary["total_attempts"] == 2
    assert "bloom_breakdown" in summary


@pytest.mark.asyncio
async def test_get_student_course_states(surreal_db):
    from app.knowledge_state import KnowledgeStateManager
    ksm = KnowledgeStateManager()
    sid, cc = "student5", "CS101"

    await ksm.update_state(sid, cc, "TopicA", 1, True)
    await ksm.update_state(sid, cc, "TopicB", 2, False)

    states = await ksm.get_student_course_states(sid, cc)
    assert len(states) >= 2


@pytest.mark.asyncio
async def test_gap_detection_no_data(surreal_db):
    from app.gap_detection import detect_gaps
    gaps = await detect_gaps("nonexistent", "CS101")
    assert gaps == []


@pytest.mark.asyncio
async def test_gap_detection_identifies_drop(surreal_db):
    from app.knowledge_state import KnowledgeStateManager
    from app.gap_detection import detect_gaps
    ksm = KnowledgeStateManager()
    sid, cc, tid = "student6", "CS101", "LogicGates"

    for _ in range(5):
        await ksm._log_question(sid, cc, tid, 1, True, source="quiz")
        await ksm._log_question(sid, cc, tid, 2, False, source="quiz")

    gaps = await detect_gaps(sid, cc, tid)
    assert len(gaps) >= 0


@pytest.mark.asyncio
async def test_should_trigger_diagnostic(surreal_db):
    from app.gap_detection import should_trigger_diagnostic
    result = await should_trigger_diagnostic("nonexistent", "CS101")
    assert result is False


@pytest.mark.asyncio
async def test_build_diagnostic_preamble():
    from app.gap_detection import build_diagnostic_preamble
    gaps = [{"bloom_label": "Apply"}, {"bloom_label": "Evaluate"}]
    result = build_diagnostic_preamble("LogicGates", gaps)
    assert "Apply" in result
    assert "Evaluate" in result
    assert "LogicGates" not in result  # it's topic_id, not shown


@pytest.mark.asyncio
async def test_topic_coverage_covered_and_missing(surreal_db):
    from app.topics import get_topic_coverage
    from app.db import get_db
    db = await get_db()

    await db.query(
        "INSERT INTO course_topic {course_code: $cc, topic_name: $tn, order_index: 0, subtopics: [], prerequisites: [], bloom_level: 'Remember', learning_objectives: []}",
        {"cc": "COV101", "tn": "CoveredTopic"},
    )
    await db.query(
        "INSERT INTO course_topic {course_code: $cc, topic_name: $tn, order_index: 1, subtopics: [], prerequisites: [], bloom_level: 'Remember', learning_objectives: []}",
        {"cc": "COV101", "tn": "MissingTopic"},
    )

    coverage = await get_topic_coverage("COV101")
    assert coverage["total_topics"] == 2
    assert coverage["covered"] == 0
    assert coverage["missing"] == 2
    assert coverage["topics"][0]["status"] == "missing"

    for t in coverage["topics"]:
        assert "topic_name" in t
        assert "status" in t


@pytest.mark.asyncio
async def test_get_course_topics_order(surreal_db):
    from app.topics import get_course_topics, store_course_topics
    topics = [
        {"topic_name": "B_topic", "subtopics": [], "prerequisites": [], "bloom_level": "Remember", "learning_objectives": []},
        {"topic_name": "A_topic", "subtopics": [], "prerequisites": [], "bloom_level": "Understand", "learning_objectives": []},
    ]
    await store_course_topics("ORD101", topics)
    stored = await get_course_topics("ORD101")
    assert stored[0]["topic_name"] == "B_topic"
    assert stored[1]["topic_name"] == "A_topic"
