import asyncio
import base64
import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi import WebSocket, WebSocketDisconnect

from app.auth import get_current_user_from_request
from app.deps import get_engine, get_knowledge_state, get_rag
from app.knowledge_state import KnowledgeStateManager
from app.query_engine import QueryEngine
from app.rag import RAGPipeline
from app.schemas import ChatFeedbackRequest, ChunkItem, QueryRequest, QueryResponse
from app.validation import (
    MAX_QUESTION_LENGTH,
    sanitize_id,
    sanitize_text,
    validate_course_code,
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
    from app.provider_router import router

    surreal_ok = await SurrealDBManager.health_check()
    provider_ok = await router.health_check()

    deps_ok = [surreal_ok, provider_ok]
    status = "ok" if all(deps_ok) else "degraded"

    return {
        "status": status,
        "version": "1.0.0",
        "dependencies": {
            "surrealdb": "ok" if surreal_ok else "error",
            "gemini": "ok" if provider_ok else "error"
        }
    }


@router.post("/chat/feedback")
async def chat_feedback(
    body: ChatFeedbackRequest,
    ks: KnowledgeStateManager = Depends(get_knowledge_state),
    user: dict = Depends(get_current_user_from_request),
):
    user_email = user.get("email", "")
    course_code = validate_course_code(body.course_code)
    # ponytail: bloom-level classification skipped — add heuristic classifier here if needed
    await ks.update_state(user_email, course_code, "general", 0, body.helpful)
    return {"status": "updated"}


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


@router.websocket("/query/ws")
async def query_ws(
    websocket: WebSocket,
    token: str = Query(""),
):
    from app.auth import decode_token
    user = decode_token(token) if token else None
    if not user:
        await websocket.close(code=4001)
        return
    await websocket.accept()

    cancel_event = asyncio.Event()
    query_queue: asyncio.Queue = asyncio.Queue(maxsize=1)
    last_query_data = None
    gen_task = None

    async def receiver():
        nonlocal last_query_data, gen_task
        try:
            async for raw in websocket.iter_json():
                t = raw.get("type")
                if t == "ping":
                    await websocket.send_json({"type": "pong"})
                elif t == "cancel":
                    cancel_event.set()
                elif t == "regenerate":
                    if last_query_data is not None:
                        cancel_event.set()
                        if gen_task is not None and not gen_task.done():
                            gen_task.cancel()
                        await query_queue.put(last_query_data)
                elif t == "query":
                    data = raw.get("data", {})
                    last_query_data = data
                    cancel_event.set()
                    if gen_task is not None and not gen_task.done():
                        gen_task.cancel()
                    await query_queue.put(data)
        except WebSocketDisconnect:
            cancel_event.set()
            if gen_task is not None and not gen_task.done():
                gen_task.cancel()

    async def runner():
        nonlocal gen_task
        from app.chat_history import add_message, get_course_history
        from app.db import get_db
        from app.query_engine import QueryEngine
        engine = QueryEngine()
        while True:
            data = await query_queue.get()
            cancel_event.clear()
            gen_task = asyncio.current_task()

            full_response = ""
            metadata = {}

            try:
                history = await get_course_history(
                    data.get("course_code", ""),
                    data.get("session_id", "default"),
                )
                image_data = None
                image_ids = data.get("image_ids") or []
                if image_ids:
                    loaded = []
                    for img_id in image_ids:
                        img_path = (UPLOAD_DIR / img_id).resolve()
                        if not str(img_path).startswith(str(UPLOAD_DIR.resolve())):
                            continue
                        if not img_path.is_file():
                            continue
                        raw_bytes = img_path.read_bytes()
                        ext = img_path.suffix.lower()
                        mime = "image/jpeg" if ext == ".jpg" else "image/png"
                        loaded.append({"b64": base64.b64encode(raw_bytes).decode(), "mime": mime})
                    if loaded:
                        image_data = loaded

                async for chunk in engine.query_stream(
                    query=data.get("question", ""),
                    course_code=data.get("course_code", ""),
                    course_name=data.get("course_code", ""),
                    language=data.get("language", "English"),
                    mastery=data.get("mastery"),
                    bloom_level=data.get("bloom_level"),
                    history=history,
                    top_k=data.get("top_k", 5),
                    images=image_data,
                ):
                    if cancel_event.is_set():
                        break
                    await websocket.send_json(chunk)
                    if chunk["type"] == "content":
                        full_response += chunk["content"]
                    elif chunk["type"] == "metadata":
                        metadata = chunk

                if not cancel_event.is_set():
                    await websocket.send_json({"type": "done"})
                    if full_response:
                        try:
                            cc = data.get("course_code", "")
                            sid = data.get("session_id", "default")
                            uid = user.get("email", "")
                            q = data.get("question", "")
                            db = await get_db()
                            await db.query(
                                "CREATE query_log CONTENT { course_code: $cc, question: $q, response_preview: $r, cited_sources: $s, user_id: $uid, out_of_scope: false, timestamp: time::now() }",
                                {"cc": cc, "q": q, "r": full_response[:200], "s": metadata.get("cited_sources", []), "uid": uid},
                            )
                            user_content = json.dumps({"text": q, "images": image_ids})
                            await add_message(cc, sid, "user", user_content, user_id=uid)
                            await add_message(cc, sid, "assistant", full_response, user_id=uid)
                        except Exception as e:
                            logger.error("Failed to persist query_log for course=%s: %s", data.get("course_code"), e)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.exception("WS query failed")
                try:
                    await websocket.send_json({"type": "error", "content": str(e)})
                except Exception:
                    pass

    try:
        await asyncio.gather(receiver(), runner())
    except WebSocketDisconnect:
        pass
    finally:
        cancel_event.set()
        if gen_task is not None and not gen_task.done():
            gen_task.cancel()


@router.post("/query-stream")
async def query_stream(
    body: QueryRequest,
    engine: QueryEngine = Depends(get_engine),
    user: dict = Depends(get_current_user_from_request),
):
    course_code = validate_course_code(body.course_code)
    session_id = sanitize_id(body.session_id)
    question = sanitize_text(body.question, MAX_QUESTION_LENGTH)
    user_email = user.get("email", "")

    from app.chat_history import add_message, get_course_history

    history = await get_course_history(body.course_code, body.session_id)

    image_data = _load_images(body.image_ids)

    async def stream_generator():
        full_response = ""
        metadata = {}
        chunk_count = 0

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
            chunk_count += 1
            ctype = chunk["type"]
            clen = len(chunk.get("content", "") or chunk.get("cited_sources", "") or json.dumps(chunk))
            preview = json.dumps(chunk)[:500]
            logger.info("SSE chunk #%d type=%s len=%d data=%s", chunk_count, ctype, clen, preview)

            if ctype == "content":
                full_response += chunk["content"]
            elif ctype == "metadata":
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
    engine: QueryEngine = Depends(get_engine),
    user: dict = Depends(get_current_user_from_request),
):
    course_code = validate_course_code(body.course_code)
    session_id = sanitize_id(body.session_id)
    question = sanitize_text(body.question, MAX_QUESTION_LENGTH)
    user_email = user.get("email", "")

    from app.chat_history import add_message, get_course_history

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
