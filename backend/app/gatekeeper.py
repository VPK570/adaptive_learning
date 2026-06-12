from typing import Optional, Tuple
from app.openrouter import client

class Gatekeeper:
    def __init__(self, model: str | None = None):
        self.model = model

    async def check_and_enrich(
        self, 
        query: str, 
        course_code: str, 
        doc_titles: list[str], 
        curriculum_content: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Returns: (is_relevant, enriched_query, refusal_message)
        """
        system_prompt = f"""You are a Gatekeeper for an AI Tutor specializing in the course: {course_code}.
Your job is to:
1. Determine if the student's query is relevant to the course materials.
2. If relevant, rewrite the query to be more descriptive for a vector search engine (Query Enrichment).
3. If irrelevant, provide a polite explanation of why it's out of scope.

AVAILABLE MATERIALS:
- Documents: {', '.join(doc_titles) if doc_titles else 'No documents uploaded yet.'}
- Curriculum Summary: {curriculum_content[:2000] if curriculum_content else 'No curriculum uploaded.'}

OUTPUT FORMAT (JSON ONLY):
{{
  "relevant": boolean,
  "enriched_query": "The rewritten query if relevant, else null",
  "refusal_message": "Polite explanation if irrelevant, else null"
}}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"STUDENT QUERY: {query}"}
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
                        "refusal_message": {"type": ["string", "null"]}
                    },
                    "required": ["relevant", "enriched_query", "refusal_message"]
                }
            )
            
            return (
                response.get("relevant", False),
                response.get("enriched_query") or query,
                response.get("refusal_message")
            )
        except Exception as e:
            print(f"[Gatekeeper] Error: {e}")
            # Fallback to true to avoid blocking the user if the small model fails
            return True, query, None

gatekeeper = Gatekeeper()
