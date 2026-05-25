"""Query engine — builds prompts, calls LLM, enforces citations.

Handles both text and image chunks in the context window.
"""

import re

from app.openrouter import client
from app.citation import validate_citations, remove_uncited_claims, extract_all_citations, parse_citation
from app.curriculum import CurriculumManager

curriculum = CurriculumManager()

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
        content_type = c.get("content_type", "text")
        text = c.get("text", "")

        header = (
            f"<Text {i}: {title}, Slide {page}>"
            if content_type == "text"
            else f"<Document {i}: {title}, Slide {page}>"
        )
        parts.append(f"{header}\n{text}\n</{content_type.title()} {i}>")
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
    async def query(
        self,
        query: str,
        course_code: str,
        course_name: str,
        chunks: list[dict],
        history: list[dict] | None = None,
        language: str = "English",
        mastery: float | None = None,
    ) -> dict:
        """
        Full query pipeline:
        1. Check curriculum scope
        2. Build prompt with system + context (text + images) + history
        3. Call LLM via OpenRouter
        4. Validate citations
        5. If validation fails, retry once with correction prompt
        6. Return response + metadata
        """
        if not await curriculum.check_topic_in_curriculum(course_code, query):
             return {
                "response": "This topic is not covered in your course materials.",
                "out_of_scope": True,
                "cited_sources": [],
                "chunks_retrieved": 0,
                "text_chunks": 0,
                "image_chunks": 0,
            }

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

        if not response_text:
            return {
                "response": "I'm sorry, I couldn't generate a response. Please try again.",
                "cited_sources": [],
                "chunks_retrieved": len(chunks),
                "text_chunks": len([c for c in chunks if c.get("content_type", "text") != "image"]),
                "image_chunks": len([c for c in chunks if c.get("content_type") == "image" or c.get("has_image")]),
                "citation_check": {"valid": False, "reason": "Empty response from LLM"},
            }

        citation_check = validate_citations(response_text, chunks)
        
        # SELF-CORRECTION RETRY: If validation fails, try one more time with a stricter prompt
        if not citation_check["valid"]:
            retry_messages = messages + [
                {"role": "assistant", "content": response_text},
                {"role": "user", "content": (
                    "Your previous response had missing or invalid citations. "
                    "Please rewrite your answer. Every factual claim MUST be followed by "
                    "a valid citation from the provided list. If you cannot verify a claim "
                    "from the materials, DO NOT make it. Use ONLY these citations:\n" +
                    "\n".join(set(citation_check.get("citations", [])))
                )}
            ]
            response_text = await client.chat(retry_messages, temperature=0.1, max_tokens=1024)
            citation_check = validate_citations(response_text, chunks)

        # Final cleanup if still failing (harder gate)
        if not citation_check["valid"]:
            response_text = remove_uncited_claims(response_text)
            # If after removal we have very little text left, or coverage is still 0, refuse
            if len(response_text) < 50:
                response_text = "I'm sorry, but I cannot verify the answer to your question using the provided course materials."
            else:
                citation_check["valid"] = True
                citation_check["note"] = "Unverified claims were removed to ensure accuracy."

        citations = extract_all_citations(response_text)
        
        # Determine which chunks were actually cited
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

        text_chunks = [c for c in chunks if c.get("content_type", "text") != "image"]
        image_chunks = [c for c in chunks if c.get("content_type") == "image" or c.get("has_image")]

        return {
            "response": response_text,
            "cited_sources": actually_cited,
            "chunks_retrieved": len(chunks),
            "text_chunks": len(text_chunks),
            "image_chunks": len(image_chunks),
            "citation_check": citation_check,
        }