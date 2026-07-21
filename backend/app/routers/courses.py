from fastapi import APIRouter, Depends, Query, HTTPException

from app.auth import require_role
from app.deps import get_rag, get_curriculum
from app.rag import RAGPipeline
from app.curriculum import CurriculumManager
from app.schemas import CourseCreate, CourseUpdate
from app.validation import validate_course_code
from app.courses import get_all_courses_data, create_course, update_course, delete_course

router = APIRouter()


@router.get("/courses/{course_code}")
async def get_course(course_code: str, rag: RAGPipeline = Depends(get_rag)):
    course_code = validate_course_code(course_code)
    courses = await get_all_courses_data()
    course = next((c for c in courses if c["course_code"] == course_code), None)
    if not course:
        raise HTTPException(404, f"Course {course_code} not found")
    stats = await rag.get_course_stats(course_code)
    course["doc_count"] = len(stats.get("documents", []))
    course["chunk_count"] = stats.get("total_chunks", 0)
    return course


@router.get("/courses")
async def list_courses(rag: RAGPipeline = Depends(get_rag)):
    courses = await get_all_courses_data()
    if not courses:
        return courses
    codes = [c["course_code"] for c in courses]
    stats_map = await rag.get_batch_stats(codes)
    for course in courses:
        stats = stats_map.get(course["course_code"], {})
        course["doc_count"] = len(stats.get("documents", []))
        course["chunk_count"] = stats.get("chunk_count", 0)
    return courses


@router.post("/courses")
async def create_new_course(body: CourseCreate, _=Depends(require_role("faculty", "admin"))):
    try:
        course_code = validate_course_code(body.course_code)
        new_course = await create_course(
            course_code, body.course_name, body.description, body.icon
        )
        return new_course
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/courses/{course_code}")
async def edit_course(course_code: str, body: CourseUpdate, _=Depends(require_role("faculty", "admin"))):
    try:
        course_code = validate_course_code(course_code)
        updated = await update_course(
            course_code, body.course_name, body.description, body.icon
        )
        return updated
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/courses/{course_code}")
async def remove_course(course_code: str, _=Depends(require_role("faculty", "admin"))):
    try:
        course_code = validate_course_code(course_code)
        await delete_course(course_code)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/curriculum/topics")
async def get_course_topics(
    course: str = Query(...),
    curriculum: CurriculumManager = Depends(get_curriculum),
):
    course = validate_course_code(course)
    return await curriculum.get_curriculum_topics(course)


@router.get("/curriculum")
async def list_curriculum_files(
    course: str = Query(...),
    curriculum: CurriculumManager = Depends(get_curriculum),
):
    course = validate_course_code(course)
    return await curriculum.list_curriculum(course)


@router.get("/courses/{course_code}/topics")
async def get_structured_topics(course_code: str):
    from app.topics import get_course_topics as get_topics
    course_code = validate_course_code(course_code)
    return await get_topics(course_code)


@router.get("/courses/{course_code}/coverage")
async def get_coverage(course_code: str):
    from app.topics import get_topic_coverage
    course_code = validate_course_code(course_code)
    return await get_topic_coverage(course_code)
