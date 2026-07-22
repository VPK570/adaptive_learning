from typing import Optional, Tuple, Any

from app.provider_router import router as client
import logging

logger = logging.getLogger(__name__)


class Gatekeeper:
    def __init__(self, model: str | None = None):
        self.model = model

    async def check_and_enrich(
        self,
        query: str,
        course_code: str,
        context: dict[str, Any],
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Returns: (is_relevant, enriched_query, refusal_message)
        context dict contains: course_name, course_description, documents,
                               curriculum_topics, topic_coverage
        """
        doc_lines = []
        for d in context.get("documents", []):
            name = d.get("name", "?")
            preview = d.get("preview", "")
            doc_lines.append(f"- {name}: {preview}" if preview else f"- {name}")

        docs_text = "\n".join(doc_lines) if doc_lines else "No documents uploaded yet."
        curriculum = context.get("curriculum_topics", "") or "No curriculum uploaded."
        desc = context.get("course_description", "")

        system_prompt = (
            f"You are a Gatekeeper for an AI Tutor specializing in the course: {course_code}.\n"
            f"Your job is to determine if the student's query is relevant to "
            f"the course materials described below.\n\n"
            f"COURSE DESCRIPTION: {desc}\n\n"
            f"AVAILABLE DOCUMENTS (with content preview):\n{docs_text}\n\n"
            f"CURRICULUM TOPICS:\n{curriculum}\n\n"
            f"If relevant, rewrite the query slightly to make it more descriptive "
            f"for a vector search engine.\n"
            f"If irrelevant, provide a polite refusal.\n\n"
            f"OUTPUT FORMAT (JSON ONLY):\n"
            f"{{\n"
            f'  "relevant": boolean,\n'
            f'  "enriched_query": "rewritten query if relevant, else null",\n'
            f'  "refusal_message": "polite explanation if irrelevant, else null"\n'
            f"}}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"STUDENT QUERY: {query}"},
        ]

        try:
            response = await client.chat_with_schema(
                messages=messages,
                model=self.model,
                response_schema={
                    "type": "object",
                    "properties": {
                        "relevant": {"type": "boolean"},
                        "enriched_query": {"type": ["string", "null"]},
                        "refusal_message": {"type": ["string", "null"]},
                    },
                    "required": ["relevant", "enriched_query", "refusal_message"],
                },
            )

            return (
                response.get("relevant", False),
                response.get("enriched_query") or query,
                response.get("refusal_message"),
            )
        except Exception as e:
            logger.error("[Gatekeeper] Error: %s", e)
            return True, query, None


gatekeeper = Gatekeeper()
