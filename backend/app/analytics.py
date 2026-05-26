import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from app.validation import (
    validate_course_code,
    sanitize_text,
    MAX_QUESTION_LENGTH,
)
from app.curriculum import CurriculumManager

LOG_FILE = Path(__file__).parent.parent / "storage" / "query_log.json"

curriculum = CurriculumManager()


def _load_logs():
    if not LOG_FILE.exists():
        return []

    try:
        with LOG_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_logs(logs):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with LOG_FILE.open("w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)


def log_query(
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

    logs = _load_logs()
    logs.append(log_entry)

    _save_logs(logs)


def get_unanswered_questions(course_code: str):
    course_code = validate_course_code(course_code)

    logs = _load_logs()

    return [
        log
        for log in logs
        if log.get("course_code") == course_code
        and log.get("out_of_scope", False)
    ]


def get_coverage(course_code: str):
    course_code = validate_course_code(course_code)

    logs = _load_logs()

    course_logs = [
        log for log in logs
        if log.get("course_code") == course_code
    ]

    doc_hits = {}

    for log in course_logs:
        for src in log.get("cited_sources", []):
            if isinstance(src, dict):
                title = src.get("source_title")
            else:
                title = str(src)

            if title:
                doc_hits[title] = doc_hits.get(title, 0) + 1

    return doc_hits


def get_analytics(course_code: str):
    course_code = validate_course_code(course_code)

    logs = _load_logs()

    course_logs = [
        log for log in logs
        if log.get("course_code") == course_code
    ]

    curriculum_topics = curriculum.get_curriculum_topics(course_code)

    topic_hits = {}

    for topic in curriculum_topics:
        hits = sum(
            1
            for log in course_logs
            if topic.lower() in log["question"].lower()
        )
        topic_hits[topic] = hits

    weak_topics = [t for t, h in topic_hits.items() if 0 < h < 2]
    suggested_revision = [t for t, h in topic_hits.items() if h == 0]

    questions = [log["question"] for log in course_logs]
    top_questions = Counter(questions).most_common(10)

    dates = [
        log["timestamp"].split("T")[0]
        for log in course_logs
    ]
    questions_per_day = dict(Counter(dates))

    recent_questions = sorted(
        course_logs,
        key=lambda x: x["timestamp"],
        reverse=True,
    )[:10]

    return {
        "top_questions": [
            {"question": q, "count": c}
            for q, c in top_questions
        ],
        "questions_per_day": questions_per_day,
        "weak_topics": weak_topics,
        "suggested_revision": suggested_revision,
        "recent_questions": recent_questions,
    }


def get_all_questions(course_code: str):
    course_code = validate_course_code(course_code)

    logs = _load_logs()

    return [
        log for log in logs
        if log.get("course_code") == course_code
    ]