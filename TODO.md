# Deferred Items — Backend & Frontend Gaps

## Missing Backend Endpoints

### Student Aggregate Stats
`GET /student/stats` or similar — returns overall mastery %, streak, topics completed, quizzes taken.
- Affects: Student Dashboard (radial progress, stat tiles), Student Progress (mastery stat)
- Current: shows `—` for all

### Student Study Activity / Heatmap
`GET /student/activity` — returns daily activity data for heatmap, active days, streak.
- Affects: Student Progress (heatmap section)
- Current: shows placeholder

### Faculty Activity Log  
`GET /faculty/activity` — returns recent student actions (who asked what, when).
- Affects: Faculty Dashboard (data table removed)
- Current: section removed from page

### Faculty Engagement Metrics
`GET /analytics/engagement?course_code=X` — returns engagement %, student counts.
- Affects: Faculty Dashboard (total students, avg engagement)
- Current: shows `—` for both

### Student Course Mastery
Per-student, per-course mastery percentage (no user-specific tracking in backend).
- Affects: Student Course Detail (mastery bar shows `—`)
- Current: shows `—` with 0% progress bar

### Analytics Batch Endpoint
`GET /analytics/batch?courses=code1,code2` — single request for multiple courses.
- Affects: Student Progress page (currently N parallel requests)
- Current: `Promise.all` loop, fine for <10 courses

## Missing Frontend Features

### Quiz & Flashcards Pages
Deferred to Phase 3. API modules exist (`api/quiz.ts`, `api/flashcards.ts`) but pages still use mock data.

### Curriculum File Listing in Upload Page
Backend `GET /curriculum` returns structured topics, not raw file list. Files appear only after upload.

## Enhancement Backlog

- Speech-to-text for chat input
- Export PDF for generated papers (PaperPreview has button but no implementation)
- Regenerate individual questions in PaperPreview
- Chat session isolation per browser tab (currently sessionId is `course_{code}` — same tab sharing)
- httpOnly cookie-based token storage (mitigate XSS token theft — requires backend changes)
