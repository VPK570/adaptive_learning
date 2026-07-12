# Frontend–Backend Integration Architecture

> **Status:** Design doc  
> **Scope:** Wire `new_frontend` to existing FastAPI backend. Auth enforcement, data fetching layer, mock data replacement, placeholder page fill-in.  
> **Style:** Robust and scalable. Not minimal — built to grow.

---

## 1. Current State

### Backend (FastAPI)
- 31 endpoints across 9 routers (query, courses, analytics, chat, ingestion, flashcards, quiz, paper, auth)
- Auth infrastructure exists (`auth.py`: JWT + bcrypt, `get_current_user`, `require_role`) but **zero routes enforce it**
- All endpoints are effectively public
- Postgres for auth (UserStore), SurrealDB for content

### Frontend (new_frontend — Next.js)
- 15 pages, only **login** calls the real API
- All other pages use `src/lib/mockData.ts` (176 lines)
- Token stored in `localStorage` but never sent in requests
- `src/lib/api.js` only exports `login()` and `register()` — no other endpoints
- No auth context, no provider, no route protection
- Login redirects to `/dashboard` — actual path is `/student/dashboard` (bug)
- `AppShell` receives `user` prop from mock data on every page

---

## 2. Target Architecture

```
                    ┌──────────────────────────────────────┐
                    │          Next.js Pages (15)           │
                    │  Each page: hook → data → render     │
                    └──────────┬───────────────────────────┘
                               │
                    ┌──────────▼───────────────────────────┐
                    │      Custom Hooks (useCourses,        │
                    │   useQuiz, useChat, useAnalytics...)  │
                    │  Wraps TanStack Query useQuery/Mut.  │
                    └──────────┬───────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────▼─────┐  ┌──────▼───────┐  ┌────▼──────────┐
     │   Zustand    │  │  TanStack    │  │    Axios      │
     │  Auth Store  │  │ Query Cache  │  │  Instance     │
     │ token, user, │  │ server state │  │ + interceptors│
     │ login/logout │  │ dedup, refetch│  │ token inject  │
     │ persist → LS │  │ loading/err  │  │ 401 → logout  │
     └──────────────┘  └──────────────┘  └────┬──────────┘
                                              │
                               ┌──────────────▼────────────┐
                               │  FastAPI Backend (31 EP)   │
                               │  + auth middleware         │
                               │  + /users/me endpoint      │
                               │  + /courses/{code}         │
                               │  + /students/stats         │
                               └───────────────────────────┘
```

### Technology Choices

| Layer | Choice | Rationale |
|-------|--------|-----------|
| HTTP client | **Axios** | Interceptors for token injection + 401 handling. `fetch` has none — you'd hand-roll wrappers everywhere. |
| Server state | **TanStack Query v5** | Caching, dedup, background refetch, loading/error/success states, optimistic updates, pagination. Eliminates hand-rolled `useEffect` + `useState` data fetching. |
| Client state | **Zustand v5** | Auth state that Axios interceptors can read (React Context can't). Persists to localStorage. No boilerplate. |
| Auth enforcement | **FastAPI middleware** | Single code path in `server.py`. One place to exclude `/auth/*`, `/health`, `/docs`. |
| Styling | **Existing CSS modules** (no change) | Project uses `*.module.css` + `globals.css`. No Tailwind. Keep it. |
| Forms | **HTML5 validation + API errors** (no library) | Login, register, and paper generation don't need Formik/React Hook Form at this scale. |

---

## 3. Shared Infrastructure

### 3.1 Backend: Auth Enforcement

**File:** `backend/server.py`

Add a middleware that validates JWT on every request except public paths:

```
Public paths:  /auth/*, /health, /docs, /openapi.json, /redoc
Protected:     everything else
```

The existing `get_current_user` dependency in `auth.py` already does JWT decode + user lookup. The middleware calls it and attaches the user dict to `request.state.user`.

New endpoints needed on the backend:

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/users/me` | GET | Return current user profile (id, email, role, name, created_at) | High |
| `/users/me` | PUT | Update profile (display name, avatar) | Medium |
| `/courses/{code}` | GET | Single course detail with stats (title, professor, term, mastery, materials) | High |
| `/students/stats` | GET | Aggregated student stats across all enrolled courses | Medium |

All existing 31 endpoints remain unchanged — the middleware just gates access.

### 3.2 Frontend: Dependencies

Add to `package.json`:

```json
{
  "dependencies": {
    "axios": "^1.7.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^5.0.0"
  }
}
```

### 3.3 Frontend: Zustand Auth Store

**File:** `src/lib/store/authStore.ts`

```typescript
interface AuthState {
  token: string | null;
  user: { email: string; role: string; name: string } | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hydrate: () => void;  // re-read localStorage on mount
}
```

- Uses Zustand `persist` middleware with `localStorage` storage
- `login()` calls `POST /auth/login`, stores token + decoded user info
- `logout()` clears state, calls `localStorage.clear()`, redirects to `/`
- `hydrate()` called in provider `useEffect` — reads token on page refresh

### 3.4 Frontend: Axios Instance

**File:** `src/lib/api/client.ts`

```typescript
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001',
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor: inject Bearer token
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor: on 401 → logout
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().logout();
    }
    return Promise.reject(err);
  }
);
```

### 3.5 Frontend: API Domain Modules

```
src/lib/api/
├── client.ts          # Axios instance + interceptors
├── types.ts           # All request/response TypeScript interfaces
├── auth.ts            # POST /auth/login, /auth/register
├── courses.ts         # GET /courses, POST/PUT/DELETE /courses/{code}
├── quiz.ts            # POST /quiz, POST /quiz/save, GET/DELETE /quiz/saved
├── flashcards.ts      # POST /flashcards, POST /flashcards/save, GET/DELETE
├── chat.ts            # GET/POST/DELETE /chat-history
├── analytics.ts       # GET /analytics, /analytics/unanswered, /analytics/coverage
├── ingestion.ts       # POST /ingest, POST /curriculum (multipart)
├── paper.ts           # POST /generate-paper
└── users.ts           # GET/PUT /users/me
```

Each module exports typed async functions:
```typescript
// courses.ts
export const coursesApi = {
  list: () => api.get<Course[]>('/courses'),
  get: (code: string) => api.get<CourseDetail>(`/courses/${code}`),
  create: (data: CourseCreate) => api.post<Course>('/courses', data),
  update: (code: string, data: CourseUpdate) => api.put<Course>(`/courses/${code}`, data),
  remove: (code: string) => api.delete(`/courses/${code}`),
};
```

### 3.6 Frontend: Providers

**File:** `src/app/providers.tsx`

```typescript
export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: true },
    },
  }));

  useEffect(() => { useAuthStore.getState().hydrate(); }, []);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

