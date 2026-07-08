from typing import List

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage


class ChatStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_history(self, course_code: str, session_id: str) -> List[ChatMessage]:
        result = await self.session.execute(
            select(ChatMessage)
            .where(ChatMessage.course_code == course_code, ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp.asc())
        )
        return list(result.scalars().all())

    async def add_message(self, course_code: str, session_id: str, role: str, content: str) -> ChatMessage:
        msg = ChatMessage(
            course_code=course_code,
            session_id=session_id,
            role=role,
            content=content,
        )
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def clear_history(self, course_code: str, session_id: str):
        await self.session.execute(
            sa_delete(ChatMessage).where(
                ChatMessage.course_code == course_code,
                ChatMessage.session_id == session_id,
            )
        )
