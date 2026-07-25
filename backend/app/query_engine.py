"""Query engine — builds prompts, calls LLM, enforces citations.

Handles both text and image chunks in the context window.
"""
import logging
from typing import Any, AsyncGenerator, Dict

logger = logging.getLogger(__name__)

from app.citation import extract_all_citations, parse_citation, remove_uncited_claims, validate_citations
from app.config import settings
from app.db import get_db
from app.gatekeeper import gatekeeper
from app.knowledge_state import BLOOM_LABELS, BLOOM_PROMPTS
from app.provider_router import router as client
from app.rag import RAGPipeline
from app.validation import sanitize_student_query
from app.verifier import verifier


def _normalize_cited_sources(sources: list[dict]) -> list[dict]:
    result = []
    for s in sources:
        result.append({
            "source_title": str(s.get("source_title", "")),
            "page": str(s["page"]) if s.get("page") is not None else "",
            "content_type": str(s.get("content_type", "text")),
            "has_image": bool(s.get("has_image", False)),
        })
    return result


def extract_cited_sources(response_text: str, chunks: list[dict]) -> list[dict]:
    """Match citations in the response back to retrieved chunks, deduped."""
    citations = extract_all_citations(response_text)
    actually_cited = []
    seen_keys = set()
    for cit in citations:
        c_title, c_page = parse_citation(cit)
        if not c_title or not c_page:
            continue
        for c in chunks:
            v_title = c.get("source_title", "").lower()
            v_page = str(c.get("page", ""))
            key = (v_title, v_page)
            if key in seen_keys:
                continue
            if v_page == c_page and (v_title in c_title or c_title in v_title):
                actually_cited.append({
                    "source_title": c.get("source_title", ""),
                    "page": str(c["page"]) if c.get("page") is not None else "",
                    "content_type": c.get("content_type", "text"),
                    "has_image": c.get("has_image", False),
                })
                seen_keys.add(key)
    return _normalize_cited_sources(actually_cited)

def build_tutor_system_prompt(
    course_name: str,
    course_code: str,
    language: str = "English",
    mastery: float | None = None,
    bloom_level: int | None = None,
) -> str:
    mastery_section = ""
    if mastery is not None:
        if mastery >= 0.70:
            mastery_section = "Student has strong mastery. Use deeper questions that require synthesis and evaluation."
        elif mastery >= 0.50:
            mastery_section = "Student has moderate mastery. Use scaffolded questions with examples."
        elif mastery >= 0.30:
            mastery_section = "Student is struggling. Use simpler diagnostic questions, break concepts into smaller parts."
        else:
            mastery_section = "Student has low mastery. Revisit prerequisites, use guided worked examples."

    bloom_section = ""
    if bloom_level is not None:
        label = BLOOM_LABELS.get(bloom_level, f"Level {bloom_level}")
        prompt = BLOOM_PROMPTS.get(bloom_level, "")
        bloom_section = f"BLOOM'S TAXONOMY LEVEL: {label}\n{prompt}\n"

    return f"""You are an expert {course_name} tutor for VIT students.
Student is enrolled in {course_code} at VIT Vellore.
Preferred language: {language}.

{mastery_section}

{bloom_section}

RULES:
- Use the provided course materials as your primary source.
- If the course materials do not fully cover the question, you may supplement with your general knowledge.
- Every factual claim MUST include an inline citation when sourced from materials.
- ONLY use citations from the "VALID CITATIONS LIST" provided in the context.
- Format: [Source: title, Slide N] or [Source: title, Page N]
- If an image is relevant, describe what you see in it: "As shown in the diagram [Source: title, Slide N]..."
- Respond in {language}.

SAFETY:
- Never write complete assignment solutions
- Never help with live exams
- Never bypass plagiarism detection"""


def build_context_window(
    chunks: list[dict],
    history: list[dict],
    max_turns: int = settings.MAX_HISTORY_TURNS,
) -> str:
    parts = ["COURSE MATERIALS:"]

    text_chunks = [c for c in chunks if c.get("content_type", "text") != "image"]
    image_chunks = [c for c in chunks if c.get("content_type") == "image" or c.get("has_image")]

    available_citations = []

    for i, c in enumerate(text_chunks, 1):
        title = c.get("source_title", "Unknown")
        page = c.get("page", "?")
        text = c.get("text", "")
        is_curriculum = c.get("source_type") == "curriculum"
        tag = "Curriculum" if is_curriculum else "Text"
        loc = "Page" if is_curriculum else "Slide"

        parts.append(f"<{tag} {i}: {title}, {loc} {page}>\n{text}\n</{tag} {i}>")
        available_citations.append(f"[{'Curriculum' if is_curriculum else 'Source'}: {title}, {loc} {page}]")

    if image_chunks:
        parts.append("\nRELEVANT IMAGES FROM COURSE MATERIALS:")
        for i, c in enumerate(image_chunks, 1):
            title = c.get("source_title", "Unknown")
            page = c.get("page", "?")
            text = c.get("text", "")
            parts.append(
                f"<Image {i}: {title}, Slide {page}>\n"
                f"{text}\n"
                f"</Image {i}>"
            )
            available_citations.append(f"[Source: {title}, Slide {page}]")

    if available_citations:
        parts.append("\nVALID CITATIONS LIST (ONLY use these exact labels):")
        for cite in sorted(list(set(available_citations))):
            parts.append(f"- {cite}")

    if history:
        parts.append("\nCONVERSATION HISTORY:")
        recent = history[-max_turns:]
        for turn in recent:
            parts.append(f"{turn.get('role', 'user').upper()}: {turn.get('content', '')}")
        if len(history) > max_turns:
            parts.append(f"[{len(history) - max_turns} earlier turns summarized for brevity]")

    return "\n\n".join(parts)


