import logging
from typing import Any

from app.provider_router import router as client

logger = logging.getLogger(__name__)

ENHANCER_SCHEMA = {
    "type": "object",
    "properties": {
        "queries": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 5,
        }
    },
    "required": ["queries"],
}


async def generate_search_queries(
    query: str,
    course_context: dict[str, Any],
    num_queries: int = 3,
    model: str | None = None,
) -> list[str]:
    """
    Generate N diverse search queries from the user's question + course context.
    Returns [query] on any failure — never blocks the user.
    """
    doc_lines = []
    for d in course_context.get("documents", []):
        name = d.get("name", "?")
        preview = d.get("preview", "")
        doc_lines.append(f"- {name}: {preview}" if preview else f"- {name}")

    docs_text = "\n".join(doc_lines) if doc_lines else "No documents uploaded yet."
    curriculum = course_context.get("curriculum_topics", "") or "No curriculum uploaded."
    desc = course_context.get("course_description", "")

    system_prompt = (
        f"You are a query enhancement specialist for a RAG tutoring system.\n"
        f"Given the course context below, generate {num_queries} distinct search queries "
        f"that would retrieve the most relevant chunks from the course materials.\n\n"
        f"Each query should target a DIFFERENT aspect of the question — "
        f"core definition, application, comparison, etc.\n\n"
        f"COURSE: {course_context.get('course_name', '')}\n"
        f"DESCRIPTION: {desc}\n\n"
        f"DOCUMENTS (with content preview):\n{docs_text}\n\n"
        f"CURRICULUM TOPICS:\n{curriculum}\n\n"
        f"Return ONLY valid JSON: {{\"queries\": [\"query 1\", \"query 2\", ...]}}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"STUDENT QUESTION: {query}"},
    ]

    try:
        n = min(max(num_queries, 1), 5)
        schema = dict(ENHANCER_SCHEMA)
        schema["properties"]["queries"]["maxItems"] = n
        schema["properties"]["queries"]["minItems"] = n

        result = await client.chat_with_schema(
            messages=messages,
            response_schema=schema,
            model=model,
            max_tokens=1024,
        )
        queries = result.get("queries", [])
        if not isinstance(queries, list) or not queries:
            return [query]
        return queries[:n]
    except Exception as e:
        logger.warning("[QueryEnhancer] Error generating queries: %s", e)
        return [query]
