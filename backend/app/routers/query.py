import json

from fastapi import APIRouter, Depends
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
from app.analytics import log_query
from app.chat_history import get_course_history, add_message

router = APIRouter()


@router.get("/health")
async def health():
    from app.db import SurrealDBManager
    from app.database import Database
    from app.openrouter import client
    
    pg_ok = await Database.health_check()
    surreal_ok = await SurrealDBManager.health_check()
    openrouter_ok = await client.health_check()
    
    deps_ok = [pg_ok, surreal_ok, openrouter_ok]
    status = "ok" if all(deps_ok) else "degraded"
    
    return {
        "status": status,
        "version": "1.0.0",
        "dependencies": {
            "postgres": "ok" if pg_ok else "error",
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
    engine: QueryEngine = Depends(get_engine),
):
    course_code = validate_course_code(body.course_code)
    session_id = sanitize_id(body.session_id)
    question = sanitize_text(body.question, MAX_QUESTION_LENGTH)

    history = await get_course_history(body.course_code, body.session_id)

    async def stream_generator():
        full_response = ""
        metadata = {}

        async for chunk in engine.query_stream(
            query=question,
            course_code=course_code,
            course_name=course_code,
            language=body.language,
            mastery=body.mastery,
            history=history,
            top_k=body.top_k,
        ):
            if chunk["type"] == "content":
                full_response += chunk["content"]
            elif chunk["type"] == "metadata":
                metadata = chunk

            yield f"data: {json.dumps(chunk)}\n\n"

        if full_response:
            await log_query(
                question, course_code, full_response, metadata.get("cited_sources", [])
            )
            await add_message(course_code, session_id, "user", question)
            await add_message(course_code, session_id, "assistant", full_response)

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


@router.post("/query", response_model=QueryResponse)
async def query(
    body: QueryRequest,
    engine: QueryEngine = Depends(get_engine),
):
    course_code = validate_course_code(body.course_code)
    session_id = sanitize_id(body.session_id)
    question = sanitize_text(body.question, MAX_QUESTION_LENGTH)

    history = await get_course_history(body.course_code, body.session_id)

    result = await engine.query(
        query=question,
        course_code=course_code,
        course_name=course_code,
        language=body.language,
        mastery=body.mastery,
        history=history,
        top_k=body.top_k,
    )

    await log_query(question, course_code, result["response"], result["cited_sources"])
    await add_message(course_code, session_id, "user", question)
    await add_message(course_code, session_id, "assistant", result["response"])

    return QueryResponse(
        response=result["response"],
        cited_sources=result["cited_sources"],
        chunks_retrieved=result["chunks_retrieved"],
        text_chunks=result["text_chunks"],
        image_chunks=result["image_chunks"],
    )
