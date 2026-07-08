"""Generate Excalidraw diagram file with all 10 architecture diagrams."""

import json
import time
import random

random.seed(42)

_id = 0
def el_id():
    global _id
    _id += 1
    return f"el{_id}"

def seed():
    return random.randint(10000, 99999)

def rect(x, y, w, h, fill="#ffffff", stroke="#1e1e1e", stroke_width=1, rough=1, dash=None, opacity=100, round=True):
    e = {
        "type": "rectangle",
        "id": el_id(),
        "x": x, "y": y, "width": w, "height": h,
        "angle": 0,
        "strokeColor": stroke,
        "backgroundColor": fill,
        "fillStyle": "solid",
        "strokeWidth": stroke_width,
        "strokeStyle": dash or "solid",
        "roughness": rough,
        "opacity": opacity,
        "groupIds": [],
        "roundness": {"type": 3} if round else None,
        "seed": seed(),
        "boundElements": [],
        "isDeleted": False,
        "updated": int(time.time() * 1000),
        "link": None,
        "locked": False,
    }
    return e

def text(x, y, txt, size=16, w=None, h=None, color="#1e1e1e", align="center", valign="middle", family=1, container=None, opacity=100):
    lines = txt.split("\n")
    lh = size * 1.2
    tw = w or (max(len(l) for l in lines) * size * 0.6)
    th = h or (len(lines) * lh)
    e = {
        "type": "text",
        "id": el_id(),
        "x": x, "y": y,
        "width": tw,
        "height": th,
        "angle": 0,
        "strokeColor": color,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": opacity,
        "groupIds": [],
        "roundness": None,
        "seed": seed(),
        "boundElements": [],
        "isDeleted": False,
        "updated": int(time.time() * 1000),
        "link": None,
        "locked": False,
        "text": txt,
        "fontSize": size,
        "fontFamily": family,
        "textAlign": align,
        "verticalAlign": valign,
        "containerId": container,
    }
    return e

def box(x, y, w, h, txt, fill="#ffffff", stroke="#1e1e1e", font_size=14, stroke_width=1, rough=1, dash=None, opacity=100, color="#1e1e1e"):
    r = rect(x, y, w, h, fill, stroke, stroke_width, rough, dash, opacity)
    cx = x + w/2
    cy = y + h/2
    # Estimate text width/height
    lines = txt.split("\n")
    lh = font_size * 1.2
    tw = max(len(l) for l in lines) * font_size * 0.6
    th = len(lines) * lh
    t = text(cx - tw/2, cy - th/2, txt, font_size, tw, th, color, "center", "middle", 1, r["id"], opacity)
    return r, t

def arrow(x1, y1, x2, y2, stroke="#1e1e1e", width=1, dash=None, end="arrow", start=None, opacity=100):
    e = {
        "type": "arrow",
        "id": el_id(),
        "x": x1, "y": y1,
        "width": abs(x2 - x1),
        "height": abs(y2 - y1),
        "angle": 0,
        "strokeColor": stroke,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": width,
        "strokeStyle": dash or "solid",
        "roughness": 1,
        "opacity": opacity,
        "groupIds": [],
        "roundness": {"type": 2},
        "seed": seed(),
        "boundElements": [],
        "isDeleted": False,
        "updated": int(time.time() * 1000),
        "link": None,
        "locked": False,
        "points": [[0, 0], [x2 - x1, y2 - y1]],
        "startBinding": None,
        "endBinding": None,
        "startArrowhead": start or None,
        "endArrowhead": end or None,
    }
    return e

def line(pts, stroke="#1e1e1e", width=1, dash=None):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    e = {
        "type": "line",
        "id": el_id(),
        "x": min(xs), "y": min(ys),
        "width": max(xs) - min(xs),
        "height": max(ys) - min(ys),
        "angle": 0,
        "strokeColor": stroke,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": width,
        "strokeStyle": dash or "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "roundness": {"type": 2},
        "seed": seed(),
        "boundElements": [],
        "isDeleted": False,
        "updated": int(time.time() * 1000),
        "link": None,
        "locked": False,
        "points": [[p[0] - min(xs), p[1] - min(ys)] for p in pts],
    }
    return e

def diagram_title(x, y, title, subtitle=""):
    els = []
    if subtitle:
        t = text(x, y, title, 22, 500, 30, "#1e1e1e", "left", "top")
        s = text(x, y + 28, subtitle, 12, 500, 18, "#868e96", "left", "top")
        els.extend([t, s])
    else:
        t = text(x, y, title, 22, 500, 30, "#1e1e1e", "left", "top")
        els.append(t)
    return els


# ============================================================
# Color palette
# ============================================================
C_FRONTEND   = "#7048e8"   # purple
C_BACKEND    = "#1971c2"   # blue
C_DB         = "#2f9e44"   # green
C_EXTERNAL   = "#e8590c"   # orange
C_AUTH       = "#c92a2a"   # red
C_ROUTER     = "#0c8599"   # teal
C_SERVICE    = "#6741d9"   # indigo
C_LLM        = "#f08c00"   # amber
C_STORAGE    = "#099268"   # teal green
C_BG         = "#f8f9fa"   # light gray
C_WHITE      = "#ffffff"
C_BLACK      = "#1e1e1e"
C_GRAY       = "#868e96"
C_LIGHT_BLUE = "#d0ebff"
C_LIGHT_GREEN= "#d3f9d8"
C_LIGHT_PURP = "#e5dbff"
C_LIGHT_ORNG = "#ffd8a8"
C_LIGHT_RED  = "#ffe3e3"
C_LIGHT_TEAL = "#c3fae8"
C_LIGHT_AMBR = "#fff3bf"

