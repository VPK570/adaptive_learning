# Loading Dots — Complete Design Document

## Problem

When a user sends a question in the AI Study Assistant chat (`page.tsx:handleSend`), an empty assistant message bubble is created immediately. There was **zero visual feedback** during the 5-70s gap between sending and the first content chunk arriving via polling. Users see an empty bubble and cannot tell if the system is working.

## Constraints

| Constraint | Source | Impact |
|---|---|---|
| Cloudflare Tunnel buffers SSE-over-GET | `cloudflared` + Edge proxy | Cannot use `GET /query-stream/{task_id}` — events arrive only after connection closes |
| Global 60 req/min rate limit | `server.py:77` — slowapi | Polling at 500ms = 120 req/min, exceeds limit |
| Celery async task model | `tasks.py:process_query_task` | Answer is generated in background worker, chunks written to Redis list `query_progress:{task_id}` |
| Dark periwinkle theme | `globals.css` — `#13131b` bg, `#c0c1ff` primary | Loading state must match existing design language |
| Page reload resilience | User can refresh mid-query | Must resume polling from stored `task_id` in `sessionStorage` |

## Architecture

```
User -> handleSend()
  -> POST /query-async -> returns { task_id }
  -> POST /query-async -> Celery: process_query_task()
    -> engine.query_stream() yields chunks
    -> r.rpush("query_progress:{id}", json.dumps(chunk))
  -> Frontend: queryPollTask(task_id, callbacks)
    -> GET /query-result/{task_id}?start=N  (every 2s)
    -> Backend reads Redis LRANGE -> returns { entries, next_start, done }
    -> onContent -> setMessages (appends to assistant bubble text)
    -> onDone -> setStreaming(false), clear sessionStorage
  -> ChatMessage: if isStreaming && !msg.text -> show typing dots
```

## Key Design Decisions

| Decision | Chosen | Alternatives Considered | Why |
|---|---|---|---|
| Transport | Polling (GET /query-result) | SSE, WebSocket, sync POST /query | Cloudflare Tunnel compatibility |
| Poll interval | 2000ms | 500ms, 1000ms | Stay under 60 req/min limit (30 polls/min vs 120) |
| Loading animation | 3 CSS dots, scale+opacity pulse | Spinner, skeleton, glow ring, wave bar | Minimal code, no dependencies, matches typing metaphor |
| Animation color | `var(--color-primary)` (#c0c1ff) | Secondary mint (#4edea3), tertiary (#ffb2b7) | Matches assistant accent, doesn't clash |
| Timeout | 60s elapsed from start | Consecutive empty polls | Predictable, not affected by bursty chunk arrivals |
| Error retry | 2x generic (1s, 2s), 5x 429 (5s increments) | No retry, infinite retry | Transient blips survive, rate limits eventually clear |
| Unmount cleanup | `useRef` + `useEffect` cleanup -> `.stop()` | Ignore flag, AbortController | Stops HTTP requests, saves bandwidth |
| Target message | Only last message when `streaming && role === 'assistant'` | All streaming messages | Only the in-flight message should show dots |

## Files Changed

| File | What | Lines |
|---|---|---|
| `backend/app/routers/query.py` | `GET /query-result/{task_id}?start=N` -- reads Redis LRANGE, returns JSON | +25 |
| `new_frontend/next.config.mjs` | Rewrite: `/query-result/:path*` -> backend | +1 |
| `new_frontend/src/lib/api/chat.ts` | `queryPollTask()` -- recursive setTimeout, 2s interval, retry, timeout, token refresh | +55 |
| `new_frontend/src/app/student/courses/[code]/page.tsx` | `attachPoll` replaces old SSE attach; `isStreaming` prop; `pollerRef` cleanup | +30 |
| `new_frontend/src/app/student/courses/[code]/CourseDetail.module.css` | `.streaming` border glow, `.typingIndicator` with `@keyframes typingDot`, `@keyframes pulse` | +36 |

## API Contract

```
GET /query-result/{task_id}?start=0

Response:
{
  "entries": [
    {"type": "thinking", "content": "..."},
    {"type": "content", "content": "..."},
    {"type": "metadata", "cited_sources": [...], "verified": true},
    {"type": "done"}
  ],
  "next_start": 5,
  "done": true
}
```

## Edge Cases Handled

| Case | Handling |
|---|---|
| Page reload mid-query | `sessionStorage` has `task_id`, `resumeActiveTask` re-polls from index 0 |
| Multiple page reloads | Each reload creates new assistant bubble, old pollers stopped by `useEffect` cleanup |
| Query takes >60s | Elapsed-time timeout fires `onError`, clears `sessionStorage` |
| Redis key expires (10min TTL) | Backend returns `{entries:[], done:false}` -> frontend times out at 60s |
| Rate limit (429) | Detected in catch, retries 5x with 5s/10s/15s/20s/25s backoff |
| Network blip | 2 retries with 1s/2s backoff before `onError` |
| Token refresh during poll | Token read fresh inside each `poll()` call from `useAuthStore.getState().token` |
| Send button during streaming | `handleSend` guards: `if (streaming) return`; button is `disabled` |

## Open Questions (for other models)

1. **2s polling delay**: First chunk text arrives up to 2s after generation. Acceptable for 30-70s queries? Should we use adaptive polling (fast at start, slow down)?
2. **Instant dots->text transition**: Dots vanish and text appears with no fade. Add `opacity` transition?
3. **`prefers-reduced-motion`**: Should the typing animation be disabled for accessibility?
4. **Rate limit safety margin**: 30 polls/min + ~10 other = 40/60 used. Is this enough headroom? Should we add backend exemption as backup?