Wrap root layout in `layout.tsx`:

```typescript
export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
```

### 3.7 Frontend: Route Protection Layouts

Each role section gets a layout that checks auth and redirects:

**Files:**
- `src/app/student/layout.tsx`
- `src/app/faculty/layout.tsx`
- `src/app/admin/layout.tsx`

```typescript
export default function RoleLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) router.replace('/');
    // Optional: check user.role matches the layout role
  }, [isAuthenticated]);

  if (!isAuthenticated) return null;  // or loading spinner
  return <>{children}</>;
}
```

Login page also gets guard logic: if `isAuthenticated`, redirect to role-appropriate dashboard.

### 3.8 AppShell: Remove `user` Prop

`AppShell` reads user from zustand store instead of requiring a prop:

```typescript
// Inside AppShell.tsx
const user = useAuthStore((s) => s.user) ?? { name: 'User', initials: 'U' };
```

This eliminates the mock user passed from every page.

---

## 4. Page Wiring — Phase 2

Each page follows this pattern:

```typescript
export default function Page() {
  const { data, isLoading, error } = usePageData();

  if (isLoading) return <Skeleton />;
  if (error) return <ErrorState message={error.message} />;
  if (!data) return <EmptyState />;

  return <PageUI data={data} />;
}
```

Custom hooks per page:

| Page | Hook | Endpoints | Replaces Mock |
|------|------|-----------|---------------|
| Login | `useAuthStore.login()` | `POST /auth/login` | Nothing (already works) |
| Student Dashboard | `useStudentDashboard()` | `GET /courses`, `GET /students/stats` | `mockStudentUser`, `mockStudentStats`, `mockStudentCourses` |
| Course Detail + Chat | `useCourseDetail(code)` + `useChat()` | `GET /courses/{code}`, `POST /query-stream`, `GET/POST/DELETE /chat-history` | `courseDetail`, `chatMessages` |
| Student Progress | `useStudentProgress()` | `GET /analytics`, `GET /analytics/unanswered`, `GET /analytics/coverage` | `progressStats`, `topicsBreakdown`, `recommendedRevision` |
| Faculty Dashboard | `useFacultyDashboard()` | `GET /courses`, `GET /analytics*`, `GET /questions` | `mockFacultyUser`, `mockFacultyStats`, `mockFacultyActivity`, `mockFacultyCourses` |
| Faculty Course Upload | `useCourseMaterials(code)` | `POST /ingest`, `POST /curriculum`, `GET /stats` | `useState` files + `mockFacultyUser` |
| Generate Paper | `useGeneratePaper()` | `POST /generate-paper`, `GET /courses` | `generateSections`, `generatedPaper` |
| Quiz | `useQuiz()` | `POST /quiz`, `POST /quiz/save`, `GET/DELETE /quiz/saved` | Placeholder → full UI |
| Flashcards | `useFlashcards()` | `POST /flashcards`, `POST /flashcards/save`, `GET/DELETE /flashcards/saved` | Placeholder → full UI |

### Chat Integration (Course Detail Page)

The student course page has a real-time chat panel. Wire it:

1. **On mount:** `GET /chat-history?course_code=X&session_id=Y` loads previous messages
2. **On send:** `POST /query-stream` (SSE) streams response tokens + sources + citations
3. **Auto-save:** On each assistant response, `POST /chat-history` to persist
4. **Clear:** Link to `DELETE /chat-history`

