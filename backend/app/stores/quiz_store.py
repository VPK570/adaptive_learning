from typing import List, Optional

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Quiz


class QuizStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, course_code: str, topic: str, questions: list, score: Optional[int] = None) -> Quiz:
        q = Quiz(
            course_code=course_code,
            topic=topic,
            questions=questions,
            score=score,
            total=len(questions),
        )
        self.session.add(q)
        await self.session.flush()
        return q

    async def get_all(self, course_code: str) -> List[Quiz]:
        result = await self.session.execute(
            select(Quiz)
            .where(Quiz.course_code == course_code)
            .order_by(Quiz.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, quiz_id: int) -> bool:
        result = await self.session.execute(
            sa_delete(Quiz).where(Quiz.id == quiz_id)
        )
        return result.rowcount > 0
