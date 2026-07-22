from fastapi import APIRouter, Depends

from app.analytics import (
    get_all_questions,
    get_analytics,
    get_coverage,
    get_my_analytics,
    get_unanswered_questions,
)
from app.auth import get_current_user, require_role
from app.gap_detection import detect_gaps
from app.validation import validate_course_code

router = APIRouter()


@router.get("/analytics/me")
async def my_analytics(course_code: str = "BAECE102", current_user: dict = Depends(get_current_user)):
    course_code = validate_course_code(course_code)
    return await get_my_analytics(current_user["email"], course_code)


@router.get("/analytics")
async def analytics(course_code: str = "BAECE102", _=Depends(require_role("faculty", "admin"))):
    course_code = validate_course_code(course_code)
    return await get_analytics(course_code)


@router.get("/analytics/unanswered")
async def unanswered(course_code: str = "BAECE102", _=Depends(require_role("faculty", "admin"))):
    course_code = validate_course_code(course_code)
    return await get_unanswered_questions(course_code)


@router.get("/analytics/coverage")
async def coverage(course_code: str = "BAECE102", _=Depends(require_role("faculty", "admin"))):
    course_code = validate_course_code(course_code)
    return await get_coverage(course_code)


@router.get("/questions")
async def questions(course_code: str = "BAECE102", _=Depends(require_role("faculty", "admin"))):
    course_code = validate_course_code(course_code)
    return await get_all_questions(course_code)


@router.get("/analytics/gaps")
async def gaps(
    course_code: str = "BAECE102",
    topic_id: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    course_code = validate_course_code(course_code)
    result = await detect_gaps(current_user["email"], course_code, topic_id)
    return {"gaps": result}
