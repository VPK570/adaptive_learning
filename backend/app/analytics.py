from collections import Counter
from datetime import datetime
from app.validation import (
    validate_course_code,
    sanitize_text,
    MAX_QUESTION_LENGTH,
)
from app.db import get_db

async def log_query(
    question: str,
    course_code: str,
    response: str,
    cited_sources: list = None,
):
    course_code = validate_course_code(course_code)
    question = sanitize_text(question, MAX_QUESTION_LENGTH)

    refusal_phrase = "This topic is not covered"
    out_of_scope = refusal_phrase in response

    log_entry = {
        "question": question,
        "course_code": course_code,
        "timestamp": datetime.now().isoformat(),
        "response_preview": response[:200],
        "out_of_scope": out_of_scope,
        "cited_sources": cited_sources or [],
    }

    db = await get_db()
    await db.query("CREATE query_log CONTENT $entry", {"entry": log_entry})


async def get_unanswered_questions(course_code: str):
    course_code = validate_course_code(course_code)
    db = await get_db()
    res = await db.query(
        "SELECT * FROM query_log WHERE course_code = $code AND out_of_scope = true",
        {"code": course_code}
    )
    return res[0]["result"] if res and res[0]["result"] else []


async def get_coverage(course_code: str):
    course_code = validate_course_code(course_code)
    db = await get_db()
    res = await db.query(
        "SELECT cited_sources FROM query_log WHERE course_code = $code",
        {"code": course_code}
    )
    
    doc_hits = {}
    if res and res[0]["result"]:
        for log in res[0]["result"]:
            for src in log.get("cited_sources", []):
                title = src.get("source_title") if isinstance(src, dict) else str(src)
                if title:
                    doc_hits[title] = doc_hits.get(title, 0) + 1
    return doc_hits


async def get_analytics(course_code: str):
    course_code = validate_course_code(course_code)
    db = await get_db()
    
    logs_res = await db.query("SELECT * FROM query_log WHERE course_code = $code", {"code": course_code})
    course_logs = logs_res[0]["result"] if logs_res and logs_res[0]["result"] else []

    # Get topics from curriculum chunks
    topics_res = await db.query("SELECT topic FROM (SELECT topic FROM text_chunk WHERE course_code = $code) GROUP BY topic", {"code": course_code})
    curriculum_topics = [r["topic"] for r in (topics_res[0]["result"] if topics_res else []) if r["topic"]]

    topic_hits = {}
    for topic in curriculum_topics:
        hits = sum(1 for log in course_logs if topic.lower() in log["question"].lower())
        topic_hits[topic] = hits

    weak_topics = [t for t, h in topic_hits.items() if 0 < h < 2]
    suggested_revision = [t for t, h in topic_hits.items() if h == 0]

    questions = [log["question"] for log in course_logs]
    top_questions = Counter(questions).most_common(10)

    dates = [log["timestamp"].split("T")[0] for log in course_logs]
    questions_per_day = dict(Counter(dates))

    recent_questions = sorted(course_logs, key=lambda x: x["timestamp"], reverse=True)[:10]

    return {
        "top_questions": [{"question": q, "count": c} for q, c in top_questions],
        "questions_per_day": questions_per_day,
        "weak_topics": weak_topics,
        "suggested_revision": suggested_revision,
        "recent_questions": recent_questions,
    }


async def get_all_questions(course_code: str):
    course_code = validate_course_code(course_code)
    db = await get_db()
    res = await db.query("SELECT * FROM query_log WHERE course_code = $code", {"code": course_code})
    return res[0]["result"] if res and res[0]["result"] else []
