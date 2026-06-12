from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_rag
from app.rag import RAGPipeline
from app.schemas import PaperRequest
from app.validation import validate_course_code, sanitize_text, MAX_TOPIC_LENGTH
from app.paper_generator import generate_paper

router = APIRouter()


@router.post("/generate-paper")
async def create_paper(
    body: PaperRequest,
    rag: RAGPipeline = Depends(get_rag),
):
    course_code = validate_course_code(body.course_code)
    sanitized_topics = [sanitize_text(t, MAX_TOPIC_LENGTH) for t in body.topics]
    query_str = (
        " ".join(sanitized_topics) if sanitized_topics else "overview of the course"
    )

    chunks = await rag.retrieve(
        query=query_str, course_code=course_code, top_k=body.top_k
    )

    if not chunks:
        raise HTTPException(404, "No course content found to generate a paper from.")

    paper = await generate_paper(
        course_code=course_code,
        total_marks=body.total_marks,
        difficulty=body.difficulty,
        topics=sanitized_topics,
        chunks=chunks,
    )
    return paper
