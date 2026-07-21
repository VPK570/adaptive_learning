"""Gap Detection — compares quiz accuracy across Bloom's Taxonomy levels.

Detects when a student's quiz accuracy drops significantly as Bloom level
increases (e.g., 90% at Remember, 50% at Evaluate), indicating a cognitive
gap between levels.
"""

from app.config import settings
from app.db import get_db
from app.knowledge_state import BLOOM_LABELS

GAP_THRESHOLD = 0.25
MIN_ATTEMPTS_PER_LEVEL = 3


async def detect_gaps(student_id: str, course_code: str, topic_id: str | None = None) -> list[dict]:
    db = await get_db()
    query = "SELECT bloom_level, is_correct, topic_id FROM question_log WHERE student_id = $sid AND course_code = $cc AND source = 'quiz'"
    params = {"sid": student_id, "cc": course_code}
    if topic_id:
        query += " AND topic_id = $tid"
        params["tid"] = topic_id

    rows = await db.query(query, params)
    if not rows:
        return []

    level_stats: dict[int, list[bool]] = {}
    for row in rows:
        bl = row.get("bloom_level")
        if bl is None:
            continue
        level_stats.setdefault(bl, []).append(row.get("is_correct", False))

    level_accuracy = {}
    for bl, outcomes in level_stats.items():
        if len(outcomes) >= MIN_ATTEMPTS_PER_LEVEL:
            level_accuracy[bl] = sum(outcomes) / len(outcomes)

    gaps = []
    for bl in sorted(level_accuracy.keys()):
        if bl <= 1:
            continue
        lower_acc = level_accuracy.get(bl - 1)
        if lower_acc is None:
            continue
        current_acc = level_accuracy[bl]
        drop = lower_acc - current_acc
        if drop > GAP_THRESHOLD and current_acc < settings.MASTERY_THRESHOLD:
            gaps.append({
                "bloom_level": bl,
                "bloom_label": BLOOM_LABELS.get(bl, f"L{bl}"),
                "accuracy": round(current_acc, 3),
                "lower_level_accuracy": round(lower_acc, 3),
                "gap": round(drop, 3),
                "attempts": len(level_stats[bl]),
            })

    gaps.sort(key=lambda g: -g["gap"])
    return gaps


async def should_trigger_diagnostic(student_id: str, course_code: str) -> bool:
    gaps = await detect_gaps(student_id, course_code)
    return len(gaps) >= 2


def build_diagnostic_preamble(topic_id: str, gaps: list[dict]) -> str:
    levels = ", ".join(g["bloom_label"] for g in gaps)
    return (
        f"Your quiz performance shows a drop at the {levels} level(s). "
        f"Let's check your understanding from a different angle..."
    )
