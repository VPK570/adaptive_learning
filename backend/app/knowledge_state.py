from datetime import datetime, timezone
from app.db import get_db

LEARNING_RATE = 0.15

BLOOM_PROMPTS = {
    1: "Ask recall questions. Request definitions, lists, and factual statements.",
    2: "Ask for explanations in the student's own words. Use 'Explain why' and 'What does this mean'.",
    3: "Ask the student to apply concepts to new scenarios. Use 'How would you solve'.",
    4: "Ask the student to break down relationships and compare. Use 'How does X relate to Y'.",
    5: "Ask the student to justify or critique. Use 'What is the strongest argument'.",
    6: "Ask the student to design or generate. Use 'How would you create'.",
}

BLOOM_LABELS = {1: "Remember", 2: "Understand", 3: "Apply", 4: "Analyze", 5: "Evaluate", 6: "Create"}


class KnowledgeStateManager:
    async def get_state(self, student_id: str, course_code: str, topic_id: str, bloom_level: int) -> dict:
        db = await get_db()
        res = await db.query(
            "SELECT * FROM knowledge_state WHERE student_id = $sid AND course_code = $cc AND topic_id = $tid AND bloom_level = $bl LIMIT 1",
            {"sid": student_id, "cc": course_code, "tid": topic_id, "bl": bloom_level},
        )
        if res and len(res) > 0:
            return res[0]
        return self._default_state(student_id, course_code, topic_id, bloom_level)

    async def get_student_course_states(self, student_id: str, course_code: str) -> list[dict]:
        db = await get_db()
        res = await db.query(
            "SELECT * FROM knowledge_state WHERE student_id = $sid AND course_code = $cc",
            {"sid": student_id, "cc": course_code},
        )
        return res or []

    async def get_topic_summary(self, student_id: str, course_code: str, topic_id: str) -> dict:
        states = await self.get_student_course_states(student_id, course_code)
        topic_states = [s for s in states if s.get("topic_id") == topic_id]
        if not topic_states:
            return {"mastery": 0.0, "confidence": 0.0, "total_attempts": 0}
        avg_mastery = sum(s.get("mastery_score", 0.0) for s in topic_states) / len(topic_states)
        avg_confidence = sum(s.get("confidence", 0.0) for s in topic_states) / len(topic_states)
        return {
            "mastery": round(avg_mastery, 3),
            "confidence": round(avg_confidence, 3),
            "total_attempts": sum(s.get("total_attempts", 0) for s in topic_states),
            "bloom_breakdown": {s.get("bloom_level", 0): s.get("mastery_score", 0.0) for s in topic_states},
        }

    async def update_state(self, student_id: str, course_code: str, topic_id: str, bloom_level: int, is_correct: bool):
        db = await get_db()
        existing = await self.get_state(student_id, course_code, topic_id, bloom_level)

        total = (existing.get("total_attempts", 0) if existing else 0) + 1
        correct = (existing.get("correct_attempts", 0) if existing else 0) + (1 if is_correct else 0)
        mastery = existing.get("mastery_score", 0.0) if existing else 0.0
        streak = existing.get("streak", 0) if existing else 0

        if is_correct:
            mastery += LEARNING_RATE * (1 - mastery)
            streak += 1
        else:
            mastery -= LEARNING_RATE * mastery
            streak = 0

        mastery = max(0.0, min(1.0, mastery))
        correct_rate = correct / total if total > 0 else 0.0
        confidence = 1.0 - ((1.0 - correct_rate) / (1.0 + total * 0.1))
        confidence = max(0.0, min(1.0, confidence))

        now = datetime.now(timezone.utc)
        existing_defaults = existing if isinstance(existing, dict) else {}
        data = {
            "student_id": student_id,
            "course_code": course_code,
            "topic_id": topic_id,
            "bloom_level": bloom_level,
            "mastery_score": mastery,
            "confidence": confidence,
            "total_attempts": total,
            "correct_attempts": correct,
            "streak": streak,
            "last_reviewed_at": now,
            "updated_at": now,
        }
        if existing_defaults.get("difficulty") is not None:
            data["difficulty"] = existing_defaults["difficulty"]
        if existing_defaults.get("stability") is not None:
            data["stability"] = existing_defaults["stability"]
        next_review = existing_defaults.get("next_review_at")
        if next_review is not None:
            data["next_review_at"] = next_review

        res = await db.query(
            "UPDATE knowledge_state MERGE $data WHERE student_id = $sid AND course_code = $cc AND topic_id = $tid AND bloom_level = $bl RETURN AFTER",
            {"data": data, "sid": student_id, "cc": course_code, "tid": topic_id, "bl": bloom_level},
        )
        if not res or len(res) == 0:
            await db.query(
                "CREATE knowledge_state CONTENT $data",
                {"data": data},
            )

        await self._log_question(student_id, course_code, topic_id, bloom_level, is_correct)

    async def _log_question(self, student_id: str, course_code: str, topic_id: str, bloom_level: int, is_correct: bool, source: str = "quiz"):
        db = await get_db()
        await db.query(
            "CREATE question_log CONTENT { student_id: $sid, course_code: $cc, topic_id: $tid, bloom_level: $bl, is_correct: $cor, source: $src, timestamp: time::now() }",
            {"sid": student_id, "cc": course_code, "tid": topic_id, "bl": bloom_level, "cor": is_correct, "src": source},
        )

    def _default_state(self, student_id: str, course_code: str, topic_id: str, bloom_level: int) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "student_id": student_id,
            "course_code": course_code,
            "topic_id": topic_id,
            "bloom_level": bloom_level,
            "mastery_score": 0.0,
            "confidence": 0.0,
            "stability": None,
            "difficulty": 0.5,
            "total_attempts": 0,
            "correct_attempts": 0,
            "streak": 0,
            "last_reviewed_at": now,
            "next_review_at": now,
        }
