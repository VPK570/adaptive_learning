"""Learning path endpoints — ZPD-based topic recommendations."""

from fastapi import APIRouter, Request

from app.validation import validate_course_code
from app.learning_path import TopicPrerequisiteGraph

router = APIRouter()


@router.get("/learning-paths/{course_code}/next")
async def get_next_topics(
    course_code: str,
    request: Request,
):
    course_code = validate_course_code(course_code)
    user_email = request.state.user.get("email", "") if hasattr(request.state, "user") else ""

    graph = TopicPrerequisiteGraph()
    candidates = await graph.get_zpd_candidates(user_email, course_code)
    return {"course_code": course_code, "student_id": user_email, "recommended": candidates}
