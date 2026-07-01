from typing import List

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.flashcard import FlashcardSet


class FlashcardStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, course_code: str, topic: str, cards: list) -> FlashcardSet:
        fs = FlashcardSet(
            course_code=course_code,
            topic=topic,
            cards=cards,
        )
        self.session.add(fs)
        await self.session.flush()
        return fs

    async def get_all(self, course_code: str) -> List[FlashcardSet]:
        result = await self.session.execute(
            select(FlashcardSet)
            .where(FlashcardSet.course_code == course_code)
            .order_by(FlashcardSet.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, set_id: int) -> bool:
        result = await self.session.execute(
            sa_delete(FlashcardSet).where(FlashcardSet.id == set_id)
        )
        return result.rowcount > 0
