from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth import get_current_user
from app.deps import get_rag
from app.db import get_db
from app.rag import RAGPipeline
from app.schemas import QuizRequest, SaveQuizRequest
from app.validation import validate_course_code, sanitize_text, MAX_TOPIC_LENGTH
from app.provider_router import router as client
from app.routers.flashcards import safe_json_parse
from app.knowledge_state import BLOOM_LABELS
from app.config import settings

router = APIRouter()


@router.post("/quiz")
async def generate_quiz(
    body: QuizRequest,
    rag: RAGPipeline = Depends(get_rag),
):
    course_code = validate_course_code(body.course_code)
    topic = sanitize_text(body.topic, MAX_TOPIC_LENGTH)

    if not topic:
        raise HTTPException(400, "Quiz topic cannot be empty.")

    chunks = await rag.retrieve(query=topic, course_code=course_code, top_k=10)
    if not chunks:
        raise HTTPException(404, "No materials found to generate a quiz.")

    context = "\n".join([c["text"] for c in chunks if c.get("text")])

    bloom_instruction = ""
    if body.bloom_levels:
        labels = [BLOOM_LABELS.get(bl, f"Level {bl}") for bl in body.bloom_levels]
        bloom_instruction = f"Generate questions at these Bloom's Taxonomy levels: {', '.join(labels)}.\nEach question must be tagged with its Bloom's level in a 'bloom_level' field (1-6).\n"

    prompt = f"""Based on the following course materials, generate {body.count} multiple-choice quiz questions for the topic: {topic}.
{bloom_instruction}Return ONLY a JSON array of objects, each with:
- 'question': the question text
- 'options': an array of 4 string options
- 'correct_index': the 0-based index of the correct option
- 'explanation': a brief explanation of why that's correct
- 'bloom_level': an integer 1-6 indicating the Bloom's Taxonomy level
- 'user_answer_index': -1 (placeholder)
- 'is_correct': false (placeholder)

Ensure the JSON is complete and valid. Do not truncate the output.

MATERIALS:
{context}
"""
    response = await client.chat(
        [{"role": "user", "content": prompt}],
        model=settings.QUIZ_MODEL,
        temperature=0.3,
        max_tokens=4096,
    )

    result = safe_json_parse(response)
    if result is None:
        raise HTTPException(500, "Failed to generate valid JSON for quiz.")
    return result


@router.post("/quiz/save")
async def save_quiz(
    body: SaveQuizRequest,
    request: Request,
):
    course_code = validate_course_code(body.course_code)
    topic = sanitize_text(body.topic, MAX_TOPIC_LENGTH)
    user_email = request.state.user.get("email", "") if hasattr(request.state, "user") else ""

    from app.db import get_db
    db = await get_db()
    result = await db.query(
        "CREATE quiz CONTENT { user_id: $uid, course_code: $cc, topic: $t, bloom_levels: $bls, questions: $q, score: $s, total: $tot, created_at: time::now() }",
        {"uid": user_email, "cc": course_code, "t": topic, "bls": body.bloom_levels, "q": body.questions, "s": body.score, "tot": body.total},
    )
    return {"id": str(result[0]["id"]) if result else None, "status": "saved"}


@router.get("/quiz/saved")
async def list_saved_quizzes(course: str = Query(...), _=Depends(get_current_user)):
    course_code = validate_course_code(course)
    db = await get_db()
    rows = await db.query(
        "SELECT * FROM quiz WHERE course_code = $cc ORDER BY created_at DESC",
        {"cc": course_code},
    )
    return [
        {
            "id": str(r["id"]),
            "course_code": r.get("course_code"),
            "topic": r.get("topic"),
            "score": r.get("score"),
            "total": r.get("total"),
            "created_at": str(r.get("created_at")) if r.get("created_at") else None,
        }
        for r in (rows or [])
    ]


@router.delete("/quiz/saved/{quiz_id}")
async def delete_saved_quiz(quiz_id: str, user: dict = Depends(get_current_user)):
    db = await get_db()
    result = await db.query(
        "DELETE quiz WHERE id = $id AND user_id = $uid RETURN BEFORE",
        {"id": quiz_id, "uid": user["email"]},
    )
    if not result:
        raise HTTPException(404, "Quiz not found or not owned by you")
    return {"status": "deleted"}
