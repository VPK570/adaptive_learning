from collections import Counter
from datetime import date, datetime, timedelta

from app.db import SurrealDBManager
from app.topics import get_topic_coverage
from app.validation import (
    MAX_QUESTION_LENGTH,
    sanitize_text,
    validate_course_code,
)


def _compute_streak(days: list[date]) -> int:
    """Length of trailing run of consecutive dates (deduped, caller-normalized to UTC date)."""
    unique = sorted({d for d in days if d is not None})
    if not unique:
        return 0
    streak, ref = 1, unique[-1]
    for d in reversed(unique[:-1]):
        if ref - d == timedelta(days=1):
            streak += 1
            ref = d
        else:
            break
    return streak


async def get_course_mastery(user_email: str, course_code: str) -> float:
    db = await SurrealDBManager.get_db()
    rows = await db.query(
        "SELECT mastery_score FROM knowledge_state WHERE student_id = $sid AND course_code = $cc",
        {"sid": user_email, "cc": course_code},
    )
    if not rows:
        return 0.0
    return round(sum(r.get("mastery_score", 0.0) for r in rows) / len(rows), 3)


async def get_student_stats(user_email: str) -> dict:
    db = await SurrealDBManager.get_db()
    courses_res = await db.query("SELECT * FROM course ORDER BY created_at DESC")
    course_codes = [r["course_code"] for r in courses_res] if courses_res else []

    course_stats = []
    total_quizzes = 0
    for cc in course_codes:
        mastery = await get_course_mastery(user_email, cc)
        quiz_res = await db.query(
            "SELECT count() AS cnt FROM quiz WHERE user_id = $uid AND course_code = $cc GROUP ALL",
            {"uid": user_email, "cc": cc},
        )
        quizzes = quiz_res[0]["cnt"] if quiz_res else 0
        total_quizzes += quizzes
        course_stats.append({"course_code": cc, "overall_mastery": mastery, "quizzes_taken": quizzes})

    activity_dates: list[date] = []
    for table, col in (("query_log", "user_id"), ("question_log", "student_id")):
        res = await db.query(f"SELECT timestamp FROM {table} WHERE {col} = $uid", {"uid": user_email})
        for r in res or []:
            ts = r.get("timestamp")
            if ts:
                try:
                    activity_dates.append(datetime.fromisoformat(str(ts).replace("Z", "+00:00")).date())
                except (ValueError, TypeError):
                    pass

    return {
        "courses": course_stats,
        "total_quizzes": total_quizzes,
        "current_streak": _compute_streak(activity_dates),
        "active_days": len({d for d in activity_dates}),
    }


async def get_student_course_map(user_email: str, course_code: str) -> dict:
    from app.knowledge_state import KnowledgeStateManager
    from app.learning_path import TopicPrerequisiteGraph
    from app.topics import get_course_topics

    ksm = KnowledgeStateManager()
    states = await ksm.get_student_course_states(user_email, course_code)

    topic_mastery: dict[str, float] = {}
    topic_attempts: dict[str, int] = {}
    for s in states:
        tid = s.get("topic_id", "")
        if tid:
            # max, not weighted — matches ZPD candidate logic (learning_path.py:31);
            # can overstate mastery on partially-attempted topics
            topic_mastery[tid] = max(topic_mastery.get(tid, 0.0), s.get("mastery_score", 0.0))
            topic_attempts[tid] = topic_attempts.get(tid, 0) + (s.get("total_attempts", 0) or 0)

    topic_list = []
    for t in await get_course_topics(course_code):
        name = t["topic_name"]
        mastery = round(topic_mastery.get(name, 0.0), 3)
        status = "mastered" if mastery >= 0.7 else "in_progress" if mastery > 0 else "not_started"
        topic_list.append({
            "topic_id": name,
            "topic_name": name,
            "mastery_score": mastery,
            "bloom_level": t.get("bloom_level", "Remember"),
            "prerequisites": t.get("prerequisites", []),
            "status": status,
            "attempts": topic_attempts.get(name, 0),
        })

    graph = TopicPrerequisiteGraph()
    candidates = await graph.get_zpd_candidates(user_email, course_code)
    if not candidates:
        # ponytail: no prereq graph — fall back to lowest-mastery unmastered topics
        not_mastered = sorted(
            (t for t in topic_list if t["status"] != "mastered"),
            key=lambda t: t["mastery_score"],
        )
        candidates = [{"topic_id": t["topic_name"], "priority": 1.0} for t in not_mastered[:5]]

    return {
        "course_code": course_code,
        "overall_mastery": await get_course_mastery(user_email, course_code),
        "topics": topic_list,
        "next": candidates,
    }


