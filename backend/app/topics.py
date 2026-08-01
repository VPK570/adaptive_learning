import asyncio
import logging
from typing import Any

from app.config import settings
from app.db import get_db
from app.provider_router import router as client
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


async def embed_course_topics(course_code: str) -> None:
    """Compute and cache embeddings for all topics in a course."""
    from app.db import get_db
    from app.provider_router import router

    db = await get_db()
    topics = await get_course_topics(course_code)
    for topic in topics:
        text = f"{topic['topic_name']} {' '.join(topic.get('subtopics', []) or [])}"
        try:
            embedding = await router.embed_text(text)
            await db.query(
                "UPDATE course_topic SET embedding = $emb WHERE course_code = $code AND topic_name = $name",
                {"emb": embedding, "code": course_code, "name": topic["topic_name"]}
            )
        except Exception as e:
            logger.warning("Failed to embed topic %s: %s", topic["topic_name"], e)


SECTION_CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "classifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "idx": {"type": "integer"},
                    "topic": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    "split_at_paragraph": {"type": ["integer", "null"]}
                },
                "required": ["idx", "topic", "confidence"]
            }
        }
    },
    "required": ["classifications"]
}

EXTRA_TOPICS_SCHEMA = {
    "type": "object",
    "properties": {
        "extra_topics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "page_range": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
                    "description": {"type": "string"}
                },
                "required": ["name", "page_range"]
            }
        }
    },
    "required": ["extra_topics"]
}

CLASSIFY_SECTIONS_PROMPT = """You are classifying sections of a course PDF against the official topic tree.

Course topics:
{course_topics_str}

For each section below, assign the best-matching topic from the list above.
If a section covers content not in any listed topic, set topic to "uncategorized".
If a section clearly covers TWO topics with a clear boundary, set split_at_paragraph to the paragraph index where the split occurs.

Sections:
{sections_str}

Return ONLY valid JSON matching the provided schema."""


def levenshtein(a: str, b: str) -> int:
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            dp[j] = min(prev + (0 if a[i - 1] == b[j - 1] else 1), dp[j] + 1, dp[j - 1] + 1)
            prev = temp
    return dp[n]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


async def classify_sections_llm(sections: list, course_code: str) -> list[dict] | None:
    """Send sections to LLM for topic classification. Returns [{idx, topic, confidence, split_at_paragraph}]."""
    from app.provider_router import router

    course_topics = await get_course_topics(course_code)
    if not course_topics:
        return None

    topic_lines = []
    for i, t in enumerate(course_topics, 1):
        subs = ", ".join(t.get("subtopics", []) or [])
        topic_lines.append(f"{i}. {t['topic_name']}" + (f" — subtopics: {subs}" if subs else ""))
    course_topics_str = "\n".join(topic_lines)

    sections_str_parts = []
    for i, sec in enumerate(sections):
        text = sec.text
        if len(text) > 4500:
            text = text[:4000] + "\n[...]\n" + text[-500:]
        sections_str_parts.append(
            f"--- Section {i} ---\nHeading: {sec.heading}\nPages: {sec.page_start}-{sec.page_end}\nText:\n{text}"
        )

    async def _classify_batch(batch: list[str]) -> list[dict]:
        sections_str = "\n\n".join(batch)
        messages = [{"role": "user", "content": CLASSIFY_SECTIONS_PROMPT.format(
            course_topics_str=course_topics_str, sections_str=sections_str
        )}]
        for attempt in range(2):
            try:
                result = await router.chat_with_schema(messages, response_schema=SECTION_CLASSIFICATION_SCHEMA, max_tokens=4096)
                classifications = result.get("classifications", result.get(".classifications", []))
                if classifications:
                    return classifications
            except Exception:
                if attempt == 1:
                    return []
        return []

    batches = [sections_str_parts[i:i + 10] for i in range(0, len(sections_str_parts), 10)]
    batch_results = await asyncio.gather(*[_classify_batch(b) for b in batches])
    all_results = [item for sublist in batch_results for item in sublist]

    valid_topics = {t["topic_name"].lower(): t["topic_name"] for t in course_topics}
    for r in all_results:
        tl = r.get("topic", "").lower()
        if tl in valid_topics:
            r["topic"] = valid_topics[tl]
        else:
            matched = False
            for cl, cn in valid_topics.items():
                if levenshtein(tl, cl) <= 2:
                    r["topic"] = cn
                    matched = True
                    break
            if not matched:
                r["topic"] = "uncategorized"

    return all_results


