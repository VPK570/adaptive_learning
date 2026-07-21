from app.db import get_db


async def get_course_history(course_code: str, session_id: str, user_id: str | None = None) -> list[dict]:
    db = await get_db()
    query = "SELECT * FROM chat_message WHERE course_code = $code AND session_id = $sid"
    params = {"code": course_code, "sid": session_id}
    if user_id:
        query += " AND user_id = $uid"
        params["uid"] = user_id
    query += " ORDER BY timestamp ASC"
    result = await db.query(query, params)
    rows = result if result else []
    return [
        {
            "id": str(r["id"]),
            "course_code": r["course_code"],
            "session_id": r["session_id"],
            "role": r["message_role"],
            "content": r["content"],
            "timestamp": str(r.get("timestamp")) if r.get("timestamp") else None,
        }
        for r in rows
    ]


async def add_message(course_code: str, session_id: str, role: str, content: str, user_id: str = ""):
    db = await get_db()
    await db.query(
        "CREATE chat_message CONTENT { course_code: $code, session_id: $sid, message_role: $role, content: $content, user_id: $uid }",
        {"code": course_code, "sid": session_id, "role": role, "content": content, "uid": user_id},
    )


async def clear_course_history(course_code: str, session_id: str, user_id: str | None = None):
    db = await get_db()
    query = "DELETE chat_message WHERE course_code = $code AND session_id = $sid"
    params = {"code": course_code, "sid": session_id}
    if user_id:
        query += " AND user_id = $uid"
        params["uid"] = user_id
    await db.query(query, params)