async def log_query(
    question: str,
    course_code: str,
    response: str,
    cited_sources: list = None,
    user_id: str = "",
):
    course_code = validate_course_code(course_code)
    question = sanitize_text(question, MAX_QUESTION_LENGTH)

    refusal_phrase = "This topic is not covered"
    out_of_scope = refusal_phrase in response

    db = await SurrealDBManager.get_db()
    await db.query(
        "CREATE query_log CONTENT { user_id: $uid, course_code: $code, question: $q, response_preview: $preview, out_of_scope: $oos, cited_sources: $sources }",
        {
            "uid": user_id,
            "code": course_code,
            "q": question,
            "preview": response[:200],
            "oos": out_of_scope,
            "sources": cited_sources or [],
        },
    )


async def get_unanswered_questions(course_code: str):
    course_code = validate_course_code(course_code)
    db = await SurrealDBManager.get_db()
    result = await db.query(
        "SELECT * FROM query_log WHERE course_code = $code AND out_of_scope = true ORDER BY timestamp DESC",
        {"code": course_code},
    )
    rows = result if result else []
    return [
        {
            "id": str(r["id"]),
            "course_code": r["course_code"],
            "question": r["question"],
            "timestamp": str(r.get("timestamp")) if r.get("timestamp") else None,
            "out_of_scope": r.get("out_of_scope", False),
        }
        for r in rows
    ]


async def get_coverage(course_code: str):
    course_code = validate_course_code(course_code)
    db = await SurrealDBManager.get_db()
    result = await db.query(
        "SELECT cited_sources FROM query_log WHERE course_code = $code",
        {"code": course_code},
    )
    rows = result if result else []
    doc_hits = {}
    for r in rows:
        sources = r.get("cited_sources") or []
        for src in sources:
            title = src.get("source_title") if isinstance(src, dict) else str(src)
            if title:
                doc_hits[title] = doc_hits.get(title, 0) + 1
    return doc_hits


async def _compute_topic_insights(course_code: str, course_logs: list) -> dict:
    db = await SurrealDBManager.get_db()
    syllabus_topics = []
    try:
        topics_res = await db.query(
            "SELECT topic_name FROM course_topic WHERE course_code = $code",
            {"code": course_code},
        )
        syllabus_topics = [r["topic_name"] for r in (topics_res if topics_res else [])]
    except Exception:
        pass

    coverage = await get_topic_coverage(course_code)
    coverage_map = {t["topic_name"]: t for t in coverage.get("topics", [])}

    topic_hits = {}
    for topic in syllabus_topics:
        hits = sum(1 for log in course_logs if topic.lower() in log.get("question", "").lower())
        topic_hits[topic] = hits

    weak = []
    revision = []
    for topic in syllabus_topics:
        info = coverage_map.get(topic, {})
        has_chunks = info.get("status") == "covered"
        hits = topic_hits.get(topic, 0)
        if hits == 0 and not has_chunks:
            revision.append(topic)
        elif 0 < hits < 2 and not has_chunks:
            weak.append(topic)

    return {
        "weak_topics": weak,
        "suggested_revision": revision,
        "topic_coverage": coverage.get("topics", []),
    }


