import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

"""FastAPI server for the RAG pipeline — publishable REST API.

Routes:
- GET  /health          — health check
- POST /ingest          — ingest PDF (multipart upload)
- POST /query           — query the RAG system
- GET  /stats           — course stats
- GET  /chunks          — raw retrieved chunks
"""

import os
import uuid
import json
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Query, UploadFile, Form, Request
from typing import Annotated, List
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.rag import RAGPipeline
from app.query_engine import QueryEngine
from app.curriculum import CurriculumManager
from app.openrouter import client
from app.analytics import log_query, get_analytics, get_all_questions, get_unanswered_questions, get_coverage
from app.chat_history import get_course_history, add_message, clear_course_history
from app.paper_generator import generate_paper
from app.courses import get_all_courses_data, create_course, update_course, delete_course
from app.saved_content import SavedContentManager

# ─── Lifespan ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up RAG pipeline API...")
    yield
    print("Shutting down...")


app = FastAPI(title="Adaptive Learning RAG API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag = RAGPipeline()
engine = QueryEngine()
curriculum = CurriculumManager()
saved_content = SavedContentManager()

# ─── Models ───────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    course_code: str = "BAECE102"
    session_id: str = "default"
    top_k: int = 5
    language: str = "English"
    mastery: float | None = None


class QueryResponse(BaseModel):
    response: str
    cited_sources: list
    chunks_retrieved: int
    text_chunks: int
    image_chunks: int


class ChunkItem(BaseModel):
    chunk_id: str
    text: str
    source_title: str
    page: int
    content_type: str
    score: float


class PaperRequest(BaseModel):
    course_code: str
    total_marks: int = 100
    difficulty: str = "Medium"
    topics: List[str] = []
    top_k: int = 10


class CourseCreate(BaseModel):
    course_code: str
    course_name: str
    description: str
    icon: str = "📚"


class CourseUpdate(BaseModel):
    course_name: str | None = None
    description: str | None = None
    icon: str | None = None


class FlashcardRequest(BaseModel):
    course_code: str
    topic: str
    count: int = 5

class SaveFlashcardRequest(BaseModel):
    course_code: str
    topic: str
    cards: List[dict]

class QuizRequest(BaseModel):
    course_code: str
    topic: str
    count: int = 5

class SaveQuizRequest(BaseModel):
    course_code: str
    topic: str
    questions: List[dict]
    score: int



# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/stats")
async def get_stats(course_code: str = "BAECE102"):
    stats = rag.get_course_stats(course_code)
    return stats


@app.get("/curriculum/topics")
async def get_course_topics(course: str = Query(...)):
    return curriculum.get_curriculum_topics(course)


@app.get("/curriculum")
async def list_curriculum_files(course: str = Query(...)):
    return curriculum.list_curriculum(course)


@app.post("/curriculum")
async def upload_curriculum(
    file: Annotated[UploadFile, Form(...)],
    course_code: Annotated[str, Form(...)],
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    temp_path = f"/tmp/curriculum_{uuid.uuid4().hex}.pdf"
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        title = Path(file.filename).stem.replace("-", " ").replace("_", " ")

        result = await curriculum.ingest_curriculum(
            course_code=course_code,
            document_title=title,
            filepath=temp_path,
        )
        return result
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.get("/analytics")
async def analytics(course_code: str = "BAECE102"):
    return get_analytics(course_code)


@app.get("/analytics/unanswered")
async def unanswered(course_code: str = "BAECE102"):
    return get_unanswered_questions(course_code)


@app.get("/analytics/coverage")
async def coverage(course_code: str = "BAECE102"):
    return get_coverage(course_code)


@app.get("/chat-history")
async def get_history(course_code: str, session_id: str):
    return get_course_history(course_code, session_id)


@app.post("/chat-history")
async def save_chat_message(course_code: str, session_id: str, role: str, content: str):
    add_message(course_code, session_id, role, content)
    return {"status": "success"}


@app.delete("/chat-history")
async def clear_history(course_code: str, session_id: str):
    clear_course_history(course_code, session_id)
    return {"status": "success"}


@app.get("/questions")
async def questions(course_code: str = "BAECE102"):
    return get_all_questions(course_code)


@app.get("/courses")
async def list_courses():
    courses = get_all_courses_data()
    # Merge stats from ChromaDB
    for course in courses:
        stats = rag.get_course_stats(course["course_code"])
        course["doc_count"] = len(stats.get("documents", []))
        course["chunk_count"] = stats.get("total_chunks", 0)
    return courses


@app.post("/courses")
async def create_new_course(body: CourseCreate):
    try:
        new_course = create_course(body.course_code, body.course_name, body.description, body.icon)
        return new_course
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/generate-paper")
async def create_paper(body: PaperRequest):
    # Retrieve chunks related to the topics or just general course chunks
    query_str = " ".join(body.topics) if body.topics else "overview of the course"
    chunks = await rag.retrieve(
        query=query_str,
        course_code=body.course_code,
        top_k=body.top_k
    )
    
    if not chunks:
        raise HTTPException(404, "No course content found to generate a paper from.")
        
    paper = await generate_paper(
        course_code=body.course_code,
        total_marks=body.total_marks,
        difficulty=body.difficulty,
        topics=body.topics,
        chunks=chunks
    )
    return paper


@app.post("/ingest")
async def ingest_pdf(
    file: Annotated[UploadFile, Form(description="PDF file to ingest")],
    course_code: Annotated[str, Form()] = "BAECE102",
    topic: Annotated[str, Form()] = "",
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    temp_path = f"/tmp/ingest_{uuid.uuid4().hex}.pdf"
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        title = Path(file.filename).stem.replace("-", " ").replace("_", " ")

        result = await rag.ingest_pdf(
            course_code=course_code,
            document_title=title,
            filepath=temp_path,
            topic=topic,
        )
        return result
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/query", response_model=QueryResponse)
async def query(body: QueryRequest):
    chunks = await rag.retrieve(
        query=body.question,
        course_code=body.course_code,
        top_k=body.top_k,
    )

    if not chunks:
        raise HTTPException(404, "No chunks found. Ingest documents first.")

    result = await engine.query(
        query=body.question,
        course_code=body.course_code,
        course_name=body.course_code,
        chunks=chunks,
        language=body.language,
        mastery=body.mastery,
    )

    # Log the query for analytics
    log_query(body.question, body.course_code, result["response"], result["cited_sources"])
    
    # Save to chat history
    add_message(body.course_code, body.session_id, "user", body.question)
    add_message(body.course_code, body.session_id, "assistant", result["response"])

    return QueryResponse(
        response=result["response"],
        cited_sources=result["cited_sources"],
        chunks_retrieved=result["chunks_retrieved"],
        text_chunks=result["text_chunks"],
        image_chunks=result["image_chunks"],
    )


@app.put("/courses/{course_code}")
async def edit_course(course_code: str, body: CourseUpdate):
    try:
        updated = update_course(course_code, body.course_name, body.description, body.icon)
        return updated
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.delete("/courses/{course_code}")
async def remove_course(course_code: str):
    try:
        delete_course(course_code)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(404, str(e))


def safe_json_parse(response_str: str):
    if not response_str:
        return None
    try:
        json_str = response_str.strip()
        if json_str.startswith("```json"):
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif json_str.startswith("```"):
            json_str = json_str.split("```")[1].split("```")[0].strip()
        return json.loads(json_str)
    except Exception as e:
        print(f"Error parsing JSON: {e}\nResponse: {response_str}")
        return None

@app.post("/flashcards")
async def generate_flashcards(body: FlashcardRequest):
    chunks = await rag.retrieve(query=body.topic, course_code=body.course_code, top_k=10)
    if not chunks:
        raise HTTPException(404, "No materials found to generate flashcards.")
    
    context = "\n".join([c["text"] for c in chunks if c.get("text")])
    prompt = f"""Based on the following course materials, generate {body.count} flashcards for the topic: {body.topic}.
Return ONLY a JSON array of objects, each with 'question' and 'answer' fields.
Ensure the JSON is complete and valid. Do not truncate the output.

MATERIALS:
{context}
"""
    response = await client.chat([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=2048)
    
    result = safe_json_parse(response)
    if result is None:
        raise HTTPException(500, "Failed to generate valid JSON for flashcards.")
    return result

@app.post("/flashcards/save")
async def save_flashcards(body: SaveFlashcardRequest):
    return saved_content.save_flashcards(body.course_code, body.topic, body.cards)

@app.get("/flashcards/saved")
async def get_saved_flashcards(course: str = Query(...)):
    return saved_content.get_saved_flashcards(course)

@app.delete("/flashcards/saved/{set_id}")
async def delete_saved_flashcards(set_id: str):
    if not saved_content.delete_flashcards(set_id):
        raise HTTPException(404, "Flashcard set not found.")
    return {"status": "success"}

@app.post("/quiz")
async def generate_quiz(body: QuizRequest):
    if not body.topic or not body.topic.strip():
        raise HTTPException(400, "Quiz topic cannot be empty.")

    chunks = await rag.retrieve(query=body.topic, course_code=body.course_code, top_k=10)
    if not chunks:
        raise HTTPException(404, "No materials found to generate a quiz.")
    
    context = "\n".join([c["text"] for c in chunks if c.get("text")])
    prompt = f"""Based on the following course materials, generate {body.count} multiple-choice quiz questions for the topic: {body.topic}.
Return ONLY a JSON array of objects, each with:
- 'question': the question text
- 'options': an array of 4 string options
- 'correct_index': the 0-based index of the correct option
- 'explanation': a brief explanation of why that's correct
- 'user_answer_index': -1 (placeholder)
- 'is_correct': false (placeholder)

Ensure the JSON is complete and valid. Do not truncate the output.

MATERIALS:
{context}
"""
    response = await client.chat([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=2048)
    
    result = safe_json_parse(response)
    if result is None:
        raise HTTPException(500, "Failed to generate valid JSON for quiz.")
    return result

@app.post("/quiz/save")
async def save_quiz(body: SaveQuizRequest):
    return saved_content.save_quiz(body.course_code, body.topic, body.questions, body.score)

@app.get("/quiz/saved")
async def get_saved_quizzes(course: str = Query(...)):
    return saved_content.get_saved_quizzes(course)

@app.delete("/quiz/saved/{quiz_id}")
async def delete_saved_quiz(quiz_id: str):
    if not saved_content.delete_quiz(quiz_id):
        raise HTTPException(404, "Quiz not found.")
    return {"status": "success"}


@app.get("/chunks")
async def get_chunks(
    course_code: str = "BAECE102",
    query: str = "",
    top_k: int = 5,
):
    chunks = await rag.retrieve(query=query, course_code=course_code, top_k=top_k)
    return [
        ChunkItem(
            chunk_id=c["chunk_id"],
            text=c["text"],
            source_title=c["source_title"],
            page=c["page"],
            content_type=c["content_type"],
            score=round(1 - c["distance"], 3),
        )
        for c in chunks
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)