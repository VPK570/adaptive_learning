from typing import Any, Tuple
from app.openrouter import client

class Verifier:
    def __init__(self, model: str = "google/gemma-2-9b-it:free"):
        self.model = model

    async def verify_answer(
        self,
        query: str,
        answer: str,
        chunks: list[dict],
        course_code: str
    ) -> Tuple[bool, str]:
        """
        Verifies if the answer is grounded in the provided chunks.
        Returns: (is_valid, corrected_answer_or_reason)
        """
        context_text = "\n\n".join([
            f"[Source: {c.get('source_title')}, Page {c.get('page')}]\n{c.get('text')}"
            for c in chunks
        ])

        system_prompt = f"""You are a Verification Agent for an AI Tutor.
Your task is to check if the generated answer is accurately grounded in the provided course materials.

COURSE: {course_code}
STUDENT QUERY: {query}
GENERATED ANSWER: {answer}

COURSE MATERIALS:
{context_text[:4000]}

RULES:
1. If the answer contains information NOT in the materials, mark as invalid.
2. If the answer is accurate but misses citations that ARE in the materials, mark as invalid.
3. If invalid, provide a brief reason.

OUTPUT FORMAT (JSON ONLY):
{{
  "valid": boolean,
  "reason": "Brief reason if invalid, else null"
}}
"""

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        try:
            response = await client.chat_with_schema(
                messages=messages,
                model=self.model,
                response_schema={
                    "type": "object",
                    "properties": {
                        "valid": {"type": "boolean"},
                        "reason": {"type": ["string", "null"]}
                    },
                    "required": ["valid", "reason"]
                }
            )
            
            return response.get("valid", True), response.get("reason")
        except Exception as e:
            print(f"[Verifier] Error: {e}")
            return True, None

verifier = Verifier()
