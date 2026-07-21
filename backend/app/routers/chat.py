from fastapi import APIRouter, Request

from app.validation import validate_course_code, sanitize_id, sanitize_text, MAX_QUESTION_LENGTH
from app.chat_history import get_course_history, add_message, clear_course_history

router = APIRouter()


@router.get("/chat-history")
async def get_history(course_code: str, session_id: str, request: Request):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    user_email = request.state.user.get("email", "") if hasattr(request.state, "user") else ""
    return await get_course_history(course_code, session_id, user_id=user_email or None)


@router.post("/chat-history")
async def save_chat_message(
    course_code: str, session_id: str, role: str, content: str, request: Request
):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    role = sanitize_text(role, 20)
    content = sanitize_text(content, MAX_QUESTION_LENGTH * 2)
    user_email = request.state.user.get("email", "") if hasattr(request.state, "user") else ""
    await add_message(course_code, session_id, role, content, user_id=user_email)
    return {"status": "success"}


@router.delete("/chat-history")
async def clear_history(course_code: str, session_id: str, request: Request):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    user_email = request.state.user.get("email", "") if hasattr(request.state, "user") else ""
    await clear_course_history(course_code, session_id, user_id=user_email or None)
    return {"status": "success"}
