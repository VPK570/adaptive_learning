from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import get_current_user_from_request
from app.bloom_classifier import classify_bloom_levels
from app.config import settings
from app.courses import get_all_courses_data
from app.db import get_db
from app.deps import get_knowledge_state, get_rag
from app.knowledge_state import BLOOM_LABELS, KnowledgeStateManager
from app.provider_router import router as client
from app.query_enhancer import generate_search_queries
from app.rag import RAGPipeline
from app.routers.flashcards import safe_json_parse
from app.schemas import QuizRequest, SaveQuizRequest
from app.topics import get_course_topics
from app.validation import MAX_TOPIC_LENGTH, sanitize_text, validate_course_code

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
        raise HTTPException(404, "No materials found to generate a quiz.")

    chunks = all_chunks[:10]
    context = "\n".join(c["text"] for c in chunks if c.get("text"))

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

    if settings.BLOOM_VALIDATION_ENABLED:
        questions = [q["question"] for q in result if q.get("question")]
        if questions:
            detected = await classify_bloom_levels(questions)
            for i, d in enumerate(detected):
                if d is not None and i < len(result):
                    result[i]["bloom_level"] = d

    return result


@router.post("/quiz/save")
async def save_quiz(
    body: SaveQuizRequest,
    ks: KnowledgeStateManager = Depends(get_knowledge_state),
    user: dict = Depends(get_current_user_from_request),
):
    course_code = validate_course_code(body.course_code)
    topic = sanitize_text(body.topic, MAX_TOPIC_LENGTH)
    user_email = user.get("email", "")
    student_id = user_email

    updates = []
    for q in body.questions:
        bloom_level = q.get("bloom_level")
        is_correct = q.get("is_correct", False)
        if bloom_level and 1 <= bloom_level <= 6:
            updates.append(ks.update_state(student_id, course_code, topic, bloom_level, is_correct))
    if updates:
        # ponytail: update_state is check-then-act (SELECT->UPDATE->CREATE); concurrent
        # same-key calls collide on the ks_student_course unique index. Serialize here —
        # only sequential callers exist today. Per-key lock if concurrent callers appear.
        for update in updates:
            await update

    from app.db import get_db
    db = await get_db()
    result = await db.query(
        "CREATE quiz CONTENT { user_id: $uid, course_code: $cc, topic: $t, bloom_levels: $bls, questions: $q, score: $s, total: $tot, created_at: time::now() }",
        {"uid": user_email, "cc": course_code, "t": topic, "bls": body.bloom_levels, "q": body.questions, "s": body.score, "tot": body.total},
    )
    return {"id": str(result[0]["id"]) if result else None, "status": "saved"}


@router.get("/quiz/saved")
async def list_saved_quizzes(course: str = Query(...), user: dict = Depends(get_current_user_from_request)):
    course_code = validate_course_code(course)
    db = await get_db()
    rows = await db.query(
        "SELECT * FROM quiz WHERE course_code = $cc AND user_id = $uid ORDER BY created_at DESC",
        {"cc": course_code, "uid": user["email"]},
    )
    return [
        {
            "id": str(r["id"]),
            "course_code": r.get("course_code"),
            "topic": r.get("topic"),
            "score": r.get("score"),
            "total": r.get("total"),
            "questions": r.get("questions"),
            "bloom_levels": r.get("bloom_levels"),
            "created_at": str(r.get("created_at")) if r.get("created_at") else None,
        }
        for r in (rows or [])
    ]


@router.delete("/quiz/saved/{quiz_id}")
async def delete_saved_quiz(quiz_id: str, user: dict = Depends(get_current_user_from_request)):
    db = await get_db()
    result = await db.query(
        "DELETE quiz WHERE id = type::record($id) AND user_id = $uid RETURN BEFORE",
        {"id": quiz_id, "uid": user["email"]},
    )
    if not result:
        raise HTTPException(404, "Quiz not found or not owned by you")
    return {"status": "deleted"}
