import os
import uuid
import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, List

from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException, Query, UploadFile, Form, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add current directory to path for app imports
sys.path.insert(0, str(Path(__file__).parent))

from app.rag import RAGPipeline
from app.query_engine import QueryEngine
from app.curriculum import CurriculumManager
from app.openrouter import client
from app.analytics import log_query, get_analytics, get_all_questions, get_unanswered_questions, get_coverage
from app.chat_history import get_course_history, add_message, clear_course_history
from app.paper_generator import generate_paper
from app.courses import get_all_courses_data, create_course, update_course, delete_course
from app.saved_content import SavedContentManager
from app.validation import (
    validate_course_code, 
    sanitize_id, 
    sanitize_text, 
    MAX_COURSE_CODE_LENGTH,
    MAX_SESSION_ID_LENGTH,
    MAX_TOPIC_LENGTH,
    MAX_QUESTION_LENGTH,
    MAX_COURSE_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_LANGUAGE_LENGTH,
    MAX_FILE_SIZE
)

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

@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    if request.method in ["POST", "PUT"]:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_FILE_SIZE:
            return Response(content="File size exceeds limit", status_code=413)
    return await call_next(request)

rag = RAGPipeline()
engine = QueryEngine()
curriculum = CurriculumManager()
saved_content = SavedContentManager()

# ─── Models ───────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., max_length=MAX_QUESTION_LENGTH)
    course_code: str = Field("BAECE102", max_length=MAX_COURSE_CODE_LENGTH)
    session_id: str = Field("default", max_length=MAX_SESSION_ID_LENGTH)
    top_k: int = Field(5, ge=1, le=20)
    language: str = Field("English", max_length=MAX_LANGUAGE_LENGTH)
    mastery: float | None = Field(None, ge=0.0, le=1.0)


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
    course_code: str = Field(..., max_length=MAX_COURSE_CODE_LENGTH)
    total_marks: int = Field(100, ge=1, le=500)
    difficulty: str = Field("Medium", max_length=20)
    topics: List[str] = []
    top_k: int = Field(10, ge=1, le=50)


class CourseCreate(BaseModel):
    course_code: str = Field(..., max_length=MAX_COURSE_CODE_LENGTH)
    course_name: str = Field(..., max_length=MAX_COURSE_NAME_LENGTH)
    description: str = Field(..., max_length=MAX_DESCRIPTION_LENGTH)
    icon: str = Field("📚", max_length=10)


class CourseUpdate(BaseModel):
    course_name: str | None = Field(None, max_length=MAX_COURSE_NAME_LENGTH)
    description: str | None = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    icon: str | None = Field(None, max_length=10)


class FlashcardRequest(BaseModel):
    course_code: str = Field(..., max_length=MAX_COURSE_CODE_LENGTH)
    topic: str = Field(..., max_length=MAX_TOPIC_LENGTH)
    count: int = Field(5, ge=1, le=20)

class SaveFlashcardRequest(BaseModel):
    course_code: str = Field(..., max_length=MAX_COURSE_CODE_LENGTH)
    topic: str = Field(..., max_length=MAX_TOPIC_LENGTH)
    cards: List[dict]

class QuizRequest(BaseModel):
    course_code: str = Field(..., max_length=MAX_COURSE_CODE_LENGTH)
    topic: str = Field(..., max_length=MAX_TOPIC_LENGTH)
    count: int = Field(5, ge=1, le=20)

class SaveQuizRequest(BaseModel):
    course_code: str = Field(..., max_length=MAX_COURSE_CODE_LENGTH)
    topic: str = Field(..., max_length=MAX_TOPIC_LENGTH)
    questions: List[dict]
    score: int = Field(..., ge=0)



# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/stats")
async def get_stats(course_code: str = "BAECE102"):
    course_code = validate_course_code(course_code)
    stats = rag.get_course_stats(course_code)
    return stats


@app.get("/curriculum/topics")
async def get_course_topics(course: str = Query(...)):
    course = validate_course_code(course)
    return curriculum.get_curriculum_topics(course)


@app.get("/curriculum")
async def list_curriculum_files(course: str = Query(...)):
    course = validate_course_code(course)
    return curriculum.list_curriculum(course)


