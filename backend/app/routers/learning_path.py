"""Learning path endpoints — ZPD-based topic recommendations."""

from fastapi import APIRouter, Depends

from app.auth import get_current_user_from_request
from app.validation import validate_course_code
from app.learning_path import TopicPrerequisiteGraph

router = APIRouter()


@router.get("/learning-paths/{course_code}/next")
async def get_next_topics(
    course_code: str,
    user: dict = Depends(get_current_user_from_request),
):
    course_code = validate_course_code(course_code)
    user_email = user.get("email", "")

    graph = TopicPrerequisiteGraph()
    candidates = await graph.get_zpd_candidates(user_email, course_code)
    return {"course_code": course_code, "student_id": user_email, "recommended": candidates}
