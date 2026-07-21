"""Bayesian Knowledge Tracing — per (topic × bloom_level) mastery prediction.

BKT models each skill as a Hidden Markov Model with 4 parameters:
  p_learn  — probability of transitioning from not-known to known
  p_guess  — probability of correct answer when skill is not known
  p_slip   — probability of wrong answer when skill is known
  p_init   — probability skill is known before any practice
"""

from app.config import settings
from app.db import get_db


class BKTModel:
    def __init__(self, p_init: float | None = None, p_learn: float | None = None, p_guess: float | None = None, p_slip: float | None = None):
        self.p_init = p_init if p_init is not None else settings.BKT_P_INIT
        self.p_learn = p_learn if p_learn is not None else settings.BKT_P_LEARN
        self.p_guess = p_guess if p_guess is not None else settings.BKT_P_GUESS
        self.p_slip = p_slip if p_slip is not None else settings.BKT_P_SLIP

    def predict(self, prior: float, is_correct: bool) -> float:
        p_correct = prior * (1 - self.p_slip) + (1 - prior) * self.p_guess
        if is_correct:
            posterior = (prior * (1 - self.p_slip)) / p_correct
        else:
            posterior = (prior * self.p_slip) / (1 - p_correct)
        return posterior + (1 - posterior) * self.p_learn

    def mastery_from_sequence(self, observations: list[bool], initial: float | None = None) -> float:
        p = initial if initial is not None else self.p_init
        for obs in observations:
            p = self.predict(p, obs)
        return p


async def run_bkt(student_id: str, course_code: str) -> dict[str, float]:
    db = await get_db()
    rows = await db.query(
        "SELECT * FROM question_log WHERE student_id = $sid AND course_code = $cc ORDER BY timestamp ASC",
        {"sid": student_id, "cc": course_code},
    )
    if not rows:
        return {}

    groups: dict[str, list[bool]] = {}
    for row in rows:
        key = f"{row.get('topic_id', 'unknown')}_{row.get('bloom_level', 0)}"
        groups.setdefault(key, []).append(row.get("is_correct", False))

    model = BKTModel(p_learn=settings.BKT_P_LEARN, p_slip=settings.BKT_P_SLIP)
    result = {}
    for key, obs in groups.items():
        result[key] = model.mastery_from_sequence(obs)
    return result


def estimate_mastery(knowledge_state: dict | None) -> float:
    if not knowledge_state:
        return 0.0
    return knowledge_state.get("mastery_score", 0.0)
