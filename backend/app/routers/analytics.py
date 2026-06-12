from fastapi import APIRouter

from app.validation import validate_course_code
from app.analytics import (
    get_analytics,
    get_all_questions,
    get_unanswered_questions,
    get_coverage,
)

router = APIRouter()


@router.get("/analytics")
async def analytics(course_code: str = "BAECE102"):
    course_code = validate_course_code(course_code)
    return await get_analytics(course_code)


@router.get("/analytics/unanswered")
async def unanswered(course_code: str = "BAECE102"):
    course_code = validate_course_code(course_code)
    return await get_unanswered_questions(course_code)


@router.get("/analytics/coverage")
async def coverage(course_code: str = "BAECE102"):
    course_code = validate_course_code(course_code)
    return await get_coverage(course_code)


@router.get("/questions")
async def questions(course_code: str = "BAECE102"):
    course_code = validate_course_code(course_code)
    return await get_all_questions(course_code)
