"""Query engine — builds prompts, calls LLM, enforces citations.

Handles both text and image chunks in the context window.
"""

import re

from app.openrouter import client
from app.citation import validate_citations, remove_uncited_claims, extract_all_citations
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
            mastery_section = "Student has strong mastery. Use deeper Socratic questions that require synthesis and evaluation."
        elif mastery >= 0.50:
            mastery_section = "Student has moderate mastery. Use scaffolded Socratic questions with examples."
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
- Every factual claim MUST include an inline citation: [Source: title, Slide N]
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
        5. Return response + metadata
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

        citations = extract_all_citations(response_text)
        
        # Determine which chunks were actually cited
        actually_cited = []
        seen_titles = set()
        for cit in citations:
            cit_lower = cit.lower()
            for c in chunks:
                title = c.get("source_title", "").lower()
                if title and title in cit_lower:
                    if title not in seen_titles:
                        actually_cited.append({
                            "source_title": c.get("source_title", ""),
                            "page": c.get("page", ""),
                            "content_type": c.get("content_type", "text"),
                            "has_image": c.get("has_image", False),
                        })
                        seen_titles.add(title)

        citation_check = validate_citations(response_text, chunks)
        if not citation_check["valid"]:
            response_text = remove_uncited_claims(response_text)
            citation_check["valid"] = True
            citation_check["note"] = "Some uncited claims were removed"

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