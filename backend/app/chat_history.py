from app.database import Database
from app.stores.chat_store import ChatStore


async def get_course_history(course_code, session_id):
    async with Database.session() as session:
        store = ChatStore(session)
        messages = await store.get_history(course_code, session_id)
        return [
            {
                "id": str(m.id),
                "course_code": m.course_code,
                "session_id": m.session_id,
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            }
            for m in messages
        ]


async def add_message(course_code, session_id, role, content):
    async with Database.session() as session:
        store = ChatStore(session)
        await store.add_message(course_code, session_id, role, content)


async def clear_course_history(course_code, session_id):
    async with Database.session() as session:
        store = ChatStore(session)
        await store.clear_history(course_code, session_id)