def build_tutor_prompt(
    query: str,
    course_code: str,
    course_name: str,
    chunks: list[dict],
    history: list[dict] | None = None,
    language: str = "English",
    mastery: float | None = None,
    bloom_level: int | None = None,
) -> list[dict[str, str]]:
    system = build_tutor_system_prompt(course_name, course_code, language, mastery, bloom_level)
    context = build_context_window(chunks, history or [])

    safe_query = sanitize_student_query(query)
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"{context}\n\nSTUDENT: {safe_query}"},
    ]


class QueryEngine:
    def __init__(self):
        self._rag_pipeline: RAGPipeline | None = None
        self._rag = None

    @property
    def rag_pipeline(self) -> RAGPipeline:
        if self._rag_pipeline is None:
            self._rag_pipeline = RAGPipeline()
        return self._rag_pipeline

    async def _get_course_context(self, course_code: str) -> dict:
        from app.courses import get_all_courses_data
        from app.topics import get_course_topics

        courses = await get_all_courses_data()
        course_info = next((c for c in courses if c["course_code"] == course_code), {})

        db = await get_db()
        rows = await db.query(
            "SELECT source_title, text, page FROM text_chunk WHERE course_code = $code ORDER BY source_title, page LIMIT 50",
            {"code": course_code},
        ) or []
        doc_previews = []
        seen = set()
        for r in rows:
            title = r["source_title"]
            if title not in seen:
                seen.add(title)
                doc_previews.append({
                    "name": title,
                    "preview": (r.get("text") or "")[:200],
                })

        topic_rows = await db.query(
            "SELECT topic, count() as cnt FROM text_chunk WHERE course_code = $code AND topic != '' GROUP BY topic",
            {"code": course_code},
        ) or []
        topic_coverage = {r["topic"]: r["cnt"] for r in topic_rows}

        topics = await get_course_topics(course_code)
        if topics:
            lines = []
            for t in topics:
                subs = "; ".join(t.get("subtopics", []))
                lines.append(f"{t['topic_name']}" + (f" — {subs}" if subs else ""))
            curriculum_text = "\n".join(lines)
        else:
            curriculum_text = ""

        return {
            "course_name": course_info.get("course_name", course_code),
            "course_description": course_info.get("description", ""),
            "documents": doc_previews,
            "curriculum_topics": curriculum_text,
            "topic_coverage": topic_coverage,
        }

    async def query_stream(
        self,
        query: str,
        course_code: str,
        course_name: str,
        history: list[dict] | None = None,
        language: str = "English",
        mastery: float | None = None,
        top_k: int = 5,
        bloom_level: int | None = None,
        images: list[dict] | None = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        course_ctx = await self._get_course_context(course_code)
        logger.info("QUERY_STREAM: course=%s query=%s", course_code, query[:100])
        is_relevant, _, refusal = await gatekeeper.check_and_enrich(
            query, course_code, course_ctx
        )
        logger.info("GATEKEEPER: is_relevant=%s enabled=%s refusal=%s", is_relevant, settings.GATEKEEPER_ENABLED, refusal)

        if settings.QUERY_ENHANCER_ENABLED:
            from app.query_enhancer import generate_search_queries
            search_queries = await generate_search_queries(
                query, course_ctx,
                num_queries=settings.QUERY_ENHANCER_NUM_QUERIES,
            )
        else:
            search_queries = [query]
        logger.info("SEARCH_QUERIES: %s", search_queries)

        all_chunks = []
        seen_ids = set()
        for sq in search_queries:
            sq_chunks = await self.rag_pipeline.retrieve(
                query=sq,
                course_code=course_code,
                top_k=top_k,
            )
            logger.info("RETRIEVE: query=%s got %d chunks", sq, len(sq_chunks))
            for c in sq_chunks:
                cid = c.get("chunk_id") or str(c.get("id", ""))
                if cid and cid not in seen_ids:
                    seen_ids.add(cid)
                    all_chunks.append(c)

        chunks = all_chunks[: top_k * 2]
        logger.info("CHUNKS: total unique=%d", len(chunks))
        for i, c in enumerate(chunks):
            preview = (c.get("text") or "")[:200]
            logger.info("  chunk[%d]: source=%s score=%.3f type=%s text=%s",
                        i, c.get("source_title"), round(1 - c.get("distance", 0), 3),
                        c.get("content_type"), preview)

        if not chunks:
            logger.info("NO_CHUNKS: no chunks found, LLM will answer from general knowledge")

        messages = build_tutor_prompt(
            query=query,
            course_code=course_code,
            course_name=course_ctx["course_name"],
            chunks=chunks,
            history=history or [],
            language=language,
            mastery=mastery,
            bloom_level=bloom_level,
        )

        strategy_prompt = messages + [
            {"role": "user", "content": "Briefly outline your strategy for answering this student's question based on the provided materials. Keep it to 2-3 sentences."}
        ]
        try:
            strategy_text = await client.chat(strategy_prompt, temperature=0.2, max_tokens=150, images=images)
            logger.info("STRATEGY: len=%d text=%s", len(strategy_text or ""), (strategy_text or "")[:200])
            if strategy_text:
                yield {"type": "thinking", "content": strategy_text + "\n\n"}
        except Exception as e:
            logger.error("STRATEGY failed (continuing without thinking chunk): %s", e)

        full_response = ""
        llm_chunks = 0
        try:
            async for chunk in client.stream(messages, temperature=0.3, images=images):
                if chunk["type"] == "content":
                    llm_chunks += 1
                    full_response += chunk["content"]
                    if llm_chunks <= 3 or len(full_response) < 500:
                        logger.info("LLM_STREAM: chunk#%d content=%s", llm_chunks, chunk["content"])
                yield chunk
        except Exception as e:
            logger.error("LLM_STREAM failed: %s", e)
            full_response = f"I encountered an error while processing your request: {e}"
            yield {"type": "content", "content": full_response}
        logger.info("LLM_DONE: total_chunks=%d full_response_len=%d preview=%s",
                     llm_chunks, len(full_response), full_response[:300])

        is_valid, reason = await verifier.verify_answer(query, full_response, chunks, course_code)
        logger.info("VERIFIER: is_valid=%s reason=%s", is_valid, reason)
        if not is_valid:
            yield {"type": "content", "content": f"\n\n⚠️ *Note: This answer may contain information not explicitly in your notes. Reason: {reason}*"}
        actually_cited = extract_cited_sources(full_response, chunks)
        logger.info("CITED: %d sources=%s", len(actually_cited), actually_cited)

        yield {
            "type": "metadata",
            "verified": is_valid,
            "verification_reason": reason if not is_valid else "",
            "cited_sources": actually_cited,
            "chunks_retrieved": len(chunks),
            "text_chunks": len([c for c in chunks if c.get("content_type") != "image"]),
            "image_chunks": len([c for c in chunks if c.get("content_type") == "image"]),
        }

    async def query(
        self,
        query: str,
        course_code: str,
        course_name: str,
        history: list[dict] | None = None,
        language: str = "English",
        mastery: float | None = None,
        top_k: int = 5,
        bloom_level: int | None = None,
        images: list[dict] | None = None,
    ) -> dict:
        course_ctx = await self._get_course_context(course_code)
        is_relevant, _, refusal = await gatekeeper.check_and_enrich(
            query, course_code, course_ctx
        )

        if settings.GATEKEEPER_ENABLED and not is_relevant:
            return {
                "response": refusal or "This topic is not covered in your course materials.",
                "out_of_scope": True,
                "cited_sources": [],
                "chunks_retrieved": 0,
                "text_chunks": 0,
                "image_chunks": 0,
            }

        if settings.QUERY_ENHANCER_ENABLED:
            from app.query_enhancer import generate_search_queries
            search_queries = await generate_search_queries(
                query, course_ctx,
                num_queries=settings.QUERY_ENHANCER_NUM_QUERIES,
            )
        else:
            search_queries = [query]

        all_chunks = []
        seen_ids = set()
        for sq in search_queries:
            sq_chunks = await self.rag_pipeline.retrieve(
                query=sq,
                course_code=course_code,
                top_k=top_k,
            )
            for c in sq_chunks:
                cid = c.get("chunk_id") or str(c.get("id", ""))
                if cid and cid not in seen_ids:
                    seen_ids.add(cid)
                    all_chunks.append(c)

        chunks = all_chunks[: top_k * 2]

        messages = build_tutor_prompt(
            query=query,
            course_code=course_code,
            course_name=course_ctx["course_name"],
            chunks=chunks,
            history=history or [],
            language=language,
            mastery=mastery,
            bloom_level=bloom_level,
        )

        response_text = await client.chat(messages, temperature=0.3, images=images)

        is_valid, reason = await verifier.verify_answer(query, response_text, chunks, course_code)
        if not is_valid:
            response_text += f"\n\n[Verification Note: {reason}]"

        citation_check = validate_citations(response_text, chunks)
        if not citation_check["valid"]:
            response_text = remove_uncited_claims(response_text)

        actually_cited = extract_cited_sources(response_text, chunks)

        return {
            "response": response_text,
            "cited_sources": actually_cited,
            "chunks_retrieved": len(chunks),
            "text_chunks": len([c for c in chunks if c.get("content_type") != "image"]),
            "image_chunks": len([c for c in chunks if c.get("content_type") == "image"]),
        }
