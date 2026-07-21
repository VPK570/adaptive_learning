from fastapi import APIRouter, Depends, Query, HTTPException

from app.deps import get_rag, get_saved_content
from app.rag import RAGPipeline
from app.saved_content import SavedContentManager
from app.schemas import QuizRequest, SaveQuizRequest
from app.validation import validate_course_code, sanitize_text, MAX_TOPIC_LENGTH
from app.provider_router import router as client
from app.routers.flashcards import safe_json_parse

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
    prompt = f"""Based on the following course materials, generate {body.count} multiple-choice quiz questions for the topic: {topic}.
Return ONLY a JSON array of objects, each with:
- 'question': the question text
- 'options': an array of 4 string options
- 'correct_index': the 0-based index of the correct option
- 'explanation': a brief explanation of why that's correct
- 'user_answer_index': -1 (placeholder)
- 'is_correct': false (placeholder)

Ensure the JSON is complete and valid. Do not truncate the output.

MATERIALS:
{context}
"""
    response = await client.chat(
        [{"role": "user", "content": prompt}], temperature=0.3, max_tokens=2048
    )

    result = safe_json_parse(response)
    if result is None:
        raise HTTPException(500, "Failed to generate valid JSON for quiz.")
    return result


@router.post("/quiz/save")
async def save_quiz(
    body: SaveQuizRequest,
    saved_content: SavedContentManager = Depends(get_saved_content),
):
    course_code = validate_course_code(body.course_code)
    topic = sanitize_text(body.topic, MAX_TOPIC_LENGTH)
    return await saved_content.save_quiz(course_code, topic, body.questions, body.score)


@router.get("/quiz/saved")
async def get_saved_quizzes(
    course: str = Query(...),
    saved_content: SavedContentManager = Depends(get_saved_content),
):
    course = validate_course_code(course)
    return await saved_content.get_saved_quizzes(course)


@router.delete("/quiz/saved/{quiz_id}")
async def delete_saved_quiz(
    quiz_id: str,
    saved_content: SavedContentManager = Depends(get_saved_content),
):
    try:
        if not await saved_content.delete_quiz(quiz_id):
            raise HTTPException(404, "Quiz not found.")
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(400, str(e))
