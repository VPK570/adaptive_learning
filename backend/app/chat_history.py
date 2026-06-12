from datetime import datetime
from app.validation import validate_course_code, sanitize_id
from app.db import get_db

async def get_course_history(course_code, session_id):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    
    db = await get_db()
    res = await db.query(
        "SELECT * FROM chat_history WHERE course_code = $course AND session_id = $session_id ORDER BY timestamp ASC",
        {"course": course_code, "session_id": session_id}
    )
    
    return res if res else []

async def add_message(course_code, session_id, role, content):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    
    db = await get_db()
    message = {
        "course_code": course_code,
        "session_id": session_id,
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    await db.query("CREATE chat_history CONTENT $msg", {"msg": message})

async def clear_course_history(course_code, session_id):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    
    db = await get_db()
    await db.query(
        "DELETE chat_history WHERE course_code = $course AND session_id = $session_id",
        {"course": course_code, "session_id": session_id}
    )