The existing SSE handler in the backend sends JSON events:
```json
data: {"type": "content", "content": "token text"}
data: {"type": "metadata", "cited_sources": [...], "chunks_retrieved": 5}
```

Frontend reads the event stream via `EventSource` or `fetch` + `ReadableStream`.

### File Upload (Faculty Course Page)

1. **Dropzone** triggers `POST /ingest` as multipart/form-data:
   - `file`: the PDF
   - `course_code`: from URL param
   - `topic`: from UI input
2. **On success:** response includes `{status, text_chunks_created, image_chunks_created, document_title}`
3. **Poll for status:** `GET /stats?course_code=X` returns document list with processing status
4. **UI:** Show processing steps (text extraction → chunking → embedding) as progress indicators

### Quiz + Flashcards: New UI

Both are currently placeholders. Build proper UIs:

**Quiz Page:**
1. Course selector → topic picker → question count
2. Generate: `POST /quiz` → display one question at a time (options as buttons)
3. Answer: highlight correct/incorrect, show explanation
4. Score: track running score, show summary at end
5. Save: `POST /quiz/save` with questions + score

**Flashcards Page:**
1. Course selector → topic picker → card count
2. Generate: `POST /flashcards` → display as flip cards
3. Study: tap to flip, "Know it" / "Study again" buttons
4. Save: `POST /flashcards/save` to persist set

---

## 5. New Backend Endpoints Needed — Phase 3

Pages that can't be fully wired with existing endpoints:

| Page | Gap | Solution |
|------|-----|----------|
| Student Chat (general) | `POST /query` requires `course_code` — no general mode | Make `course_code` optional; default to all enrolled courses |
| Profile pages (student/faculty/admin) | No user profile read/update | `GET /users/me`, `PUT /users/me` |
| Faculty Analytics | Backend endpoints exist (`/analytics*`) — just needs UI | No new backend work |
| Admin Dashboard | No admin-specific endpoints | Entirely new scope — platform stats, user management, system health |

### Profile Endpoints

**`GET /users/me`**
- Auth required (uses middleware)
- Returns: `{ id, email, role, name, created_at }`
- Name defaults to email prefix until user updates it

**`PUT /users/me`**
- Accepts: `{ name?: string, avatar_url?: string }`
- Updates user store in Postgres
- Returns updated user

### Student Chat — General Query Mode

Current `POST /query` requires `course_code`. For the general chat page:
- Make `course_code` optional in `QueryRequest` schema
- When omitted, search across all courses the student is enrolled in
- Or: add `POST /query-general` that does cross-course retrieval

---

## 6. Error Handling Strategy

| Layer | Strategy |
|-------|----------|
| Axios interceptor | Catches 401 globally → auto logout |
| TanStack Query | `isError` + `error` on every query; `onError` callback for toasts |
| API modules | Throw typed errors: `ApiError` with `status`, `message`, `details` |
| Pages | Render error state: icon + message + retry button |
| Layout | Error boundary catches unhandled render errors |

---

## 7. Mock Data Deletion

`src/lib/mockData.ts` stays until **all pages are confirmed wired** — it's a reference for expected data shapes. Delete after Phase 2 completion.

---

## 8. Delivery Order

| Step | Area | Description | Est. Files |
|------|------|-------------|------------|
| 1 | Backend | Auth middleware + `/users/me` + `/courses/{code}` + `/students/stats` | 3-5 |
| 2 | Frontend | Install deps, zustand store, axios client, API modules, providers | 12-15 |
| 3 | Frontend | Route layouts (auth guards), fix login redirect, AppShell auth | 6 |
| 4 | Frontend | Wire Student Dashboard + Course Detail + Chat | 4 |
| 5 | Frontend | Wire Faculty Dashboard + Course Upload + Generate Paper | 4 |
| 6 | Frontend | Wire Student Progress + Analytics | 2 |
| 7 | Frontend | Build Quiz UI | 2-3 |
| 8 | Frontend | Build Flashcards UI | 2-3 |
| 9 | Cross | New backend APIs (general chat, profiles) + remaining pages | 4-6 |
| 10 | Cleanup | Delete mockData.ts, verify all pages, run lint | 1 |

---

## 9. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Auth state | Zustand (not React Context) | Axios interceptors need token access outside React tree |
| HTTP client | Axios (not fetch) | Interceptors for token injection + 401 handling |
| Server state | TanStack Query | Caching, dedup, loading states without boilerplate |
| Auth enforcement | Backend middleware (not per-route Depends) | Single code path, easy path exclusion |
| File structure | `src/lib/api/*.ts` per domain | Scales as endpoints grow |
| Quiz + Flashcards UI | Built from scratch (not third-party) | No lib handles our data shape + backend model |
| Styling | Existing CSS modules (no change) | No benefit from rewriting to Tailwind |
| Mock deletion | Last step, after all pages wired | Reference for data shapes during migration |
