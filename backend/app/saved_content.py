from datetime import datetime
from app.validation import validate_course_code, sanitize_text, MAX_TOPIC_LENGTH, validate_id
from app.db import get_db

class SavedContentManager:
    async def save_flashcards(self, course_code, topic, cards):
        course_code = validate_course_code(course_code)
        topic = sanitize_text(topic, MAX_TOPIC_LENGTH)
        
        db = await get_db()
        new_set = {
            "course_code": course_code,
            "topic": topic,
            "cards": cards,
            "created_at": datetime.now().isoformat()
        }
        res = await db.query("CREATE flashcard_set CONTENT $content", {"content": new_set})
        if res and res[0]["result"]:
            item = res[0]["result"][0]
            item["id"] = str(item["id"])
            return item
        return new_set

    async def get_saved_flashcards(self, course_code):
        course_code = validate_course_code(course_code)
        db = await get_db()
        res = await db.query("SELECT * FROM flashcard_set WHERE course_code = $code ORDER BY created_at DESC", {"code": course_code})
        if res and res[0]["result"]:
            results = res[0]["result"]
            for r in results:
                r["id"] = str(r["id"])
            return results
        return []

    async def delete_flashcards(self, set_id):
        # If it's a full record ID like "flashcard_set:id", extract the id part for validation
        id_part = set_id.split(":")[-1] if ":" in set_id else set_id
        validate_id(id_part)
        
        db = await get_db()
        if ":" not in set_id:
            set_id = f"flashcard_set:{set_id}"
            
        res = await db.query("DELETE $id", {"id": set_id})
        return bool(res and res[0]["status"] == "OK")

    async def save_quiz(self, course_code, topic, questions, score):
        course_code = validate_course_code(course_code)
        topic = sanitize_text(topic, MAX_TOPIC_LENGTH)
        
        db = await get_db()
        new_quiz = {
            "course_code": course_code,
            "topic": topic,
            "questions": questions,
            "score": score,
            "total": len(questions),
            "created_at": datetime.now().isoformat()
        }
        res = await db.query("CREATE quiz CONTENT $content", {"content": new_quiz})
        if res and res[0]["result"]:
            item = res[0]["result"][0]
            item["id"] = str(item["id"])
            return item
        return new_quiz

    async def get_saved_quizzes(self, course_code):
        course_code = validate_course_code(course_code)
        db = await get_db()
        res = await db.query("SELECT * FROM quiz WHERE course_code = $code ORDER BY created_at DESC", {"code": course_code})
        if res and res[0]["result"]:
            results = res[0]["result"]
            for r in results:
                r["id"] = str(r["id"])
            return results
        return []

    async def delete_quiz(self, quiz_id):
        id_part = quiz_id.split(":")[-1] if ":" in quiz_id else quiz_id
        validate_id(id_part)
        
        db = await get_db()
        if ":" not in quiz_id:
            quiz_id = f"quiz:{quiz_id}"
        res = await db.query("DELETE $id", {"id": quiz_id})
        return bool(res and res[0]["status"] == "OK")
