from datetime import datetime
from app.validation import validate_course_code, sanitize_text, MAX_TOPIC_LENGTH, validate_id
from app.db import get_db

class SavedContentManager:
    async def _save(self, table: str, data: dict):
        db = await get_db()
        res = await db.query(f"CREATE {table} CONTENT $content", {"content": data})
        if res and res[0]["result"]:
            item = res[0]["result"][0]
            item["id"] = str(item["id"])
            return item
        return data

    async def _get_all(self, table: str, course_code: str):
        course_code = validate_course_code(course_code)
        db = await get_db()
        res = await db.query(f"SELECT * FROM {table} WHERE course_code = $code ORDER BY created_at DESC", {"code": course_code})
        if res and res[0]["result"]:
            results = res[0]["result"]
            for r in results:
                r["id"] = str(r["id"])
            return results
        return []

    async def _delete(self, table: str, item_id: str):
        id_part = item_id.split(":")[-1] if ":" in item_id else item_id
        validate_id(id_part)
        db = await get_db()
        if ":" not in item_id:
            item_id = f"{table}:{item_id}"
        res = await db.query("DELETE $id", {"id": item_id})
        return bool(res and res[0]["status"] == "OK")

    async def save_flashcards(self, course_code, topic, cards):
        return await self._save("flashcard_set", {
            "course_code": validate_course_code(course_code),
            "topic": sanitize_text(topic, MAX_TOPIC_LENGTH),
            "cards": cards,
            "created_at": datetime.now().isoformat(),
        })

    async def get_saved_flashcards(self, course_code):
        return await self._get_all("flashcard_set", course_code)

    async def delete_flashcards(self, set_id):
        return await self._delete("flashcard_set", set_id)

    async def save_quiz(self, course_code, topic, questions, score):
        return await self._save("quiz", {
            "course_code": validate_course_code(course_code),
            "topic": sanitize_text(topic, MAX_TOPIC_LENGTH),
            "questions": questions,
            "score": score,
            "total": len(questions),
            "created_at": datetime.now().isoformat(),
        })

    async def get_saved_quizzes(self, course_code):
        return await self._get_all("quiz", course_code)

    async def delete_quiz(self, quiz_id):
        return await self._delete("quiz", quiz_id)
