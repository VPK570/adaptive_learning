import base64
import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.deps import get_rag, get_engine
from app.rag import RAGPipeline
from app.query_engine import QueryEngine
from app.schemas import QueryRequest, QueryResponse, ChunkItem
from app.validation import (
    validate_course_code,
    sanitize_id,
    sanitize_text,
    MAX_QUESTION_LENGTH,
)

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "chat"


def _load_images(image_ids: list[str]) -> list[dict]:
    if not image_ids:
        return []
    loaded = []
    for img_id in image_ids:
        img_path = (UPLOAD_DIR / img_id).resolve()
        base = UPLOAD_DIR.resolve()
        if not str(img_path).startswith(str(base)):
            raise HTTPException(status_code=400, detail=f"Invalid image: {img_id}")
        if not img_path.is_file():
            raise HTTPException(status_code=400, detail=f"Image not found: {img_id}")
        data = img_path.read_bytes()
        ext = img_path.suffix.lower()
        mime = "image/jpeg" if ext == ".jpg" else "image/png"
        loaded.append({"b64": base64.b64encode(data).decode(), "mime": mime})
    return loaded


@router.get("/health")
async def health():
    from app.db import SurrealDBManager
    from app.openrouter import client
    
    surreal_ok = await SurrealDBManager.health_check()
    openrouter_ok = await client.health_check()
    
    deps_ok = [surreal_ok, openrouter_ok]
    status = "ok" if all(deps_ok) else "degraded"
    
    return {
        "status": status,
        "version": "1.0.0",
        "dependencies": {
            "surrealdb": "ok" if surreal_ok else "error",
            "openrouter": "ok" if openrouter_ok else "error"
        }
    }


@router.get("/stats")
async def get_stats(course_code: str = "BAECE102", rag: RAGPipeline = Depends(get_rag)):
    course_code = validate_course_code(course_code)
    stats = await rag.get_course_stats(course_code)
    return stats


@router.get("/chunks")
async def get_chunks(
    course_code: str = "BAECE102",
    query: str = "",
    top_k: int = 5,
    rag: RAGPipeline = Depends(get_rag),
):
    course_code = validate_course_code(course_code)
    q = sanitize_text(query, MAX_QUESTION_LENGTH)

    chunks = await rag.retrieve(query=q, course_code=course_code, top_k=top_k)
    return [
        ChunkItem(
            chunk_id=c["chunk_id"],
            text=c["text"],
            source_title=c["source_title"],
            page=c["page"],
            content_type=c["content_type"],
            score=round(1 - c["distance"], 3),
        )
        for c in chunks
    ]


@router.post("/query-stream")
async def query_stream(
    body: QueryRequest,
    request: Request,
    engine: QueryEngine = Depends(get_engine),
):
    course_code = validate_course_code(body.course_code)
    session_id = sanitize_id(body.session_id)
    question = sanitize_text(body.question, MAX_QUESTION_LENGTH)
    user_email = request.state.user.get("email", "") if hasattr(request.state, "user") else ""

    from app.chat_history import get_course_history, add_message

    history = await get_course_history(body.course_code, body.session_id)

    image_data = _load_images(body.image_ids)

    async def stream_generator():
        full_response = ""
        metadata = {}

        async for chunk in engine.query_stream(
            query=question,
            course_code=course_code,
            course_name=course_code,
            language=body.language,
            mastery=body.mastery,
            bloom_level=body.bloom_level,
            history=history,
            top_k=body.top_k,
            images=image_data or None,
        ):
            if chunk["type"] == "content":
                full_response += chunk["content"]
            elif chunk["type"] == "metadata":
                metadata = chunk

            yield f"data: {json.dumps(chunk)}\n\n"

        if full_response:
            try:
                from app.db import get_db
                db = await get_db()
                await db.query(
                    "CREATE query_log CONTENT { course_code: $cc, question: $q, response_preview: $r, cited_sources: $s, user_id: $uid, out_of_scope: false, timestamp: time::now() }",
                    {"cc": course_code, "q": question, "r": full_response[:200], "s": metadata.get("cited_sources", []), "uid": user_email},
                )
                user_content = json.dumps({"text": question, "images": body.image_ids})
                await add_message(course_code, session_id, "user", user_content, user_id=user_email)
                await add_message(course_code, session_id, "assistant", full_response, user_id=user_email)
            except Exception as e:
                logger.error("Failed to persist query_log for course=%s: %s", course_code, e)

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


@router.post("/query", response_model=QueryResponse)
async def query(
    body: QueryRequest,
    request: Request,
    engine: QueryEngine = Depends(get_engine),
):
    course_code = validate_course_code(body.course_code)
    session_id = sanitize_id(body.session_id)
    question = sanitize_text(body.question, MAX_QUESTION_LENGTH)
    user_email = request.state.user.get("email", "") if hasattr(request.state, "user") else ""

    from app.chat_history import get_course_history, add_message

    history = await get_course_history(body.course_code, body.session_id)

    image_data = _load_images(body.image_ids)

    result = await engine.query(
        query=question,
        course_code=course_code,
        course_name=course_code,
        language=body.language,
        mastery=body.mastery,
        bloom_level=body.bloom_level,
        history=history,
        top_k=body.top_k,
        images=image_data or None,
    )

    from app.db import get_db
    _db = await get_db()
    await _db.query(
        "CREATE query_log CONTENT { course_code: $cc, question: $q, response_preview: $r, cited_sources: $s, user_id: $uid, out_of_scope: false, timestamp: time::now() }",
        {"cc": course_code, "q": question, "r": result["response"][:200], "s": result["cited_sources"], "uid": user_email},
    )
    user_content = json.dumps({"text": question, "images": body.image_ids})
    await add_message(course_code, session_id, "user", user_content, user_id=user_email)
    await add_message(course_code, session_id, "assistant", result["response"], user_id=user_email)

    return QueryResponse(
        response=result["response"],
        cited_sources=result["cited_sources"],
        chunks_retrieved=result["chunks_retrieved"],
        text_chunks=result["text_chunks"],
        image_chunks=result["image_chunks"],
    )
