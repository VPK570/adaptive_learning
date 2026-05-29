import pytest
import pytest_asyncio
from app.db import SurrealDBManager

@pytest.mark.asyncio
async def test_surreal_connection(surreal_db):
    """Verify SurrealDB is connected and functional."""
    # Run a simple query - no semicolon
    result = await surreal_db.query("RETURN 1")
    # Result structure is usually a list of dicts, check the actual structure
    assert result == 1

@pytest.mark.asyncio
async def test_schema_initialization(surreal_db):
    """Verify tables are correctly defined."""
    result = await surreal_db.query("INFO FOR DB")
    # It seems in this version it returns dict directly or differently
    tables = result['tables']
    assert 'course' in tables
    assert 'text_chunk' in tables
    assert 'chat_history' in tables

@pytest.mark.asyncio
async def test_course_crud(surreal_db):
    """Verify course CRUD operations."""
    # Create
    await surreal_db.create("course", {"course_code": "TEST101"})
    
    # Read
    res = await surreal_db.query("SELECT * FROM course WHERE course_code = 'TEST101'")
    assert len(res) == 1
    assert res[0]['course_code'] == 'TEST101'
    
    # Update
    await surreal_db.query("UPDATE course SET course_code = 'TEST102' WHERE course_code = 'TEST101'")
    
    # Read updated
    res = await surreal_db.query("SELECT * FROM course WHERE course_code = 'TEST102'")
    assert len(res) == 1
    
    # Delete
    await surreal_db.query("DELETE course WHERE course_code = 'TEST102'")
    res = await surreal_db.query("SELECT * FROM course WHERE course_code = 'TEST102'")
    assert len(res) == 0

@pytest.mark.asyncio
async def test_chat_history_ops(surreal_db):
    """Verify chat_history operations."""
    # Defined fields: course_code, session_id, role, content, timestamp
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
