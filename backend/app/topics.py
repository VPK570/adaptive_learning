import json
import logging
from typing import Any

from app.config import settings
from app.db import get_db
from app.openrouter import client
from app.validation import validate_course_code

logger = logging.getLogger(__name__)

TOPIC_EXTRACTION_PROMPT = """You are analyzing a course syllabus divided into modules. Each module contains multiple topics.

A topic is a specific concept, technique, or sub-theme listed under a module heading. Topics are typically separated by dashes (-), colons (:), or appear as standalone phrases before a colon. Do NOT use module headings ("Module:1", "Module:2" etc.) as topics — use the sub-items under them.

For each topic, extract:
- topic_name: The specific concept (not the module name)
- subtopics: Related sub-concepts or techniques under this topic
- prerequisites: Names of topics from earlier modules that this builds on (leave empty if unsure)
- bloom_level: The cognitive level: Remember, Understand, Apply, Analyze, Evaluate, Create. "Understand" is a safe default
- learning_objectives: What students should be able to do after learning this topic

Return the topics array inside a JSON object with key 'topics'. No explanation.

Syllabus:
"""

TOPIC_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "topics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic_name": {"type": "string"},
                    "subtopics": {"type": "array", "items": {"type": "string"}},
                    "prerequisites": {"type": "array", "items": {"type": "string"}},
                    "bloom_level": {"type": "string"},
                    "learning_objectives": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["topic_name"],
            },
        }
    },
    "required": ["topics"],
}


async def extract_topics_from_syllabus(syllabus_text: str) -> list[dict[str, Any]]:
    if not syllabus_text.strip():
        return []
    try:
        result = await client.chat_with_schema(
            messages=[
                {"role": "system", "content": "Extract structured topic outlines from syllabi."},
                {"role": "user", "content": TOPIC_EXTRACTION_PROMPT + syllabus_text},
            ],
            response_schema=TOPIC_EXTRACTION_SCHEMA,
            max_tokens=4096,
            model=settings.TOPIC_EXTRACTION_MODEL,
        )
        topics = result.get("topics", result.get(".topics", []))
        if not isinstance(topics, list):
            logger.warning("LLM returned non-list topics: %s", str(topics)[:200])
            return []
        logger.info("Extracted %d topics from syllabus", len(topics))
        return topics
    except Exception as e:
        logger.warning("Topic extraction failed: %s", e)
        return []


async def store_course_topics(course_code: str, topics: list[dict[str, Any]]) -> None:
    db = await get_db()
    await db.query("DELETE course_topic WHERE course_code = $code", {"code": course_code})
    await db.query("DELETE topic_prerequisite WHERE course_code = $code", {"code": course_code})

    for idx, topic in enumerate(topics):
        if not isinstance(topic, dict):
            continue
        topic_name = topic.get("topic_name", "Unit {}".format(idx + 1))
        await db.query(
            "INSERT INTO course_topic {course_code: $code, topic_name: $name, subtopics: $subtopics, prerequisites: $prereqs, bloom_level: $bloom, learning_objectives: $objectives, order_index: $idx}",
            {
                "code": course_code,
                "name": topic_name,
                "subtopics": topic.get("subtopics", []),
                "prereqs": topic.get("prerequisites", []),
                "bloom": topic.get("bloom_level", "Remember"),
                "objectives": topic.get("learning_objectives", []),
                "idx": idx,
            },
        )

    for topic in topics:
        if not isinstance(topic, dict):
            continue
        topic_name = topic.get("topic_name", "")
        for prereq in topic.get("prerequisites", []):
            if not isinstance(prereq, str):
                continue
            await db.query(
                "INSERT INTO topic_prerequisite {course_code: $code, topic_from: $from, topic_to: $to, prereq_type: 'sequential'}",
                {"code": course_code, "from": prereq, "to": topic_name},
            )


async def get_course_topics(course_code: str) -> list[dict[str, Any]]:
    course_code = validate_course_code(course_code)
    db = await get_db()
    res = await db.query(
        "SELECT * FROM course_topic WHERE course_code = $code ORDER BY order_index",
        {"code": course_code},
    )
    if not res:
        return []
    return [
        {
            "topic_name": r.get("topic_name", ""),
            "subtopics": r.get("subtopics", []),
            "prerequisites": r.get("prerequisites", []),
            "bloom_level": r.get("bloom_level", "Remember"),
            "learning_objectives": r.get("learning_objectives", []),
            "order_index": r.get("order_index", 0),
        }
        for r in res
    ]


async def get_topic_coverage(course_code: str) -> dict[str, Any]:
    topics = await get_course_topics(course_code)
    db = await get_db()
    res = await db.query(
        "SELECT topic, count() as cnt FROM text_chunk WHERE course_code = $code AND topic != '' GROUP BY topic",
        {"code": course_code},
    )
    covered = {r["topic"]: r["cnt"] for r in res} if res else {}

    result = []
    for t in topics:
        name = t["topic_name"]
        chunk_count = covered.get(name, 0)
        status = "covered" if chunk_count > 0 else "missing"
        result.append({
            "topic_name": name,
            "status": status,
            "chunk_count": chunk_count,
            "subtopics": t["subtopics"],
            "bloom_level": t["bloom_level"],
        })

    return {
        "course_code": course_code,
        "total_topics": len(topics),
        "covered": sum(1 for r in result if r["status"] == "covered"),
        "missing": sum(1 for r in result if r["status"] == "missing"),
        "topics": result,
    }
