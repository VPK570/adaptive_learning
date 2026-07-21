# API Documentation

## Overview
RESTful API built with FastAPI. Base URL: `http://localhost:8001` (or backend container).

Auth is enforced via middleware on all routes except `/auth`, `/health`, `/docs`, `/openapi.json`, `/redoc`. JWT tokens are validated on every request.

---

## Endpoints

### Health

**`GET /health`**

Check service health (SurrealDB + OpenRouter connectivity).

Response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "dependencies": {
    "surrealdb": "ok",
    "openrouter": "ok"
  }
}
```

---

### Authentication

**`POST /auth/register`**

Register a new user.

Request body:
```json
{
  "email": "student@vit.edu",
  "password": "securepass123",
  "role": "student"
}
```
Roles: `student`, `faculty`, `admin`.

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "role": "student"
}
```

**`POST /auth/login`**

Login with email/password (uses `OAuth2PasswordRequestForm`).

Form fields:
- `username` (treated as email)
- `password`

Response: same as `TokenResponse` above.

> **Note:** JWT tokens are validated on every request via auth middleware. Protected routes require a valid Bearer token.

### Ingestion

**`POST /ingest`**

Upload and ingest a PDF document. (Multipart/form-data)

Fields:
- `file` — PDF file
- `course_code` (default: `"BAECE102"`)
- `topic` (default: `""`)

Response:
```json
{
  "status": "success",
  "text_chunks_created": 54,
  "image_chunks_created": 93,
  "document_title": "Digital Logic Design"
}
```

**`POST /curriculum`**

Upload a curriculum PDF for a course. (Multipart/form-data)

Fields:
- `file` — PDF file
- `course_code`

Response: curriculum ingestion result.

---

### Query

**`POST /query`**

Full RAG query → Socratic response with citations.

Request body:
```json
{
  "question": "Explain the state diagram for a modulo-6 counter",
  "course_code": "BAECE102",
  "session_id": "default",
  "top_k": 5,
  "language": "English",
  "mastery": null
}
```

Response:
```json
{
  "response": "A modulo-6 counter has 6 states... [Source: DLD Notes, Slide 42]",
  "cited_sources": ["DLD Notes, Slide 42", "DLD Notes, Slide 44"],
  "chunks_retrieved": 10,
  "text_chunks": 5,
  "image_chunks": 5
}
```

**`POST /query-stream`**

Same as `/query` but returns SSE stream of tokens.

Events:
```
data: {"type": "content", "content": "A modulo-6..."}
data: {"type": "content", "content": " counter..."}
data: {"type": "metadata", "cited_sources": [...], "chunks_retrieved": 10, ...}
```

---

### Quiz

**`POST /quiz`**

Generate quiz questions for a topic.

Request body:
```json
{
  "course_code": "BAECE102",
  "topic": "Flip-flops",
  "count": 5
}
```

Response: JSON array of question objects:
```json
[
  {
    "question": "What is the output of an SR latch when S=1, R=0?",
    "options": ["Q=1, Q'=0", "Q=0, Q'=1", "Q=1, Q'=1", "Q=0, Q'=0"],
    "correct_index": 0,
    "explanation": "When Set is active high...",
    "user_answer_index": -1,
    "is_correct": false
  }
]
```

---

### Flashcards

**`POST /flashcards`**

Generate flashcards for a topic.

Request body:
```json
{
  "course_code": "BAECE102",
  "topic": "Karnaugh Maps",
  "count": 5
}
```

Response: JSON array:
```json
[
  {
    "question": "What is a K-map?",
    "answer": "A graphical method to simplify boolean expressions..."
  }
]
```

---

### Exam Paper Generation

**`POST /generate-paper`**

Generate an exam paper with Bloom's taxonomy levels.

Request body:
```json
{
  "course_code": "BAECE102",
  "total_marks": 100,
  "difficulty": "Medium",
  "topics": [],
  "top_k": 10
}
```

Response: Generated paper object with sections and questions.

---

### Course Management

**`GET /courses`**

List all courses with stats (document count, chunk count).

**`POST /courses`**

Create a new course.

Request body:
```json
{
  "course_code": "CSET101",
  "course_name": "Programming Fundamentals",
  "description": "Intro to programming using Python",
  "icon": "🐍"
}
```

**`PUT /courses/{course_code}`**

Update a course. Fields are optional.

Request body:
```json
{
  "course_name": "Updated Name",
  "description": null,
  "icon": "📘"
}
```

**`DELETE /courses/{course_code}`**

Delete a course. Returns `{"status": "success"}`.

---

### Chat History

**`GET /chat-history`**

Get chat history for a session. Query params: `course_code`, `session_id`.

**`POST /chat-history`**

Add a message to chat history. Query params: `course_code`, `session_id`, `role`, `content`.

Returns `{"status": "success"}`.

**`DELETE /chat-history`**

Clear chat history for a session. Query params: `course_code`, `session_id`.

Returns `{"status": "success"}`.

---

### Analytics

**`GET /analytics`**

Get course analytics. Query param: `course_code` (default: `"BAECE102"`).

Returns aggregated analytics (query counts, activity, etc.).

**`GET /analytics/unanswered`**

Get unanswered/hard questions. Query param: `course_code`.

**`GET /analytics/coverage`**

Get curriculum coverage metrics. Query param: `course_code`.

**`GET /questions`**

Get all asked questions with metadata. Query param: `course_code`.

---

### User Management

**`GET /users/me`**

Get current user profile. Requires auth.

**`PUT /users/me`**

Update current user profile.

Request body:
```json
{
  "name": "Updated Name"
}
```

---

### Admin

**`GET /admin/stats`**

Get platform-wide statistics. Requires admin role.

**`GET /admin/users`**

List all users. Requires admin role.

---

### Learning Path

**`GET /api/learning-path/recommendations`**

Get personalized topic recommendations. Query param: `course_code`.

**`POST /api/learning-path/update-mastery`**

Update mastery for a topic.

Request body:
```json
{
  "course_code": "BAECE102",
  "topic": "Flip-flops",
  "correct": true
}
```

---

### Tasks (Celery)

**`GET /tasks/{task_id}`**

Check status of a background task.

**`POST /tasks/trigger/ingest`**

Trigger a scheduled ingestion task.

---

### Statistics

**`GET /stats`**

Get course statistics (document list, chunk counts). Query param: `course_code` (default: `"BAECE102"`).

---

### Curriculum

**`GET /curriculum`**

List curriculum files for a course. Query param: `course`.

**`GET /curriculum/topics`**

Get topics extracted from curriculum. Query param: `course`.

---

### Raw Data (Debug)

**`GET /chunks`**

Retrieve raw chunks for debugging. Query params: `course_code`, `query`, `top_k` (default: 5).

Returns array of:
```json
[
  {
    "chunk_id": "uuid",
    "text": "...",
    "source_title": "DLD Notes",
    "page": 42,
    "content_type": "text",
    "score": 0.892
  }
]
```

---

## Common Parameters

| Parameter | Type | Default | Constraints |
|-----------|------|---------|-------------|
| `course_code` | string | `"BAECE102"` | max 20 chars |
| `top_k` | integer | `5` | 1–20 |
| `session_id` | string | `"default"` | max 64 chars |
| `language` | string | `"English"` | max 30 chars |
| `mastery` | float | `null` | 0.0–1.0 |
| `topic` | string | — | max 200 chars |
| `count` | integer | `5` | 1–20 |

## Rate Limiting
60 requests/minute per IP across all routes (via `slowapi`, in-memory).

## CORS
Configured via `CORS_ORIGINS` env var (default: `*` in dev).