@app.post("/curriculum")
async def upload_curriculum(
    file: Annotated[UploadFile, Form(...)],
    course_code: Annotated[str, Form(...)],
):
    course_code = validate_course_code(course_code)
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    temp_path = f"/tmp/curriculum_{uuid.uuid4().hex}.pdf"
    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(413, "File size exceeds limit (15MB)")

        with open(temp_path, "wb") as f:
            f.write(content)

        title = Path(file.filename).stem.replace("-", " ").replace("_", " ")
        title = sanitize_text(title, MAX_COURSE_NAME_LENGTH)

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
    course_code = validate_course_code(course_code)
    return get_analytics(course_code)


@app.get("/analytics/unanswered")
async def unanswered(course_code: str = "BAECE102"):
    course_code = validate_course_code(course_code)
    return get_unanswered_questions(course_code)


@app.get("/analytics/coverage")
async def coverage(course_code: str = "BAECE102"):
    course_code = validate_course_code(course_code)
    return get_coverage(course_code)


@app.get("/chat-history")
async def get_history(course_code: str, session_id: str):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    return get_course_history(course_code, session_id)


@app.post("/chat-history")
async def save_chat_message(course_code: str, session_id: str, role: str, content: str):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    role = sanitize_text(role, 20)
    content = sanitize_text(content, MAX_QUESTION_LENGTH * 2) # Allow more for response
    add_message(course_code, session_id, role, content)
    return {"status": "success"}


@app.delete("/chat-history")
async def clear_history(course_code: str, session_id: str):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    clear_course_history(course_code, session_id)
    return {"status": "success"}


@app.get("/questions")
async def questions(course_code: str = "BAECE102"):
    course_code = validate_course_code(course_code)
    return get_all_questions(course_code)


@app.get("/courses")
async def list_courses():
    courses = get_all_courses_data()
    # Merge stats from ChromaDB
    for course in courses:
        cc = validate_course_code(course["course_code"])
        stats = rag.get_course_stats(cc)
        course["doc_count"] = len(stats.get("documents", []))
        course["chunk_count"] = stats.get("total_chunks", 0)
    return courses


@app.post("/courses")
async def create_new_course(body: CourseCreate):
    try:
        # Pydantic already validated lengths
        course_code = validate_course_code(body.course_code)
        new_course = create_course(course_code, body.course_name, body.description, body.icon)
        return new_course
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/generate-paper")
async def create_paper(body: PaperRequest):
    course_code = validate_course_code(body.course_code)
    # Retrieve chunks related to the topics or just general course chunks
    sanitized_topics = [sanitize_text(t, MAX_TOPIC_LENGTH) for t in body.topics]
    query_str = " ".join(sanitized_topics) if sanitized_topics else "overview of the course"
    
    chunks = await rag.retrieve(
        query=query_str,
        course_code=course_code,
        top_k=body.top_k
    )
    
    if not chunks:
        raise HTTPException(404, "No course content found to generate a paper from.")
        
    paper = await generate_paper(
        course_code=course_code,
        total_marks=body.total_marks,
        difficulty=body.difficulty,
        topics=sanitized_topics,
        chunks=chunks
    )
    return paper


@app.post("/ingest")
async def ingest_pdf(
    file: Annotated[UploadFile, Form(description="PDF file to ingest")],
    course_code: Annotated[str, Form()] = "BAECE102",
    topic: Annotated[str, Form()] = "",
):
    course_code = validate_course_code(course_code)
    topic = sanitize_text(topic, MAX_TOPIC_LENGTH)
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    temp_path = f"/tmp/ingest_{uuid.uuid4().hex}.pdf"
    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(413, "File size exceeds limit (15MB)")

        with open(temp_path, "wb") as f:
            f.write(content)

        title = Path(file.filename).stem.replace("-", " ").replace("_", " ")
        title = sanitize_text(title, MAX_COURSE_NAME_LENGTH)

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


