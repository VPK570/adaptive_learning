from typing import List

from pydantic import BaseModel, Field

from app.validation import (
    MAX_COURSE_CODE_LENGTH,
    MAX_COURSE_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_LANGUAGE_LENGTH,
    MAX_QUESTION_LENGTH,
    MAX_SESSION_ID_LENGTH,
    MAX_TOPIC_LENGTH,
)


class QueryRequest(BaseModel):
    question: str = Field(..., max_length=MAX_QUESTION_LENGTH)
    course_code: str = Field("BAECE102", max_length=MAX_COURSE_CODE_LENGTH)
    session_id: str = Field("default", max_length=MAX_SESSION_ID_LENGTH)
    top_k: int = Field(5, ge=1, le=20)
    language: str = Field("English", max_length=MAX_LANGUAGE_LENGTH)
    mastery: float | None = Field(None, ge=0.0, le=1.0)
    bloom_level: int | None = Field(None, ge=1, le=6)
    image_ids: list[str] = Field(default_factory=list, max_length=5)
    source_titles: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)


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
    bloom_levels: list[int] | None = Field(None, min_length=1, max_length=6)


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
    bloom_levels: list[int] | None = Field(None, min_length=1, max_length=6)


class SaveFlashcardRequest(BaseModel):
    course_code: str = Field(..., max_length=MAX_COURSE_CODE_LENGTH)
    topic: str = Field(..., max_length=MAX_TOPIC_LENGTH)
    cards: list[dict]


class RecordFlashcardRequest(BaseModel):
    known_count: int = Field(..., ge=0)
    total: int = Field(..., ge=1)


class ChatFeedbackRequest(BaseModel):
    question: str = Field(..., max_length=MAX_QUESTION_LENGTH)
    course_code: str = Field(..., max_length=MAX_COURSE_CODE_LENGTH)
    helpful: bool


class QuizRequest(BaseModel):
    course_code: str = Field(..., max_length=MAX_COURSE_CODE_LENGTH)
    topic: str = Field(..., max_length=MAX_TOPIC_LENGTH)
    count: int = Field(5, ge=1, le=20)
    bloom_levels: list[int] | None = Field(None, min_length=1, max_length=6)


class SaveQuizRequest(BaseModel):
    course_code: str = Field(..., max_length=MAX_COURSE_CODE_LENGTH)
    topic: str = Field(..., max_length=MAX_TOPIC_LENGTH)
    questions: list[dict]
    score: int = Field(..., ge=0)
    total: int = Field(..., ge=0)
    bloom_levels: list[int] | None = None
