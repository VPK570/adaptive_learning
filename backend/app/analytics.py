from collections import Counter
from datetime import datetime

from app.validation import (
    validate_course_code,
    sanitize_text,
    MAX_QUESTION_LENGTH,
)
from app.database import Database
from app.stores.analytics_store import AnalyticsStore


async def log_query(
    question: str,
    course_code: str,
    response: str,
    cited_sources: list = None,
):
    course_code = validate_course_code(course_code)
    question = sanitize_text(question, MAX_QUESTION_LENGTH)

    async with Database.session() as session:
        store = AnalyticsStore(session)
        await store.log_query(question, course_code, response, cited_sources)


async def get_unanswered_questions(course_code: str):
    course_code = validate_course_code(course_code)
    async with Database.session() as session:
        store = AnalyticsStore(session)
        logs = await store.get_unanswered(course_code)
        return [
            {
                "id": str(l.id),
                "course_code": l.course_code,
                "question": l.question,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
                "out_of_scope": l.out_of_scope,
            }
            for l in logs
        ]


async def get_coverage(course_code: str):
    course_code = validate_course_code(course_code)
    async with Database.session() as session:
        store = AnalyticsStore(session)
        return await store.get_coverage(course_code)


async def get_analytics(course_code: str):
    course_code = validate_course_code(course_code)
    async with Database.session() as session:
        store = AnalyticsStore(session)
        course_logs = await store.get_all_for_course(course_code)

        questions = [l.question for l in course_logs]
        top_questions = Counter(questions).most_common(10)

        dates = [l.timestamp.strftime("%Y-%m-%d") for l in course_logs if l.timestamp]
        questions_per_day = dict(Counter(dates))

        recent = sorted(course_logs, key=lambda x: x.timestamp or datetime.min, reverse=True)[:10]

    # Get topics from SurrealDB (RAG vector store — stays there)
    try:
        from app.db import get_db as get_surreal_db
        sdb = await get_surreal_db()
        topics_res = await sdb.query(
            "SELECT topic FROM (SELECT topic FROM text_chunk WHERE course_code = $code) GROUP BY topic",
            {"code": course_code}
        )
        curriculum_topics = [r["topic"] for r in (topics_res if topics_res else []) if r.get("topic")]
    except Exception:
        curriculum_topics = []

    # Topic engagement analytics
    topic_hits = {}
    for topic in curriculum_topics:
        hits = sum(1 for log in course_logs if topic.lower() in log.question.lower())
        topic_hits[topic] = hits

    weak_topics = [t for t, h in topic_hits.items() if 0 < h < 2]
    suggested_revision = [t for t, h in topic_hits.items() if h == 0]

    return {
        "top_questions": [{"question": q, "count": c} for q, c in top_questions],
        "questions_per_day": questions_per_day,
        "weak_topics": weak_topics,
        "suggested_revision": suggested_revision,
        "recent_questions": [
            {
                "id": str(l.id),
                "course_code": l.course_code,
                "question": l.question,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
                "out_of_scope": l.out_of_scope,
            }
            for l in recent
        ],
    }


async def get_all_questions(course_code: str):
    course_code = validate_course_code(course_code)
    async with Database.session() as session:
        store = AnalyticsStore(session)
        logs = await store.get_all_for_course(course_code)
        return [
            {
                "id": str(l.id),
                "course_code": l.course_code,
                "question": l.question,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
                "out_of_scope": l.out_of_scope,
            }
            for l in logs
        ]
