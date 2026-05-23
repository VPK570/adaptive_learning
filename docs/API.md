# API Documentation

## Overview
The platform provides a RESTful API built with FastAPI.

## Endpoints

### Health
- `GET /health`

### Ingestion
- `POST /ingest` (Multipart/form-data: `file`, `course_code`, `topic`)

### Chat & Query
- `POST /query` (Body: `question`, `course_code`, `session_id`, `top_k`, `language`, `mastery`)
- `GET /chat-history` (Params: `course_code`, `session_id`)
- `POST /chat-history` (Params: `course_code`, `session_id`, `role`, `content`)
- `DELETE /chat-history` (Params: `course_code`, `session_id`)

### Curriculum
- `GET /curriculum` (Param: `course`)
- `POST /curriculum` (Multipart: `file`, `course_code`)
- `GET /curriculum/topics` (Param: `course`)

### Flashcards & Quizzes
- `POST /flashcards` (Body: `course_code`, `topic`, `count`)
- `POST /flashcards/save` (Body: `course_code`, `topic`, `cards`)
- `GET /flashcards/saved` (Param: `course`)
- `DELETE /flashcards/saved/{set_id}`
- `POST /quiz` (Body: `course_code`, `topic`, `count`)
- `POST /quiz/save` (Body: `course_code`, `topic`, `questions`, `score`)
- `GET /quiz/saved` (Param: `course`)
- `DELETE /quiz/saved/{quiz_id}`

### Analytics & Stats
- `GET /stats` (Param: `course_code`)
- `GET /analytics` (Param: `course_code`)
- `GET /analytics/unanswered` (Param: `course_code`)
- `GET /analytics/coverage` (Param: `course_code`)
- `GET /questions` (Param: `course_code`)

### Course Management
- `GET /courses`
- `POST /courses` (Body: `course_code`, `course_name`, `description`, `icon`)
- `PUT /courses/{course_code}` (Body: `course_name`, `description`, `icon`)
- `DELETE /courses/{course_code}`

### Generation
- `POST /generate-paper` (Body: `course_code`, `total_marks`, `difficulty`, `topics`)

### Raw Data
- `GET /chunks` (Params: `course_code`, `query`, `top_k`)
