import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth import get_current_user
from app.deps import get_rag
from app.db import get_db
from app.rag import RAGPipeline
from app.schemas import FlashcardRequest, SaveFlashcardRequest
from app.validation import validate_course_code, sanitize_text, MAX_TOPIC_LENGTH
from app.openrouter import client
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def safe_json_parse(response_str: str):
    if not response_str:
        return None
    try:
        json_str = response_str.strip()
        if json_str.startswith("```json"):
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif json_str.startswith("```"):
            json_str = json_str.split("```")[1].split("```")[0].strip()
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Error parsing JSON: {e}\nResponse: {response_str}")
        return None


@router.post("/flashcards")
async def generate_flashcards(
    body: FlashcardRequest,
    rag: RAGPipeline = Depends(get_rag),
):
    course_code = validate_course_code(body.course_code)
    topic = sanitize_text(body.topic, MAX_TOPIC_LENGTH)

    chunks = await rag.retrieve(query=topic, course_code=course_code, top_k=10)
    if not chunks:
        raise HTTPException(404, "No materials found to generate flashcards.")

    context = "\n".join([c["text"] for c in chunks if c.get("text")])

    prompt = f"""Based on the following course materials, generate {body.count} flashcards for the topic: {topic}.
Return ONLY a JSON array of objects, each with 'question', 'answer', and 'bloom_level' (integer 1-6) fields.
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
        raise HTTPException(500, "Failed to generate valid JSON for flashcards.")
    return result


@router.post("/flashcards/save")
async def save_flashcards(
    body: SaveFlashcardRequest,
    request: Request,
):
    course_code = validate_course_code(body.course_code)
    topic = sanitize_text(body.topic, MAX_TOPIC_LENGTH)
    user_email = request.state.user.get("email", "") if hasattr(request.state, "user") else ""

    from app.db import get_db
    db = await get_db()
    result = await db.query(
        "CREATE flashcard_set CONTENT { user_id: $uid, course_code: $cc, topic: $t, cards: $c, created_at: time::now() }",
        {"uid": user_email, "cc": course_code, "t": topic, "c": body.cards},
    )
    return {"id": str(result[0]["id"]) if result else None, "status": "saved"}


@router.get("/flashcards/saved")
async def list_saved_flashcards(course: str = Query(...), _=Depends(get_current_user)):
    course_code = validate_course_code(course)
    db = await get_db()
    rows = await db.query(
        "SELECT * FROM flashcard_set WHERE course_code = $cc ORDER BY created_at DESC",
        {"cc": course_code},
    )
    return [
        {
            "id": str(r["id"]),
            "course_code": r.get("course_code"),
            "topic": r.get("topic"),
            "created_at": str(r.get("created_at")) if r.get("created_at") else None,
        }
        for r in (rows or [])
    ]


@router.delete("/flashcards/saved/{set_id}")
async def delete_saved_flashcards(set_id: str, user: dict = Depends(get_current_user)):
    db = await get_db()
    result = await db.query(
        "DELETE flashcard_set WHERE id = $id AND user_id = $uid RETURN BEFORE",
        {"id": set_id, "uid": user["email"]},
    )
    if not result:
        raise HTTPException(404, "Flashcard set not found or not owned by you")
    return {"status": "deleted"}
