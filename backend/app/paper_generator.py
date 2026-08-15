from typing import List

from app.knowledge_state import BLOOM_LABELS
from app.provider_router import router as client


async def generate_paper(course_code: str, total_marks: int, difficulty: str, topics: List[str], chunks: List[dict], bloom_levels: list[int] | None = None):
    context_text = "\n\n".join([f"Source: {c['source_title']} (Page {c['page']})\nContent: {c['text']}" for c in chunks])

    bloom_instruction = ""
    if bloom_levels:
        labels = [BLOOM_LABELS.get(bl, f"Level {bl}") for bl in bloom_levels]
        bloom_instruction = f"\n    Distribute questions across these Bloom's Taxonomy levels: {', '.join(labels)}."

    prompt = f"""
    You are an expert academic examiner. Generate a structured question paper for the course {course_code}.
    
    Total Marks: {total_marks}
    Difficulty Level: {difficulty}
    Topics to cover: {", ".join(topics)}
    
    Use the following provided course material as the primary source for questions:
    {context_text}
    
    Distribution Guidelines:
    - Use Bloom's Taxonomy (Remember, Understand, Apply, Analyze, Evaluate, Create).
    - Include Multiple Choice Questions (MCQs), Short Answer Questions, and Long Answer Questions.
    - Ensure marks add up to approximately {total_marks}.{bloom_instruction}
    
    Return JSON: {{"course_code":"...","total_marks":N,"difficulty":"...","sections":{{"mcq":[{{"question":"...","options":["A","B","C","D"],"answer":"...","marks":1,"taxonomy":"Remember"}}],"short_answer":[{{"question":"...","marks":5,"taxonomy":"Understand"}}],"long_answer":[{{"question":"...","marks":10,"taxonomy":"Apply"}}]}}}}
    """

    messages = [
        {"role": "system", "content": "You are a helpful assistant that generates academic question papers in JSON format."},
        {"role": "user", "content": prompt}
    ]

    schema = {
        "type": "object",
        "properties": {
            "course_code": {"type": "string"},
            "total_marks": {"type": "integer"},
            "difficulty": {"type": "string"},
            "sections": {
                "type": "object",
                "properties": {
                    "mcq": {"type": "array", "items": {"type": "object", "properties": {"question": {"type": "string"}, "options": {"type": "array", "items": {"type": "string"}}, "answer": {"type": "string"}, "marks": {"type": "integer"}, "taxonomy": {"type": "string"}}, "required": ["question", "options", "answer", "marks", "taxonomy"]}},
                    "short_answer": {"type": "array", "items": {"type": "object", "properties": {"question": {"type": "string"}, "marks": {"type": "integer"}, "taxonomy": {"type": "string"}}, "required": ["question", "marks", "taxonomy"]}},
                    "long_answer": {"type": "array", "items": {"type": "object", "properties": {"question": {"type": "string"}, "marks": {"type": "integer"}, "taxonomy": {"type": "string"}}, "required": ["question", "marks", "taxonomy"]}},
                },
                "required": ["mcq", "short_answer", "long_answer"]
            }
        },
        "required": ["course_code", "total_marks", "difficulty", "sections"]
    }

    return await client.chat_with_schema(messages, schema)