async def classify_sections_embedding(sections: list, course_code: str) -> list[dict] | None:
    """Fallback: assign topics via cosine similarity to cached topic embeddings."""
    from app.provider_router import router
    from app.db import get_db

    db = await get_db()
    topics = await db.query(
        "SELECT topic_name, embedding FROM course_topic WHERE course_code = $code AND embedding != NONE",
        {"code": course_code}
    )
    if not topics:
        return None

    results = []
    for i, sec in enumerate(sections):
        sec_emb = await router.embed_text(sec.text[:32000])
        best_topic = "uncategorized"
        best_sim = 0.0
        for t in topics:
            sim = cosine_similarity(sec_emb, t["embedding"])
            if sim > best_sim:
                best_sim = sim
                best_topic = t["topic_name"]
        results.append({
            "idx": i,
            "topic": best_topic if best_sim > 0.5 else "uncategorized",
            "confidence": "high" if best_sim > 0.7 else "medium" if best_sim > 0.5 else "low",
            "split_at_paragraph": None,
        })

    return results


def resolve_topic_boundaries(sections: list, classifications: list[dict]) -> list[dict]:
    """Convert sections + classifications into topic regions. Handles splits and merges adjacent same-topic."""
    class_map = {c["idx"]: c for c in classifications}
    regions = []
    for i, sec in enumerate(sections):
        c = class_map.get(i, {"topic": "uncategorized", "confidence": "low", "split_at_paragraph": None})
        topic = c.get("topic", "uncategorized")
        split = c.get("split_at_paragraph")
        if split is not None and 0 < split < len(sec.text):
            paragraphs = sec.text.split("\n\n")
            if split < len(paragraphs):
                text_a = "\n\n".join(paragraphs[:split])
                text_b = "\n\n".join(paragraphs[split:])
                regions.append({"topic": topic, "heading": sec.heading, "page_start": sec.page_start, "page_end": sec.page_end, "text": text_a})
                regions.append({"topic": "uncategorized", "heading": sec.heading + " (cont.)", "page_start": sec.page_start, "page_end": sec.page_end, "text": text_b})
                continue
        regions.append({"topic": topic, "heading": sec.heading, "page_start": sec.page_start, "page_end": sec.page_end, "text": sec.text})

    merged = []
    for r in regions:
        if merged and merged[-1]["topic"] == r["topic"]:
            merged[-1]["text"] += "\n\n" + r["text"]
            merged[-1]["page_end"] = r["page_end"]
        else:
            merged.append(dict(r))
    return merged


async def extract_extra_topics_llm(unmatched_texts: list[dict], course_code: str) -> list[dict]:
    """Batch uncategorized sections and ask LLM for topic suggestions."""
    if not unmatched_texts:
        return []
    from app.provider_router import router
    batch_text = "\n\n".join(
        f"--- Chunk from pages {t['page_start']}-{t['page_end']} ---\n{t['text'][:1000]}"
        for t in unmatched_texts
    )
    messages = [
        {"role": "user", "content": (
            "These text fragments from a course PDF don't match any known curriculum topics. "
            f"Suggest 1-3 topic names that describe what they cover. Course code: {course_code}.\n\n{batch_text}"
        )}
    ]
    for attempt in range(2):
        try:
            result = await router.chat_with_schema(messages, response_schema=EXTRA_TOPICS_SCHEMA, max_tokens=1024)
            extras = result.get("extra_topics", result.get(".extra_topics", []))
            return extras
        except Exception:
            if attempt == 1:
                return []
    return []


async def get_topic_coverage(course_code: str) -> dict[str, Any]:
    topics = await get_course_topics(course_code)
    db = await get_db()
    res = await db.query(
        "SELECT topic, count() as cnt FROM text_chunk WHERE course_code = $code GROUP BY topic",
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