async def get_analytics(course_code: str):
    course_code = validate_course_code(course_code)
    db = await SurrealDBManager.get_db()
    result = await db.query(
        "SELECT * FROM query_log WHERE course_code = $code ORDER BY timestamp DESC",
        {"code": course_code},
    )
    rows = result if result else []
    course_logs = rows

    questions = [row["question"] for row in course_logs]
    top_questions = Counter(questions).most_common(10)

    dates = []
    for row in course_logs:
        ts = row.get("timestamp")
        if ts:
            try:
                dates.append(datetime.fromisoformat(str(ts).replace("Z", "+00:00")).strftime("%Y-%m-%d"))
            except (ValueError, TypeError):
                pass
    questions_per_day = dict(Counter(dates))

    recent = sorted(course_logs, key=lambda x: x.get("timestamp") or "", reverse=True)[:10]

    insights = await _compute_topic_insights(course_code, course_logs)

    return {
        "top_questions": [{"question": q, "count": c} for q, c in top_questions],
        "questions_per_day": questions_per_day,
        "weak_topics": insights["weak_topics"],
        "suggested_revision": insights["suggested_revision"],
        "topic_coverage": insights["topic_coverage"],
        "recent_questions": [
            {
                "id": str(r["id"]),
                "course_code": r["course_code"],
                "question": r["question"],
                "timestamp": str(r.get("timestamp")) if r.get("timestamp") else None,
                "out_of_scope": r.get("out_of_scope", False),
            }
            for r in recent
        ],
    }


async def get_student_bloom_mastery(student_id: str, course_code: str) -> dict:
    db = await SurrealDBManager.get_db()
    rows = await db.query(
        "SELECT bloom_level, mastery_score FROM knowledge_state WHERE student_id = $sid AND course_code = $cc",
        {"sid": student_id, "cc": course_code},
    )
    return {r["bloom_level"]: r["mastery_score"] for r in (rows or [])}


async def get_my_analytics(user_email: str, course_code: str):
    course_code = validate_course_code(course_code)
    db = await SurrealDBManager.get_db()
    result = await db.query(
        "SELECT * FROM query_log WHERE course_code = $code AND user_id = $uid ORDER BY timestamp DESC",
        {"code": course_code, "uid": user_email},
    )
    rows = result if result else []
    course_logs = rows

    questions = [row["question"] for row in course_logs]
    top_questions = Counter(questions).most_common(10)

    dates = []
    for row in course_logs:
        ts = row.get("timestamp")
        if ts:
            try:
                dates.append(datetime.fromisoformat(str(ts).replace("Z", "+00:00")).strftime("%Y-%m-%d"))
            except (ValueError, TypeError):
                pass
    questions_per_day = dict(Counter(dates))

    recent = sorted(course_logs, key=lambda x: x.get("timestamp") or "", reverse=True)[:10]

    insights = await _compute_topic_insights(course_code, course_logs)
    bloom_mastery = await get_student_bloom_mastery(user_email, course_code)

    return {
        "top_questions": [{"question": q, "count": c} for q, c in top_questions],
        "questions_per_day": questions_per_day,
        "weak_topics": insights["weak_topics"],
        "suggested_revision": insights["suggested_revision"],
        "topic_coverage": insights["topic_coverage"],
        "bloom_mastery": bloom_mastery,
        "recent_questions": [
            {
                "id": str(r["id"]),
                "course_code": r["course_code"],
                "question": r["question"],
                "timestamp": str(r.get("timestamp")) if r.get("timestamp") else None,
                "out_of_scope": r.get("out_of_scope", False),
            }
            for r in recent
        ],
    }


async def get_all_questions(course_code: str):
    course_code = validate_course_code(course_code)
    db = await SurrealDBManager.get_db()
    result = await db.query(
        "SELECT * FROM query_log WHERE course_code = $code ORDER BY timestamp DESC",
        {"code": course_code},
    )
    rows = result if result else []
    return [
        {
            "id": str(r["id"]),
            "course_code": r["course_code"],
            "question": r["question"],
            "timestamp": str(r.get("timestamp")) if r.get("timestamp") else None,
            "out_of_scope": r.get("out_of_scope", False),
        }
        for r in rows
    ]
