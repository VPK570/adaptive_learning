from app.db import SurrealDBManager


class SavedContentManager:
    async def _get_db(self):
        return await SurrealDBManager.get_db()

    async def save_flashcards(self, course_code, topic, cards, user_id=""):
        db = await self._get_db()
        result = await db.query(
            "CREATE flashcard_set CONTENT { user_id: $uid, course_code: $code, topic: $topic, cards: $cards }",
            {"uid": user_id, "code": course_code, "topic": topic, "cards": cards},
        )
        fs = result[0]
        return {
            "id": str(fs["id"]),
            "course_code": fs["course_code"],
            "topic": fs["topic"],
            "cards": fs["cards"],
            "created_at": str(fs.get("created_at")) if fs.get("created_at") else None,
        }

    async def get_saved_flashcards(self, course_code):
        db = await self._get_db()
        result = await db.query(
            "SELECT * FROM flashcard_set WHERE course_code = $code ORDER BY created_at DESC",
            {"code": course_code},
        )
        rows = result if result else []
        return [
            {
                "id": str(r["id"]),
                "course_code": r["course_code"],
                "topic": r["topic"],
                "cards": r["cards"],
                "created_at": str(r.get("created_at")) if r.get("created_at") else None,
            }
            for r in rows
        ]

    async def delete_flashcards(self, set_id):
        db = await self._get_db()
        result = await db.query("DELETE flashcard_set WHERE id = $id", {"id": set_id})
        return bool(result) if result else False

    async def save_quiz(self, course_code, topic, questions, score, user_id=""):
        db = await self._get_db()
        result = await db.query(
            "CREATE quiz CONTENT { user_id: $uid, course_code: $code, topic: $topic, questions: $questions, score: $score, total: $total, completed_at: NONE }",
            {"uid": user_id, "code": course_code, "topic": topic, "questions": questions, "score": score, "total": len(questions)},
        )
        q = result[0]
        return {
            "id": str(q["id"]),
            "course_code": q["course_code"],
            "topic": q["topic"],
            "questions": q["questions"],
            "score": q["score"],
            "total": q["total"],
            "created_at": str(q.get("created_at")) if q.get("created_at") else None,
        }

    async def get_saved_quizzes(self, course_code):
        db = await self._get_db()
        result = await db.query(
            "SELECT * FROM quiz WHERE course_code = $code ORDER BY created_at DESC",
            {"code": course_code},
        )
        rows = result if result else []
        return [
            {
                "id": str(r["id"]),
                "course_code": r["course_code"],
                "topic": r["topic"],
                "questions": r["questions"],
                "score": r["score"],
                "total": r["total"],
                "created_at": str(r.get("created_at")) if r.get("created_at") else None,
            }
            for r in rows
        ]

    async def delete_quiz(self, quiz_id):
        db = await self._get_db()
        result = await db.query("DELETE quiz WHERE id = $id", {"id": quiz_id})
        return bool(result) if result else False