def build_diagrams():
    all_els = []

    # ============ DIAGRAM 1: High-Level Architecture ============
    x0, y0 = 100, 80
    all_els.extend(diagram_title(x0, y0, "1. High-Level Architecture", "Adaptive Learning Platform — system boundaries and data flow"))
    yr = y0 + 50

    # Frontend box
    b1r, b1t = box(x0, yr, 320, 160, "New Frontend\n(Next.js 16 / JavaScript)\nCSS Modules + lucide-react\nMock data (prototype)", C_LIGHT_PURP, C_FRONTEND, 11, 2)
    all_els.extend([b1r, b1t])

    # Backend box
    b2r, b2t = box(x0 + 400, yr, 320, 160, "Backend\n(FastAPI / Python)\n9 Routers + Service Layer\nRAG Pipeline + Auth", C_LIGHT_BLUE, C_BACKEND, 11, 2)
    all_els.extend([b2r, b2t])

    # SurrealDB box
    b3r, b3t = box(x0 + 800, yr + 50, 260, 110, "SurrealDB\n(Document DB)\nHNSW Vector Indexes\n10 Tables", C_LIGHT_GREEN, C_DB, 11, 2)
    all_els.extend([b3r, b3t])

    # OpenRouter box
    b4r, b4t = box(x0 + 1140, yr, 260, 160, "OpenRouter\n(External API)\nLLM: Nemotron 3B\nEmbeddings: Nemotron VL\nChat Completions", C_LIGHT_ORNG, C_EXTERNAL, 11, 2)
    all_els.extend([b4r, b4t])

    # Arrows
    all_els.append(arrow(x0 + 320, yr + 50, x0 + 400, yr + 50, C_FRONTEND, 2))
    all_els.append(arrow(x0 + 720, yr + 50, x0 + 800, yr + 75, C_BACKEND, 2))
    a = arrow(x0 + 720, yr + 50, x0 + 1140, yr + 50, C_BACKEND, 2)
    all_els.append(arrow(x0 + 940, yr + 160, x0 + 940, yr + 210, C_DB, 2))

    # Legend
    lx = x0 + 1140
    ly = yr + 220
    all_els.append(text(lx, ly, "Legend:", 12, 100, 18, C_GRAY, "left", "top"))
    all_els.extend(box(lx, ly+22, 12, 12, "", C_LIGHT_PURP, C_FRONTEND, 8, 1, 0))
    all_els.append(text(lx+18, ly+22, "Frontend", 10, 100, 14, C_GRAY, "left", "top"))
    all_els.extend(box(lx+100, ly+22, 12, 12, "", C_LIGHT_BLUE, C_BACKEND, 8, 1, 0))
    all_els.append(text(lx+118, ly+22, "Backend", 10, 100, 14, C_GRAY, "left", "top"))
    all_els.extend(box(lx+200, ly+22, 12, 12, "", C_LIGHT_GREEN, C_DB, 8, 1, 0))
    all_els.append(text(lx+218, ly+22, "Database", 10, 100, 14, C_GRAY, "left", "top"))
    all_els.extend(box(lx+300, ly+22, 12, 12, "", C_LIGHT_ORNG, C_EXTERNAL, 8, 1, 0))
    all_els.append(text(lx+318, ly+22, "External", 10, 100, 14, C_GRAY, "left", "top"))


    # ============ DIAGRAM 2: API Request/Response Flow ============
    x0, y0 = 100, 500
    all_els.extend(diagram_title(x0, y0, "2. API Request/Response Flow", "HTTP request lifecycle through the backend"))
    yr = y0 + 50

    # Components in flow
    comps = [
        ("HTTP\nRequest", C_EXTERNAL, C_LIGHT_ORNG),
        ("FastAPI\nRouter", C_ROUTER, C_LIGHT_TEAL),
        ("Validation\n& Sanitize", C_AUTH, C_LIGHT_RED),
        ("Service\nModule", C_SERVICE, C_LIGHT_PURP),
        ("DB / LLM", C_DB, C_LIGHT_GREEN),
        ("JSON\nResponse", C_EXTERNAL, C_LIGHT_ORNG),
    ]
    cw, ch = 130, 70
    gap = 40
    total_w = len(comps) * cw + (len(comps)-1) * gap
    start_x = x0 + 50
    for i, (label, sc, sf) in enumerate(comps):
        bx = start_x + i * (cw + gap)
        by = yr + 30
        r, t = box(bx, by, cw, ch, label, sf, sc, 11, 2)
        all_els.extend([r, t])
        if i < len(comps) - 1:
            ax = bx + cw
            ay = by + ch/2
            ax2 = ax + gap
            all_els.append(arrow(ax, ay, ax2, ay, sc, 2))

    # Async path annotation
    all_els.append(text(x0 + 50, yr + 130, "Streaming path: Request → Router → QueryEngine → Gatekeeper → RAG → LLM (SSE stream) → Verifier → Streaming chunks", 10, 700, 16, C_GRAY, "left", "top"))
    all_els.append(text(x0 + 50, yr + 150, "Non-streaming path: Same flow, plus citation validation + uncited claim removal + verification note appended to response", 10, 700, 16, C_GRAY, "left", "top"))

    # Example request/response boxes
    req_x = x0 + 50
    req_y = yr + 180
    rr, rt = box(req_x, req_y, 280, 60, "POST /query-stream\n{question, course_code, session_id, language, mastery}", C_LIGHT_BLUE, C_BACKEND, 10, 1)
    all_els.extend([rr, rt])
    ar = arrow(req_x + 280, req_y + 30, req_x + 360, req_y + 30, C_BACKEND, 1)
    all_els.append(ar)
    rr2, rt2 = box(req_x + 360, req_y, 280, 60, "SSE Stream:\ndata: {type: thinking|content}\ndata: {type: metadata, cited_sources}", C_LIGHT_GREEN, C_DB, 10, 1)
    all_els.extend([rr2, rt2])


    # ============ DIAGRAM 3: User Flow ============
    x0, y0 = 100, 820
    all_els.extend(diagram_title(x0, y0, "3. User Flow", "Navigation paths for students and faculty"))
    yr = y0 + 50

    # Student section
    all_els.append(text(x0 + 20, yr, "STUDENT", 16, 200, 22, C_FRONTEND, "left", "top"))
    # Swimlane box
    sr, _ = box(x0, yr + 25, 900, 300, "", "#f8f9fa", C_FRONTEND, 8, 1, None, 70)
    all_els.append(sr)

    student_pages = [
        ("Dashboard\n/", C_FRONTEND),
        ("Chat\n/chat", C_ROUTER),
        ("Quiz\n/quiz", C_SERVICE),
        ("Flashcards\n/flashcards", C_DB),
        ("Progress\n/progress", C_EXTERNAL),
    ]
    sp_w, sp_h = 130, 60
    sp_gap = 30
    sp_start = x0 + 40
    sp_top = yr + 55
    for i, (lbl, clr) in enumerate(student_pages):
        bx = sp_start + i * (sp_w + sp_gap)
        r, t = box(bx, sp_top, sp_w, sp_h, lbl, C_WHITE, clr, 11, 2)
        all_els.extend([r, t])
        if i > 0:
            all_els.append(arrow(bx - sp_gap, sp_top + sp_h/2, bx, sp_top + sp_h/2, C_GRAY, 1))

    # Enrollment via localStorage annotation
    all_els.append(text(x0 + 40, sp_top + 80, "Note: No login required. Course enrollment tracked in localStorage.", 10, 500, 16, C_GRAY, "left", "top"))

    # Faculty section
    fy = yr + 25 + 300 + 40
    all_els.append(text(x0 + 20, fy, "FACULTY", 16, 200, 22, C_EXTERNAL, "left", "top"))
    fr, _ = box(x0, fy + 25, 900, 300, "", "#f8f9fa", C_EXTERNAL, 8, 1, None, 70)
    all_els.append(fr)

    faculty_pages = [
        ("Faculty Dashboard\n/faculty", C_EXTERNAL),
        ("Manage Courses\n(CRUD)", C_ROUTER),
        ("Upload Materials\n/ingest + /curriculum", C_BACKEND),
        ("Generate Paper\n/generate-paper", C_LLM),
        ("Analytics\n/analytics", C_DB),
    ]
    fp_top = fy + 55
    for i, (lbl, clr) in enumerate(faculty_pages):
        bx = sp_start + i * (sp_w + sp_gap)
        r, t = box(bx, fp_top, sp_w, sp_h, lbl, C_WHITE, clr, 10, 2)
        all_els.extend([r, t])
        if i > 0:
            all_els.append(arrow(bx - sp_gap, fp_top + sp_h/2, bx, fp_top + sp_h/2, C_GRAY, 1))

    all_els.append(text(x0 + 40, fp_top + 80, "Note: Faculty routes unprotected. JWT auth built but NOT enforced on any route.", 10, 500, 16, C_GRAY, "left", "top"))


    # ============ DIAGRAM 4: Module Dependency ============
    x0, y0 = 1100, 500
    all_els.extend(diagram_title(x0, y0, "4. Module Dependency", "Startup initialization and dependency injection"))
    yr = y0 + 50

    # server.py box
    sr, st = box(x0 + 150, yr, 200, 50, "server.py\n(FastAPI entry)", C_LIGHT_BLUE, C_BACKEND, 12, 2)
    all_els.extend([sr, st])

    # 4 singletons
    sgl_y = yr + 80
    sgl_names = ["RAGPipeline\n(rag)", "QueryEngine\n(engine)", "CurriculumManager\n(curriculum)", "SavedContentManager\n(saved_content)"]
    sgl_colors = [C_ROUTER, C_SERVICE, C_DB, C_EXTERNAL]
    sgl_fills = [C_LIGHT_TEAL, C_LIGHT_PURP, C_LIGHT_GREEN, C_LIGHT_ORNG]
    sgl_w, sgl_h = 150, 55
    sgl_gap = 30
    sgl_start = x0
    for i, (nm, sc, sf) in enumerate(zip(sgl_names, sgl_colors, sgl_fills)):
        bx = sgl_start + i * (sgl_w + sgl_gap)
        r, t = box(bx, sgl_y, sgl_w, sgl_h, nm, sf, sc, 9, 2)
        all_els.extend([r, t])
        # arrow from server.py
        all_els.append(arrow(x0 + 250, yr + 50, bx + sgl_w/2, sgl_y, C_BACKEND, 1, "dashed"))

    # Router boxes
    router_y = sgl_y + 85
    router_names = ["query", "courses", "analytics", "chat", "ingestion", "flashcards", "quiz", "paper", "auth"]
    rw, rh = 80, 35
    r_gap = 12
    r_start = x0 + 10
    for i, nm in enumerate(router_names):
        bx = r_start + i * (rw + r_gap)
        r, t = box(bx, router_y, rw, rh, nm, C_LIGHT_TEAL, C_ROUTER, 9, 2)
        all_els.extend([r, t])
        # arrow from singletons to routers
        all_els.append(arrow(x0 + 250, sgl_y + 55, bx + rw/2, router_y, C_GRAY, 1, "dashed"))

    # Deps injector
    dr, dt = box(x0 + 400, router_y + 55, 180, 40, "deps.py\n(DI getters)", C_LIGHT_BLUE, C_BACKEND, 9, 1)
    all_els.extend([dr, dt])

    # External dependencies box
    exr, ext = box(x0 + 50, router_y + 120, 700, 60, "Shared Dependencies: db.py (SurrealDB)  |  openrouter.py (LLM/Embeddings)  |  config.py  |  validation.py  |  schemas.py", C_LIGHT_GREEN, C_DB, 9, 1)
    all_els.extend([exr, ext])


    # ============ DIAGRAM 5: Database ERD ============
    x0, y0 = 100, 1600
    all_els.extend(diagram_title(x0, y0, "5. Database Schema (ERD)", "SurrealDB tables, fields, and relationships"))
    yr = y0 + 50

    table_w, table_h = 200, 140
    t_gap_x, t_gap_y = 40, 30

    # Define tables
    tables = [
        # (name, fields, x, y, color)
        ("course", ["course_code (PK, unique)", "course_name", "description", "icon", "created_at"], x0 + 30, yr, C_DB),
        ("users", ["email (PK, unique)", "hashed_password", "role", "created_at"], x0 + 30, yr + 220, C_AUTH),
        ("document", ["id", "course_code (FK)", "filename", "content_hash (unique)", "created_at"], x0 + 30, yr + 440, C_STORAGE),
        ("text_chunk", ["id", "course_code (FK)", "text", "embedding (HNSW)", "source_title", "topic", "page", "content_type"], x0 + 330, yr, C_BACKEND),
        ("image_chunk", ["id", "course_code (FK)", "text", "embedding (HNSW)", "source_title", "topic", "page", "mime_type", "image_size_kb"], x0 + 330, yr + 220, C_LLM),
        ("curriculum_chunk", ["id", "course_code (FK)", "text", "embedding (HNSW)", "source_title", "topic", "page"], x0 + 330, yr + 440, C_SERVICE),
        ("chat_history", ["id", "course_code (FK)", "session_id", "role", "content", "timestamp"], x0 + 630, yr, C_ROUTER),
        ("flashcard_set", ["id", "course_code (FK)", "title", "flashcards (array)", "created_at"], x0 + 630, yr + 220, C_SERVICE),
        ("quiz", ["id", "course_code (FK)", "title", "questions (array)", "created_at", "score"], x0 + 630, yr + 440, C_DB),
        ("query_log", ["id", "course_code (FK)", "question", "response_preview", "timestamp", "out_of_scope", "cited_sources (array)"], x0 + 630, yr + 660, C_LLM),
    ]

    table_rects = {}
    for name, fields, tx, ty, color in tables:
        # Header
        hr, ht = box(tx, ty, table_w, 28, name, color, C_WHITE, 12, 2, None, 100, C_WHITE)
        all_els.extend([hr, ht])
        # Field rows
        row_h = 16
        for i, field in enumerate(fields):
            fx = tx + 5
            fy = ty + 30 + i * (row_h + 2)
            all_els.append(text(fx, fy, f"• {field}", 9, table_w - 10, row_h, C_BLACK, "left", "top"))
        # Background rect
        total_h = 30 + len(fields) * (row_h + 2) + 8
        # Put a background rectangle behind
        br, _ = box(tx, ty, table_w, total_h, "", "#ffffff" if color != C_AUTH else C_LIGHT_RED, color, 1, 1, None, 80)
        # Remove the header box we already added, add background first, then header on top
        # Actually easier: just draw box with outline, and text on top
        # Remove the header rect+text and redraw properly
        # (we already appended them - for simplicity let's just draw the outline box around the whole table)
        outline_r = rect(tx, ty, table_w, total_h, C_WHITE, color, 1.5, 1, opacity=90)
        all_els.append(outline_r)
        # Re-add header on top
        hr2, ht2 = box(tx, ty, table_w, 28, name, color, C_WHITE, 12, 2, None, 100, C_WHITE)
        all_els.extend([hr2, ht2])
        # Re-add field text (draw after background)
        for i, field in enumerate(fields):
            fx = tx + 8
            fy = ty + 32 + i * 17
            all_els.append(text(fx, fy, f"• {field}", 9, table_w - 16, 15, C_BLACK if color != C_AUTH else C_AUTH, "left", "top"))

        table_rects[name] = (tx + table_w/2, ty + total_h/2, tx, ty, tx + table_w, ty + total_h)

    # Relationships (arrows between tables)
    # course -> text_chunk, image_chunk, curriculum_chunk, chat_history, flashcard_set, quiz, query_log (FK course_code)
    course_cx, course_cy = table_rects["course"][0], table_rects["course"][1]
    course_r = table_rects["course"][4]
    targets = ["text_chunk", "image_chunk", "curriculum_chunk", "chat_history", "flashcard_set", "quiz", "query_log"]
    for tname in targets:
        if tname in table_rects:
            t_l = table_rects[tname][2]
            t_cy2 = table_rects[tname][1]
            # Horizontal arrow from right of course to left of target
            all_els.append(arrow(course_r, course_cy, t_l, course_cy, C_DB, 1, "dashed", "arrow", opacity=50))
            # Actually arrows will overlap. Let's do smart routing.
            # Just draw a simple line annotation
            break  # Simplified: one arrow with note

    # N:M relationships note
    note_x = x0 + 30
    note_y = yr + 660
    all_els.append(text(note_x, note_y, "Relationships: course.course_code → *.*course_code (FK on 7 tables)", 10, 500, 16, C_GRAY, "left", "top"))
    all_els.append(text(note_x, note_y + 16, "Cascade delete: DELETE course triggers cascade to text_chunk, image_chunk, curriculum_chunk via SurrealDB EVENT", 10, 600, 16, C_GRAY, "left", "top"))
    all_els.append(text(note_x, note_y + 32, "Indexes: Unique on course_code, email, content_hash. course_code indexes on all FK tables. HNSW vector on chunks. BM25 fulltext on text_chunk.", 10, 700, 16, C_GRAY, "left", "top"))


    # ============ DIAGRAM 6: Auth Flow ============
    x0, y0 = 1100, 820
    all_els.extend(diagram_title(x0, y0, "6. Authentication & Authorization", "JWT-based auth with bcrypt password hashing"))
    yr = y0 + 50

    # Register flow
    all_els.append(text(x0 + 20, yr, "Register: POST /auth/register", 12, 300, 18, C_AUTH, "left", "top"))
    reg_comps = [
        ("Client", C_FRONTEND, C_LIGHT_PURP, 0),
        ("Validation", C_AUTH, C_LIGHT_RED, 1),
        ("bcrypt hash", C_LLM, C_LIGHT_AMBR, 2),
        ("SurrealDB\nusers table", C_DB, C_LIGHT_GREEN, 3),
        ("JWT Response", C_EXTERNAL, C_LIGHT_ORNG, 4),
    ]
    for label, sc, sf, idx in reg_comps:
        bx = x0 + 30 + idx * 155
        r, t = box(bx, yr + 25, 130, 45, label, sf, sc, 9, 2)
        all_els.extend([r, t])
        if idx < len(reg_comps) - 1:
            all_els.append(arrow(bx + 130, yr + 47, bx + 155, yr + 47, sc, 1))

    # Login flow
    log_y = yr + 100
    all_els.append(text(x0 + 20, log_y, "Login: POST /auth/login (OAuth2 form)", 12, 350, 18, C_AUTH, "left", "top"))
    log_comps = [
        ("Client\n(email+pass)", C_FRONTEND, C_LIGHT_PURP, 0),
        ("Lookup user\nby email", C_DB, C_LIGHT_GREEN, 1),
        ("bcrypt\nverify", C_LLM, C_LIGHT_AMBR, 2),
        ("JWT\n(24h expiry)", C_EXTERNAL, C_LIGHT_ORNG, 3),
    ]
    for label, sc, sf, idx in log_comps:
        bx = x0 + 30 + idx * 170
        r, t = box(bx, log_y + 25, 145, 45, label, sf, sc, 9, 2)
        all_els.extend([r, t])
        if idx < len(log_comps) - 1:
            all_els.append(arrow(bx + 145, log_y + 47, bx + 170, log_y + 47, sc, 1))

    # JWT payload
    jwt_y = log_y + 100
    all_els.append(text(x0 + 20, jwt_y, "JWT Payload:", 11, 200, 16, C_BLACK, "left", "top"))
    jwt_r, jwt_t = box(x0 + 30, jwt_y + 20, 300, 70, "sub: email\nrole: student|faculty|admin\nexp: timestamp", C_LIGHT_RED, C_AUTH, 10, 2)
    all_els.extend([jwt_r, jwt_t])

    # Key note
    note_y2 = jwt_y + 110
    all_els.append(text(x0 + 20, note_y2, "⚠ CRITICAL: Auth is built but NOT enforced on any route.", 11, 450, 18, C_AUTH, "left", "top"))
    all_els.append(text(x0 + 20, note_y2 + 20, "get_current_user and require_role() dependencies exist but no route uses Depends().", 10, 500, 16, C_GRAY, "left", "top"))
    all_els.append(text(x0 + 20, note_y2 + 38, "Roles: student, faculty, admin (defined in auth.py VALID_ROLES)", 10, 400, 16, C_GRAY, "left", "top"))


    # ============ DIAGRAM 7: State Management ============
    x0, y0 = 1100, 1300
    all_els.extend(diagram_title(x0, y0, "7. State Management", "Frontend state: local React state + localStorage"))
    yr = y0 + 50

    # React state box
    rr1, rt1 = box(x0 + 30, yr, 280, 100, "React Local State\nuseState() + useEffect()\n- Chat messages\n- Quiz answers\n- Flashcard flip state\n- Form inputs", C_LIGHT_PURP, C_FRONTEND, 10, 2)
    all_els.extend([rr1, rt1])

    # localStorage box
    rr2, rt2 = box(x0 + 380, yr, 280, 100, "localStorage\n- enrolled_BAECE102\n- last_question_*\n- session_id\n- Chat history cache", C_LIGHT_AMBR, C_LLM, 10, 2)
    all_els.extend([rr2, rt2])

    # API fetch
    rr3, rt3 = box(x0 + 200, yr + 140, 280, 80, "API Fetch (real-time)\n- All data fetched fresh\n  on mount via GET endpoints\n- No global state store\n- No Redux / Context", C_LIGHT_BLUE, C_BACKEND, 10, 2)
    all_els.extend([rr3, rt3])

    # Arrows
    all_els.append(arrow(x0 + 310, yr + 50, x0 + 380, yr + 50, C_FRONTEND, 1, "dashed"))
    all_els.append(arrow(x0 + 340, yr + 100, x0 + 340, yr + 140, C_LLM, 1, "dashed"))

    all_els.append(text(x0 + 30, yr + 250, "No global state store. No React Context. No Redux. State is local to each page component.", 10, 500, 16, C_GRAY, "left", "top"))


    # ============ DIAGRAM 8: Sequence — Student Query ============
    x0, y0 = 100, 2420
    all_els.extend(diagram_title(x0, y0, "8. Sequence: Student Query (SSE Streaming)", "End-to-end flow for a student asking a question"))
    yr = y0 + 50

    participants = [
        ("Student\n(Browser)", 0, C_FRONTEND),
        ("Frontend\nNext.js", 1, C_FRONTEND),
        ("POST\n/query-stream", 2, C_BACKEND),
        ("Gatekeeper\n(relevance)", 3, C_ROUTER),
        ("RAG Pipeline\n(retrieve)", 4, C_DB),
        ("OpenRouter\n(LLM)", 5, C_EXTERNAL),
        ("Verifier\n(grounding)", 6, C_SERVICE),
    ]
    lane_w = 120
    lane_gap = 10
    lane_start = x0 + 30
    lanes = {}
    for name, idx, clr in participants:
        bx = lane_start + idx * (lane_w + lane_gap)
        r, t = box(bx, yr, lane_w, 40, name, C_WHITE, clr, 9, 2)
        all_els.extend([r, t])
        lanes[idx] = (bx + lane_w/2, bx, bx + lane_w)

    # Vertical lanes (dashed lines)
    for idx, (cx, lx, rx) in lanes.items():
        if idx > 0:
            lx2 = lx - lane_gap/2
            all_els.append(line([[lx2, yr + 40], [lx2, yr + 600]], C_GRAY, 1, "dashed"))

    # Sequence arrows with labels
    seq_y = yr + 60
    step = 45

    # 1. User types question → POST
    s1 = seq_y
    all_els.append(arrow(lanes[0][0], s1, lanes[2][0], s1, C_FRONTEND, 1.5))
    all_els.append(text(lane_start + lane_w + 10, s1 - 12, "Ask question", 9, 150, 14, C_BLACK, "left", "top"))

    # 2. POST /query-stream → Gatekeeper
    s2 = seq_y + step
    all_els.append(arrow(lanes[2][0], s2, lanes[3][0], s2, C_BACKEND, 1.5))
    all_els.append(text(lanes[2][0] + 20, s2 - 12, "Forward query", 9, 100, 14, C_BLACK, "left", "top"))

    # 3. Gatekeeper → returns relevant/enriched
    s3 = seq_y + 2*step
    all_els.append(arrow(lanes[3][0], s3, lanes[2][0], s3, C_ROUTER, 1.5))
    all_els.append(text(lanes[3][0] + 10, s3 - 12, "relevant + enriched", 9, 120, 14, C_BLACK, "left", "top"))

    # 4. POST → RAG retrieve
    s4 = seq_y + 3*step
    all_els.append(arrow(lanes[2][0], s4, lanes[4][0], s4, C_BACKEND, 1.5))
    all_els.append(text(lanes[2][0] + 20, s4 - 12, "retrieve chunks", 9, 100, 14, C_BLACK, "left", "top"))

    # 5. RAG → LLM (embed query + hybrid search)
    s5 = seq_y + 4*step
    all_els.append(arrow(lanes[4][0], s5, lanes[5][0], s5, C_DB, 1.5))
    all_els.append(text(lanes[4][0] + 10, s5 - 12, "embed + search", 9, 100, 14, C_BLACK, "left", "top"))

    # 6. LLM → embeddings back
    s6 = seq_y + 5*step
    all_els.append(arrow(lanes[5][0], s6, lanes[4][0], s6, C_EXTERNAL, 1.5))
    all_els.append(text(lanes[5][0] + 10, s6 - 12, "embeddings", 9, 80, 14, C_BLACK, "left", "top"))

    # 7. RAG returns chunks
    s7 = seq_y + 6*step
    all_els.append(arrow(lanes[4][0], s7, lanes[2][0], s7, C_DB, 1.5))

    # 8. Build prompt → LLM
    s8 = seq_y + 7*step
    all_els.append(arrow(lanes[2][0], s8, lanes[5][0], s8, C_BACKEND, 1.5))
    all_els.append(text(lanes[2][0] + 20, s8 - 12, "build prompt → LLM", 9, 120, 14, C_BLACK, "left", "top"))

    # 9. LLM streaming response
    s9 = seq_y + 8*step
    llm_end = lanes[5][2]
    router_l = lanes[2][2]
    all_els.append(arrow(lanes[5][0], s9, lanes[2][0], s9, C_EXTERNAL, 1.5))
    all_els.append(text(lanes[5][0] + 10, s9 - 12, "SSE stream", 9, 80, 14, C_BLACK, "left", "top"))

    # 10. Verifier check
    s10 = seq_y + 9*step
    all_els.append(arrow(lanes[2][0], s10, lanes[6][0], s10, C_BACKEND, 1.5, "dashed"))
    all_els.append(text(lanes[2][0] + 20, s10 - 12, "verify grounding", 9, 100, 14, C_BLACK, "left", "top"))

    # 11. Verifier result back
    s11 = seq_y + 10*step
    all_els.append(arrow(lanes[6][0], s11, lanes[2][0], s11, C_SERVICE, 1.5, "dashed"))

    # 12. Stream response to frontend
    s12 = seq_y + 11*step
    all_els.append(arrow(lanes[2][0], s12, lanes[1][0], s12, C_BACKEND, 1.5))
    all_els.append(text(lanes[2][0] + 10, s12 - 12, "SSE data chunks", 9, 100, 14, C_BLACK, "left", "top"))

    # 13. Update UI
    s13 = seq_y + 12*step
    all_els.append(arrow(lanes[1][0], s13, lanes[0][0], s13, C_FRONTEND, 1.5))
    all_els.append(text(lanes[1][0] + 10, s13 - 12, "render response", 9, 100, 14, C_BLACK, "left", "top"))


    # ============ DIAGRAM 9: Sequence — PDF Upload ============
    x0, y0 = 100, 3080
    all_els.extend(diagram_title(x0, y0, "9. Sequence: Faculty Uploads PDF", "End-to-end flow for ingesting a PDF document"))
    yr = y0 + 50

    parts = [
        ("Faculty\n(Browser)", 0, C_EXTERNAL),
        ("POST\n/ingest", 1, C_BACKEND),
        ("SHA-256\nDedup", 2, C_DB),
        ("PDF\nExtractor", 3, C_ROUTER),
        ("Chunker\n(tiktoken)", 4, C_SERVICE),
        ("OpenRouter\n(embeddings)", 5, C_EXTERNAL),
        ("SurrealDB\n(storage)", 6, C_DB),
    ]
    for name, idx, clr in parts:
        bx = lane_start + idx * (lane_w + lane_gap)
        r, t = box(bx, yr, lane_w, 40, name, C_WHITE, clr, 8, 2)
        all_els.extend([r, t])
        p_lanes = {}
        p_lanes[idx] = (bx + lane_w/2, bx, bx + lane_w)

    # Vertical lane lines
    for idx in range(1, len(parts)):
        lx2 = lane_start + idx * (lane_w + lane_gap) - lane_gap/2
        all_els.append(line([[lx2, yr + 40], [lx2, yr + 520]], C_GRAY, 1, "dashed"))

    def p_lane_center(idx):
        return lane_start + idx * (lane_w + lane_gap) + lane_w/2

    s1 = yr + 60
    all_els.append(arrow(p_lane_center(0), s1, p_lane_center(1), s1, C_EXTERNAL, 1.5))
    all_els.append(text(lane_start + lane_w + 10, s1 - 12, "Upload PDF file", 9, 120, 14, C_BLACK, "left", "top"))

    s2 = yr + 60 + step
    all_els.append(arrow(p_lane_center(1), s2, p_lane_center(2), s2, C_BACKEND, 1.5))
    all_els.append(text(p_lane_center(1) + 10, s2 - 12, "check hash", 9, 80, 14, C_BLACK, "left", "top"))

    s3 = yr + 60 + 2*step
    all_els.append(arrow(p_lane_center(2), s3, p_lane_center(1), s3, C_DB, 1.5))
    all_els.append(text(p_lane_center(2) + 10, s3 - 12, "new document", 9, 90, 14, C_BLACK, "left", "top"))

    s4 = yr + 60 + 3*step
    all_els.append(arrow(p_lane_center(1), s4, p_lane_center(3), s4, C_BACKEND, 1.5))
    all_els.append(text(p_lane_center(1) + 10, s4 - 12, "extract pages", 9, 90, 14, C_BLACK, "left", "top"))

    s5 = yr + 60 + 4*step
    all_els.append(arrow(p_lane_center(3), s5, p_lane_center(4), s5, C_ROUTER, 1.5))
    all_els.append(text(p_lane_center(3) + 10, s5 - 12, "text chunks", 9, 80, 14, C_BLACK, "left", "top"))

    s6 = yr + 60 + 5*step
    all_els.append(arrow(p_lane_center(4), s6, p_lane_center(5), s6, C_SERVICE, 1.5))
    all_els.append(text(p_lane_center(4) + 10, s6 - 12, "embed batch", 9, 80, 14, C_BLACK, "left", "top"))

    s7 = yr + 60 + 6*step
    all_els.append(arrow(p_lane_center(5), s7, p_lane_center(4), s7, C_EXTERNAL, 1.5))
    all_els.append(text(p_lane_center(5) + 10, s7 - 12, "embeddings", 9, 80, 14, C_BLACK, "left", "top"))

    s8 = yr + 60 + 7*step
    all_els.append(arrow(p_lane_center(4), s8, p_lane_center(6), s8, C_SERVICE, 1.5))
    all_els.append(text(p_lane_center(4) + 10, s8 - 12, "store chunks", 9, 80, 14, C_BLACK, "left", "top"))

    s9 = yr + 60 + 8*step
    all_els.append(arrow(p_lane_center(3), s5, p_lane_center(5), s5, C_ROUTER, 1.5))
    all_els.append(text(p_lane_center(3) + 10, s5 - 12, "image chunks", 9, 80, 14, C_BLACK, "left", "top"))
    # Actually let me fix this - I'm reusing s5. Let me add a separate image flow
    s_img = yr + 60 + 5*step + 25
    all_els.append(arrow(p_lane_center(3), s_img, p_lane_center(5), s_img, C_ROUTER, 1.5, "dashed"))
    all_els.append(text(p_lane_center(3) + 10, s_img - 12, "image embed", 9, 80, 14, C_BLACK, "left", "top"))

    s10 = yr + 60 + 9*step
    all_els.append(arrow(p_lane_center(6), s10, p_lane_center(1), s10, C_DB, 1.5))
    all_els.append(text(p_lane_center(6) + 10, s10 - 12, "ingestion complete", 9, 110, 14, C_BLACK, "left", "top"))

    s11 = yr + 60 + 10*step
    all_els.append(arrow(p_lane_center(1), s11, p_lane_center(0), s11, C_BACKEND, 1.5))
    all_els.append(text(p_lane_center(1) + 10, s11 - 12, "success response", 9, 100, 14, C_BLACK, "left", "top"))


    # ============ DIAGRAM 10: Folder Structure ============
    x0, y0 = 100, 3700
    all_els.extend(diagram_title(x0, y0, "10. Folder / Module Structure", "Repository layout with key file annotations"))
    yr = y0 + 50

    # Tree structure as nested text with lines
    tree_lines = [
        (0, "📁 adaptive_learning/", True, C_BLACK),
        (1, "📁 backend/", True, C_BACKEND),
        (2, "📄 server.py           — FastAPI entry, lifespan, middleware, 9 routers", False, C_BLACK),
        (2, "📁 app/", True, C_BACKEND),
        (3, "📁 routers/", True, C_ROUTER),
        (4, "📄 __init__.py", False, C_GRAY),
        (4, "📄 query.py            — /health, /query, /query-stream, /stats, /chunks", False, C_BLACK),
        (4, "📄 courses.py          — CRUD /courses + /curriculum/topics", False, C_BLACK),
        (4, "📄 analytics.py        — /analytics, /unanswered, /coverage, /questions", False, C_BLACK),
        (4, "📄 chat.py             — /chat-history CRUD", False, C_BLACK),
        (4, "📄 ingestion.py        — /ingest (PDF upload), /curriculum upload", False, C_BLACK),
        (4, "📄 flashcards.py       — /flashcards generate + save", False, C_BLACK),
        (4, "📄 quiz.py             — /quiz generate + save", False, C_BLACK),
        (4, "📄 paper.py            — /generate-paper", False, C_BLACK),
        (4, "📄 auth.py             — /auth/register, /auth/login", False, C_AUTH),
        (3, "📄 rag.py              — RAGPipeline: ingest, retrieve, hybrid search (BM25+vector+RRF)", False, C_BLACK),
        (3, "📄 query_engine.py     — QueryEngine: prompt builder, context window, orchestration", False, C_BLACK),
        (3, "📄 openrouter.py       — OpenRouterClient: LLM, embeddings, streaming singleton", False, C_EXTERNAL),
        (3, "📄 db.py               — SurrealDBManager: singleton, schema init, 10 tables", False, C_DB),
        (3, "📄 curriculum.py       — CurriculumManager: upload, topics, relevance check", False, C_DB),
        (3, "📄 analytics.py        — Query analytics: top questions, weak topics, coverage", False, C_DB),
        (3, "📄 courses.py          — Course CRUD logic with cascade delete", False, C_BLACK),
        (3, "📄 chat_history.py     — Chat message persistence", False, C_BLACK),
        (3, "📄 saved_content.py    — Flashcard + quiz persistence", False, C_BLACK),
        (3, "📄 paper_generator.py  — Question paper with Bloom's taxonomy", False, C_BLACK),
        (3, "📄 chunker.py          — Text chunking (tiktoken, sentence-aware, 512 tokens)", False, C_SERVICE),
        (3, "📄 citation.py         — Citation parsing, validation, uncited claim removal", False, C_SERVICE),
        (3, "📄 gatekeeper.py       — Pre-query: relevance check + query enrichment", False, C_SERVICE),
        (3, "📄 verifier.py         — Post-answer: grounding verification", False, C_SERVICE),
        (3, "📄 pdf_extractor.py    — PDF text + image extraction with magic byte validation", False, C_SERVICE),
        (3, "📄 evaluator.py        — RAGAS-style evaluation (faithfulness, relevancy, precision, recall)", False, C_SERVICE),
        (3, "📄 auth.py             — JWT helpers, bcrypt hashing, get_current_user dependency", False, C_AUTH),
        (3, "📄 validation.py       — Input sanitizers, prompt injection detection, size limits", False, C_AUTH),
        (3, "📄 config.py           — All env settings, @lru_cache singleton", False, C_BLACK),
        (3, "📄 schemas.py          — Pydantic models for request/response", False, C_BLACK),
        (3, "📄 deps.py             — FastAPI dependency injection getters", False, C_BLACK),
        (2, "📄 requirements.txt    — Python dependencies", False, C_GRAY),
        (2, "📄 Dockerfile          — Backend container build", False, C_GRAY),
        (2, "📁 tests/", True, C_GRAY),
        (1, "📁 new_frontend/", True, C_FRONTEND),
        (2, "📁 src/", True, C_FRONTEND),
        (3, "📁 app/                — Pages: /, /dashboard, /chat, /courses, /progress, /quiz, /flashcards, /faculty/*, /admin", False, C_BLACK),
        (3, "📁 lib/", True, C_FRONTEND),
        (4, "📄 mockData.js         — All mock data for the prototype", False, C_GRAY),
        (3, "📁 app/components/     — 19 reusable UI components (AppShell, Sidebar, DataTable, etc.)", False, C_BLACK),
        (1, "📄 docker-compose.yml  — 4 services: surrealdb + backend + frontend + postgres (unused)", False, C_GRAY),
        (1, "📄 SPEC.md             — Original MVP specification (partially outdated)", False, C_GRAY),
        (1, "📄 README.md           — Run instructions", False, C_GRAY),
        (1, "📄 REPOSITORY_AUDIT_REPORT.md — Multi-agent audit report", False, C_GRAY),
    ]

    indent = 20
    line_h = 16
    for level, label, is_bold, color in tree_lines:
        tx = x0 + 30 + level * 20
        ty = yr + level * 2 + (tree_lines.index((level, label, is_bold, color))) * line_h
        # Actually compute position by index
        idx = tree_lines.index((level, label, is_bold, color))
        ty = yr + idx * (line_h)
        fs = 10 if level > 1 else 11
        ft = 2 if is_bold else 1
        all_els.append(text(x0 + 30 + level * 20, ty, label, fs, 900, line_h, color, "left", "top", ft))


    return all_els


