import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import get_current_user_from_request
from app.config import settings
from app.courses import get_all_courses_data
from app.db import get_db
from app.deps import get_rag
from app.knowledge_state import BLOOM_LABELS
from app.provider_router import router as client
from app.query_enhancer import generate_search_queries
from app.rag import RAGPipeline
from app.schemas import FlashcardRequest, RecordFlashcardRequest, SaveFlashcardRequest
from app.topics import get_course_topics
from app.validation import MAX_TOPIC_LENGTH, sanitize_text, validate_course_code

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

    courses = await get_all_courses_data()
    course_info = next((c for c in courses if c["course_code"] == course_code), {})
    db = await get_db()
    rows = await db.query(
        "SELECT source_title, text FROM text_chunk WHERE course_code = $code ORDER BY source_title LIMIT 50",
        {"code": course_code},
    ) or []
    doc_previews = []
    seen = set()
    for r in rows:
        t = r["source_title"]
        if t not in seen:
            seen.add(t)
            doc_previews.append({"name": t, "preview": (r.get("text") or "")[:200]})
    topics = await get_course_topics(course_code)
    curr_text = "\n".join(
        f"{t['topic_name']}" + (" — " + "; ".join(t.get("subtopics", [])) if t.get("subtopics") else "")
        for t in topics
    ) if topics else ""
    course_ctx = {
        "course_name": course_info.get("course_name", course_code),
        "course_description": course_info.get("description", ""),
        "documents": doc_previews,
        "curriculum_topics": curr_text,
    }

    search_queries = [topic]
    if settings.QUERY_ENHANCER_ENABLED:
        enhanced = await generate_search_queries(topic, course_ctx, settings.QUERY_ENHANCER_NUM_QUERIES, model=settings.QUIZ_MODEL)
        search_queries = list(dict.fromkeys(enhanced + [topic]))

    all_chunks = []
    seen_ids = set()
    for sq in search_queries:
        for c in await rag.retrieve(query=sq, course_code=course_code, top_k=5):
            cid = c.get("chunk_id") or str(c.get("id", ""))
            if cid not in seen_ids:
                seen_ids.add(cid)
                all_chunks.append(c)

    if not all_chunks:
        raise HTTPException(404, "No materials found to generate flashcards.")

    chunks = all_chunks[:10]
    context = "\n".join(c["text"] for c in chunks if c.get("text"))

    bloom_instruction = ""
    if body.bloom_levels:
        labels = [BLOOM_LABELS.get(bl, f"Level {bl}") for bl in body.bloom_levels]
        bloom_instruction = f" Generate flashcards at these Bloom's Taxonomy levels: {', '.join(labels)}."

    prompt = f"""Based on the following course materials, generate {body.count} flashcards for the topic: {topic}.
{bloom_instruction}Return ONLY a JSON array of objects, each with 'question', 'answer', and 'bloom_level' (integer 1-6) fields.
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
    user: dict = Depends(get_current_user_from_request),
):
    course_code = validate_course_code(body.course_code)
    topic = sanitize_text(body.topic, MAX_TOPIC_LENGTH)
    user_email = user.get("email", "")

    from app.db import get_db
    db = await get_db()
    result = await db.query(
        "CREATE flashcard_set CONTENT { user_id: $uid, course_code: $cc, topic: $t, cards: $c, created_at: time::now() }",
        {"uid": user_email, "cc": course_code, "t": topic, "c": body.cards},
    )
    return {"id": str(result[0]["id"]) if result else None, "status": "saved"}


@router.get("/flashcards/saved")
async def list_saved_flashcards(course: str = Query(...), user: dict = Depends(get_current_user_from_request)):
    course_code = validate_course_code(course)
    db = await get_db()
    rows = await db.query(
        "SELECT * FROM flashcard_set WHERE course_code = $cc AND user_id = $uid ORDER BY created_at DESC",
        {"cc": course_code, "uid": user["email"]},
    )
    return [
        {
            "id": str(r["id"]),
            "course_code": r.get("course_code"),
            "topic": r.get("topic"),
            "cards": r.get("cards"),
            "times_studied": r.get("times_studied") or 0,
            "best_recall": r.get("best_recall"),
            "last_recall": r.get("last_recall"),
            "created_at": str(r.get("created_at")) if r.get("created_at") else None,
        }
        for r in (rows or [])
    ]


@router.post("/flashcards/saved/{set_id}/record")
async def record_flashcard_study(
    set_id: str,
    body: RecordFlashcardRequest,
    user: dict = Depends(get_current_user_from_request),
):
    db = await get_db()
    rows = await db.query(
        "SELECT * FROM flashcard_set WHERE id = type::record($id) AND user_id = $uid",
        {"id": set_id, "uid": user["email"]},
    ) or []
    if not rows:
        raise HTTPException(404, "Flashcard set not found or not owned by you")
    recall = round(body.known_count / body.total * 100)
    current = rows[0]
    times = (current.get("times_studied") or 0) + 1
    best = max(current.get("best_recall") or 0, recall)
    await db.query(
        "UPDATE flashcard_set SET times_studied = $ts, best_recall = $br, last_recall = $lr WHERE id = type::record($id) AND user_id = $uid",
        {"id": set_id, "uid": user["email"], "ts": times, "br": best, "lr": recall},
    )
    return {"id": set_id, "times_studied": times, "best_recall": best, "last_recall": recall, "status": "recorded"}


@router.delete("/flashcards/saved/{set_id}")
async def delete_saved_flashcards(set_id: str, user: dict = Depends(get_current_user_from_request)):
    db = await get_db()
    result = await db.query(
        "DELETE flashcard_set WHERE id = type::record($id) AND user_id = $uid RETURN BEFORE",
        {"id": set_id, "uid": user["email"]},
    )
    if not result:
        raise HTTPException(404, "Flashcard set not found or not owned by you")
    return {"status": "deleted"}
