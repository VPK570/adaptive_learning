from fastapi import APIRouter

from app.validation import validate_course_code, sanitize_id, sanitize_text, MAX_QUESTION_LENGTH
from app.chat_history import get_course_history, add_message, clear_course_history

router = APIRouter()


@router.get("/chat-history")
async def get_history(course_code: str, session_id: str):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    return await get_course_history(course_code, session_id)


@router.post("/chat-history")
async def save_chat_message(
    course_code: str, session_id: str, role: str, content: str
):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    role = sanitize_text(role, 20)
    content = sanitize_text(content, MAX_QUESTION_LENGTH * 2)
    await add_message(course_code, session_id, role, content)
    return {"status": "success"}


@router.delete("/chat-history")
async def clear_history(course_code: str, session_id: str):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    await clear_course_history(course_code, session_id)
    return {"status": "success"}
