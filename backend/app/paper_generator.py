from typing import List
from app.provider_router import router as client

async def generate_paper(course_code: str, total_marks: int, difficulty: str, topics: List[str], chunks: List[dict]):
    context_text = "\n\n".join([f"Source: {c['source_title']} (Page {c['page']})\nContent: {c['text']}" for c in chunks])
    
    prompt = f"""
    You are an expert academic examiner. Generate a structured question paper for the course {course_code}.
    
    Total Marks: {total_marks}
    Difficulty Level: {difficulty}
    Topics to cover: {", ".join(topics)}
    
    Use the following provided course material as the primary source for questions:
    {context_text}
    
    Distribution Guidelines:
    - Use Bloom's Taxonomy (Knowledge, Understanding, Application, Analysis).
    - Include Multiple Choice Questions (MCQs), Short Answer Questions, and Long Answer Questions.
    - Ensure marks add up to approximately {total_marks}.
    
    Return the paper as a JSON object with this structure:
    {{
      "course_code": "{course_code}",
      "total_marks": {total_marks},
      "difficulty": "{difficulty}",
      "sections": {{
        "mcq": [
          {{ "question": "...", "options": ["A", "B", "C", "D"], "answer": "...", "marks": 1, "taxonomy": "Knowledge" }}
        ],
        "short_answer": [
          {{ "question": "...", "marks": 5, "taxonomy": "Understanding" }}
        ],
        "long_answer": [
          {{ "question": "...", "marks": 10, "taxonomy": "Application" }}
        ]
      }}
    }}
    """

    messages = [
        {"role": "system", "content": "You are a helpful assistant that generates academic question papers in JSON format."},
        {"role": "user", "content": prompt}
    ]

    response_schema = {
        "type": "object",
        "properties": {
            "course_code": {"type": "string"},
            "total_marks": {"type": "integer"},
            "difficulty": {"type": "string"},
            "sections": {
                "type": "object",
                "properties": {
                    "mcq": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question": {"type": "string"},
                                "options": {"type": "array", "items": {"type": "string"}},
                                "answer": {"type": "string"},
                                "marks": {"type": "integer"},
                                "taxonomy": {"type": "string"}
                            },
                            "required": ["question", "options", "answer", "marks", "taxonomy"]
                        }
                    },
                    "short_answer": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question": {"type": "string"},
                                "marks": {"type": "integer"},
                                "taxonomy": {"type": "string"}
                            },
                            "required": ["question", "marks", "taxonomy"]
                        }
                    },
                    "long_answer": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question": {"type": "string"},
                                "marks": {"type": "integer"},
                                "taxonomy": {"type": "string"}
                            },
                            "required": ["question", "marks", "taxonomy"]
                        }
                    }
                },
                "required": ["mcq", "short_answer", "long_answer"]
            }
        },
        "required": ["course_code", "total_marks", "difficulty", "sections"]
    }

    result = await client.chat_with_schema(messages, response_schema)
    return result
