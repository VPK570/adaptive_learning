from app.db import SurrealDBManager


async def get_course_history(course_code, session_id, user_id=None):
    db = await SurrealDBManager.get_db()
    params = {"code": course_code, "sid": session_id}
    extra = ""
    if user_id:
        extra = " AND user_id = $uid"
        params["uid"] = user_id
    result = await db.query(
        f"SELECT * FROM chat_message WHERE course_code = $code AND session_id = $sid{extra} ORDER BY timestamp ASC",
        params,
    )
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


async def add_message(course_code, session_id, role, content, user_id=None):
    db = await SurrealDBManager.get_db()
    await db.query(
        "CREATE chat_message CONTENT { user_id: $uid, course_code: $code, session_id: $sid, message_role: $role, content: $content }",
        {"uid": user_id or "", "code": course_code, "sid": session_id, "role": role, "content": content},
    )


async def clear_course_history(course_code, session_id, user_id=None):
    db = await SurrealDBManager.get_db()
    params = {"code": course_code, "sid": session_id}
    extra = ""
    if user_id:
        extra = " AND user_id = $uid"
        params["uid"] = user_id
    await db.query(
        f"DELETE chat_message WHERE course_code = $code AND session_id = $sid{extra}",
        params,
    )