def generate_file():
    elements = build_diagrams()

    # Calculate canvas bounds
    max_x = 0
    max_y = 0
    for el in elements:
        ex = el.get("x", 0) + el.get("width", 0)
        ey = el.get("y", 0) + el.get("height", 0)
        max_x = max(max_x, ex)
        max_y = max(max_y, ey)

    canvas_w = max(int(max_x * 1.1), 1500)
    canvas_h = max(int(max_y * 1.1), 2000)

    doc = {
        "type": "excalidraw",
        "version": 2,
        "source": "script",
        "elements": elements,
        "appState": {
            "gridSize": None,
            "viewBackgroundColor": "#ffffff",
            "zenModeEnabled": False,
            "zoom": {
                "value": 0.8
            },
            "offset": {
                "x": 0,
                "y": 0
            },
            "scrollX": 0,
            "scrollY": 0,
            "width": canvas_w,
            "height": canvas_h,
        }
    }

    output_path = "/home/krishna/coding/adaptive_learning/dont touch/docs/diagrams/all-diagrams.excalidraw"
    with open(output_path, "w") as f:
        json.dump(doc, f, indent=2)

    print(f"Generated Excalidraw file: {output_path}")
    print(f"  Elements: {len(elements)}")
    print(f"  Canvas: {canvas_w} x {canvas_h}")


if __name__ == "__main__":
    generate_file()
