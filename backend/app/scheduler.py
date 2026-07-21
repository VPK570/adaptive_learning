"""Spaced repetition scheduler — simplified exponential-backoff algorithm.

Upgrade path: swap `_schedule_simple` for `py-fsrs` Scheduler when
Python 3.14+ compat is available (pip install py-fsrs).
"""

import importlib
import logging
from datetime import datetime, timedelta, timezone
from app.db import get_db

logger = logging.getLogger(__name__)

FSRS_AVAILABLE = importlib.util.find_spec("fsrs") is not None
if not FSRS_AVAILABLE:
    logger.info("py-fsrs not available — using SM-2 fallback scheduler")


async def run_nightly_scheduler():
    db = await get_db()
    states = await db.query("SELECT * FROM knowledge_state")
    if not states:
        return

    now = datetime.now(timezone.utc)
    updated = 0
    for state in states:
        if not state.get("id"):
            continue
        mastery = state.get("mastery_score", 0.0)

        rating = _mastery_to_rating(mastery)
        interval_days = _schedule_simple(rating, state.get("streak", 0))

        next_review = now + timedelta(days=interval_days)
        await db.query(
            "UPDATE $id MERGE { stability: $s, next_review_at: $n }",
            {"id": state["id"], "s": interval_days, "n": next_review.isoformat()},
        )
        updated += 1

    logger.info("Scheduler ran: %d knowledge states updated", updated)


async def schedule_on_quiz(student_id: str, course_code: str, topic_id: str, bloom_level: int, mastery: float, streak: int):
    db = await get_db()
    res = await db.query(
        "SELECT * FROM knowledge_state WHERE student_id = $sid AND course_code = $cc AND topic_id = $tid AND bloom_level = $bl LIMIT 1",
        {"sid": student_id, "cc": course_code, "tid": topic_id, "bl": bloom_level},
    )
    if not res:
        return

    state = res[0]
    rating = _mastery_to_rating(mastery)
    interval_days = _schedule_simple(rating, streak)
    now = datetime.now(timezone.utc)
    next_review = now + timedelta(days=interval_days)

    await db.query(
        "UPDATE $id MERGE { stability: $s, next_review_at: $n }",
        {"id": state["id"], "s": interval_days, "n": next_review.isoformat()},
    )


def _mastery_to_rating(mastery: float) -> int:
    if mastery >= 0.9:
        return 5
    elif mastery >= 0.7:
        return 4
    elif mastery >= 0.5:
        return 3
    elif mastery >= 0.3:
        return 2
    return 1


def _schedule_simple(rating: int, streak: int) -> int:
    if rating < 3:
        return 1
    if streak == 0:
        return 1
    if streak == 1:
        return 6
    return round(6 * (rating - 1) ** (streak - 1))
