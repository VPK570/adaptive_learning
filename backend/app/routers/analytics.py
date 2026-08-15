from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.analytics import (
    get_all_questions,
    get_analytics,
    get_coverage,
    get_my_analytics,
    get_student_stats,
    get_unanswered_questions,
)
from app.auth import get_current_user_from_request, require_role
from app.gap_detection import detect_gaps
from app.topics import get_topic_coverage
from app.validation import validate_course_code

router = APIRouter()


@router.get("/students/me/stats")
async def my_stats(current_user: dict = Depends(get_current_user_from_request)):
    return await get_student_stats(current_user["email"])


@router.get("/analytics/me")
async def my_analytics(course_code: str = "BAECE102", current_user: dict = Depends(get_current_user_from_request)):
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


@router.get("/analytics/report/{course_code}")
async def analytics_report(course_code: str, _=Depends(require_role("faculty", "admin"))):
    course_code = validate_course_code(course_code)
    from datetime import datetime
    analytics_data = await get_analytics(course_code)
    coverage_data = await get_coverage(course_code)
    topic_coverage = await get_topic_coverage(course_code)
    unanswered = await get_unanswered_questions(course_code)
    return JSONResponse(
        content={
            "generated_at": datetime.now().isoformat(),
            "course_code": course_code,
            "analytics": analytics_data,
            "document_coverage": coverage_data,
            "topic_coverage": topic_coverage,
            "unanswered_questions": unanswered,
        },
        headers={"Content-Disposition": f'attachment; filename="analytics_{course_code}_{datetime.now().strftime("%Y%m%d")}.json"'},
    )


@router.get("/analytics/gaps")
async def gaps(
    course_code: str = "BAECE102",
    topic_id: str | None = None,
    current_user: dict = Depends(get_current_user_from_request),
):
    course_code = validate_course_code(course_code)
    result = await detect_gaps(current_user["email"], course_code, topic_id)
    return {"gaps": result}
