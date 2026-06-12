"""Query engine — builds prompts, calls LLM, enforces citations.

Handles both text and image chunks in the context window.
"""

from typing import AsyncGenerator, Dict, Any

from app.openrouter import client
from app.citation import validate_citations, remove_uncited_claims, extract_all_citations, parse_citation
from app.gatekeeper import gatekeeper
from app.verifier import verifier
from app.rag import RAGPipeline


def build_tutor_system_prompt(
    course_name: str,
    course_code: str,
    language: str = "English",
    mastery: float | None = None,
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

    return f"""You are an expert {course_name} tutor for VIT students.
Student is enrolled in {course_code} at VIT Vellore.
Preferred language: {language}.

{mastery_section}

RULES:
- Answer ONLY from provided course materials. 
- If the answer cannot be found in the provided context chunks, respond with:
  "This topic is not covered in your course materials."
- Never answer from general knowledge.
- Every factual claim MUST include an inline citation.
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
    max_turns: int = 8,
) -> str:
    parts = ["COURSE MATERIALS:"]

    text_chunks = [c for c in chunks if c.get("content_type", "text") != "image"]
    image_chunks = [c for c in chunks if c.get("content_type") == "image" or c.get("has_image")]
    
    available_citations = []

    for i, c in enumerate(text_chunks, 1):
        title = c.get("source_title", "Unknown")
        page = c.get("page", "?")
        text = c.get("text", "")

        parts.append(f"<Text {i}: {title}, Slide {page}>\n{text}\n</Text {i}>")
        available_citations.append(f"[Source: {title}, Slide {page}]")

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
) -> list[dict[str, str]]:
    system = build_tutor_system_prompt(course_name, course_code, language, mastery)
    context = build_context_window(chunks, history or [])

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"{context}\n\nSTUDENT: {query}"},
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

    async def _get_gatekeeper_context(self, course_code: str) -> tuple[list[str], str]:
        stats = await self.rag_pipeline.get_course_stats(course_code)
        doc_titles = [d["name"] for d in stats.get("documents", [])]
        
        from app.db import get_db
        db = await get_db()
        curr_res = await db.query(
            "SELECT text FROM curriculum_chunk WHERE course_code = $code",
            {"code": course_code}
        )
        curriculum_text = "\n".join([r["text"] for r in (curr_res if curr_res else [])])
        
        return doc_titles, curriculum_text

    async def query_stream(
        self,
        query: str,
        course_code: str,
        course_name: str,
        history: list[dict] | None = None,
        language: str = "English",
        mastery: float | None = None,
        top_k: int = 5,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        doc_titles, curriculum_text = await self._get_gatekeeper_context(course_code)
        is_relevant, enriched_query, refusal = await gatekeeper.check_and_enrich(
            query, course_code, doc_titles, curriculum_text
        )

        if not is_relevant:
            yield {"type": "content", "content": refusal or "This topic is not covered in your course materials."}
            yield {"type": "metadata", "out_of_scope": True, "cited_sources": []}
            return

        chunks = await self.rag_pipeline.retrieve(
            query=enriched_query,
            course_code=course_code,
            top_k=top_k,
        )

        if not chunks:
            yield {"type": "content", "content": "I couldn't find specific information in the course materials, but I can try to help based on the curriculum."}
            
        messages = build_tutor_prompt(
            query=query,
            course_code=course_code,
            course_name=course_name,
            chunks=chunks,
            history=history or [],
            language=language,
            mastery=mastery,
        )

        strategy_prompt = messages + [
            {"role": "user", "content": "Briefly outline your strategy for answering this student's question based on the provided materials. Keep it to 2-3 sentences."}
        ]
        strategy_text = await client.chat(strategy_prompt, temperature=0.2, max_tokens=150)
        if strategy_text:
            yield {"type": "thinking", "content": strategy_text + "\n\n"}

        full_response = ""
        async for chunk in client.stream(messages, temperature=0.3, max_tokens=1024):
            if chunk["type"] == "content":
                full_response += chunk["content"]
            yield chunk

        is_valid, reason = await verifier.verify_answer(query, full_response, chunks, course_code)
        if not is_valid:
            yield {"type": "content", "content": f"\n\n⚠️ *Note: This answer may contain information not explicitly in your notes. Reason: {reason}*"}

        citations = extract_all_citations(full_response)
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
                        "page": c.get("page", ""),
                        "content_type": c.get("content_type", "text"),
                        "has_image": c.get("has_image", False),
                    })
                    seen_keys.add(key)

        yield {
            "type": "metadata",
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
    ) -> dict:
        doc_titles, curriculum_text = await self._get_gatekeeper_context(course_code)
        is_relevant, enriched_query, refusal = await gatekeeper.check_and_enrich(
            query, course_code, doc_titles, curriculum_text
        )

        if not is_relevant:
            return {
                "response": refusal or "This topic is not covered in your course materials.",
                "out_of_scope": True,
                "cited_sources": [],
                "chunks_retrieved": 0,
            }

        chunks = await self.rag_pipeline.retrieve(
            query=enriched_query,
            course_code=course_code,
            top_k=top_k,
        )

        messages = build_tutor_prompt(
            query=query,
            course_code=course_code,
            course_name=course_name,
            chunks=chunks,
            history=history or [],
            language=language,
            mastery=mastery,
        )

        response_text = await client.chat(messages, temperature=0.3, max_tokens=1024)
        
        is_valid, reason = await verifier.verify_answer(query, response_text, chunks, course_code)
        if not is_valid:
            response_text += f"\n\n[Verification Note: {reason}]"

        citation_check = validate_citations(response_text, chunks)
        if not citation_check["valid"]:
            response_text = remove_uncited_claims(response_text)

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
                        "page": c.get("page", ""),
                    })
                    seen_keys.add(key)

        return {
            "response": response_text,
            "cited_sources": actually_cited,
            "chunks_retrieved": len(chunks),
            "text_chunks": len([c for c in chunks if c.get("content_type") != "image"]),
            "image_chunks": len([c for c in chunks if c.get("content_type") == "image"]),
        }
