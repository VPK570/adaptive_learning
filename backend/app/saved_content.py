from app.database import Database
from app.stores.flashcard_store import FlashcardStore
from app.stores.quiz_store import QuizStore


class SavedContentManager:
    async def save_flashcards(self, course_code, topic, cards):
        async with Database.session() as session:
            store = FlashcardStore(session)
            fs = await store.save(course_code, topic, cards)
            return {"id": fs.id, "course_code": fs.course_code, "topic": fs.topic, "cards": fs.cards, "created_at": fs.created_at.isoformat() if fs.created_at else None}

    async def get_saved_flashcards(self, course_code):
        async with Database.session() as session:
            store = FlashcardStore(session)
            sets = await store.get_all(course_code)
            return [
                {"id": s.id, "course_code": s.course_code, "topic": s.topic, "cards": s.cards, "created_at": s.created_at.isoformat() if s.created_at else None}
                for s in sets
            ]

    async def delete_flashcards(self, set_id):
        async with Database.session() as session:
            store = FlashcardStore(session)
            return await store.delete(int(set_id))

    async def save_quiz(self, course_code, topic, questions, score):
        async with Database.session() as session:
            store = QuizStore(session)
            q = await store.save(course_code, topic, questions, score)
            return {"id": q.id, "course_code": q.course_code, "topic": q.topic, "questions": q.questions, "score": q.score, "total": q.total, "created_at": q.created_at.isoformat() if q.created_at else None}

    async def get_saved_quizzes(self, course_code):
        async with Database.session() as session:
            store = QuizStore(session)
            quizzes = await store.get_all(course_code)
            return [
                {"id": q.id, "course_code": q.course_code, "topic": q.topic, "questions": q.questions, "score": q.score, "total": q.total, "created_at": q.created_at.isoformat() if q.created_at else None}
                for q in quizzes
            ]

    async def delete_quiz(self, quiz_id):
        async with Database.session() as session:
            store = QuizStore(session)
            return await store.delete(int(quiz_id))
