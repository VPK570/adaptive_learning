from fastapi import APIRouter, Depends

from app.auth import get_current_user_from_request
from app.chat_history import add_message, clear_course_history, get_course_history
from app.validation import MAX_QUESTION_LENGTH, sanitize_id, sanitize_text, validate_course_code

router = APIRouter()


@router.get("/chat-history")
async def get_history(
    course_code: str,
    session_id: str,
    user: dict = Depends(get_current_user_from_request),
):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    user_email = user.get("email", "")
    return await get_course_history(course_code, session_id, user_id=user_email or None)


@router.post("/chat-history")
async def save_chat_message(
    course_code: str,
    session_id: str,
    role: str,
    content: str,
    user: dict = Depends(get_current_user_from_request),
):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    role = sanitize_text(role, 20)
    content = sanitize_text(content, MAX_QUESTION_LENGTH * 2)
    user_email = user.get("email", "")
    await add_message(course_code, session_id, role, content, user_id=user_email)
    return {"status": "success"}


@router.delete("/chat-history")
async def clear_history(
    course_code: str,
    session_id: str,
    user: dict = Depends(get_current_user_from_request),
):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    user_email = user.get("email", "")
    await clear_course_history(course_code, session_id, user_id=user_email or None)
    return {"status": "success"}