@app.post("/query-stream")
async def query_stream(body: QueryRequest):
    course_code = validate_course_code(body.course_code)
    session_id = sanitize_id(body.session_id)
    question = sanitize_text(body.question, MAX_QUESTION_LENGTH)
    
    history = get_course_history(body.course_code, body.session_id)

    async def stream_generator():
        full_response = ""
        metadata = {}
        
        async for chunk in engine.query_stream(
            query=question,
            course_code=course_code,
            course_name=course_code,
            language=body.language,
            mastery=body.mastery,
            history=history,
            top_k=body.top_k
        ):
            if chunk["type"] == "content":
                full_response += chunk["content"]
            elif chunk["type"] == "metadata":
                metadata = chunk
            
            yield f"data: {json.dumps(chunk)}\n\n"
        
        # After stream: Log and save history
        if full_response:
            log_query(question, course_code, full_response, metadata.get("cited_sources", []))
            add_message(course_code, session_id, "user", question)
            add_message(course_code, session_id, "assistant", full_response)

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


@app.post("/query", response_model=QueryResponse)
async def query(body: QueryRequest):
    course_code = validate_course_code(body.course_code)
    session_id = sanitize_id(body.session_id)
    question = sanitize_text(body.question, MAX_QUESTION_LENGTH)

    history = get_course_history(body.course_code, body.session_id)

    result = await engine.query(
        query=question,
        course_code=course_code,
        course_name=course_code, # Use course_code as name if name not available
        language=body.language,
        mastery=body.mastery,
        history=history,
        top_k=body.top_k
    )

    # Log the query for analytics
    log_query(question, course_code, result["response"], result["cited_sources"])
    
    # Save to chat history
    add_message(course_code, session_id, "user", question)
    add_message(course_code, session_id, "assistant", result["response"])

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
        course_code = validate_course_code(course_code)
        updated = update_course(course_code, body.course_name, body.description, body.icon)
        return updated
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.delete("/courses/{course_code}")
async def remove_course(course_code: str):
    try:
        course_code = validate_course_code(course_code)
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
    course_code = validate_course_code(body.course_code)
    topic = sanitize_text(body.topic, MAX_TOPIC_LENGTH)

    chunks = await rag.retrieve(query=topic, course_code=course_code, top_k=10)
    if not chunks:
        raise HTTPException(404, "No materials found to generate flashcards.")
    
    context = "\n".join([c["text"] for c in chunks if c.get("text")])
    
    prompt = f"""Based on the following course materials, generate {body.count} flashcards for the topic: {topic}.
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
    course_code = validate_course_code(body.course_code)
    topic = sanitize_text(body.topic, MAX_TOPIC_LENGTH)
    return saved_content.save_flashcards(course_code, topic, body.cards)

@app.get("/flashcards/saved")
async def get_saved_flashcards(course: str = Query(...)):
    course = validate_course_code(course)
    return saved_content.get_saved_flashcards(course)

@app.delete("/flashcards/saved/{set_id}")
async def delete_saved_flashcards(set_id: str):
    set_id = sanitize_id(set_id)
    if not saved_content.delete_flashcards(set_id):
        raise HTTPException(404, "Flashcard set not found.")
    return {"status": "success"}

@app.post("/quiz")
async def generate_quiz(body: QuizRequest):
    course_code = validate_course_code(body.course_code)
    topic = sanitize_text(body.topic, MAX_TOPIC_LENGTH)

    if not topic:
        raise HTTPException(400, "Quiz topic cannot be empty.")

    chunks = await rag.retrieve(query=topic, course_code=course_code, top_k=10)
    if not chunks:
        raise HTTPException(404, "No materials found to generate a quiz.")
    
    context = "\n".join([c["text"] for c in chunks if c.get("text")])
    prompt = f"""Based on the following course materials, generate {body.count} multiple-choice quiz questions for the topic: {topic}.
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
    course_code = validate_course_code(body.course_code)
    topic = sanitize_text(body.topic, MAX_TOPIC_LENGTH)
    return saved_content.save_quiz(course_code, topic, body.questions, body.score)

@app.get("/quiz/saved")
async def get_saved_quizzes(course: str = Query(...)):
    course = validate_course_code(course)
    return saved_content.get_saved_quizzes(course)

@app.delete("/quiz/saved/{quiz_id}")
async def delete_saved_quiz(quiz_id: str):
    quiz_id = sanitize_id(quiz_id)
    if not saved_content.delete_quiz(quiz_id):
        raise HTTPException(404, "Quiz not found.")
    return {"status": "success"}


@app.get("/chunks")
async def get_chunks(
    course_code: str = "BAECE102",
    query: str = "",
    top_k: int = 5,
):
    course_code = validate_course_code(course_code)
    query = sanitize_text(query, MAX_QUESTION_LENGTH)
    
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
