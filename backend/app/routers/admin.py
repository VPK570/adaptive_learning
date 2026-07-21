from fastapi import APIRouter, Depends

from app.auth import require_role
from app.db import SurrealDBManager

router = APIRouter(dependencies=[Depends(require_role("admin"))])


@router.get("/admin/users")
async def list_users():
    db = await SurrealDBManager.get_db()
    result = await db.query("SELECT * FROM user ORDER BY created_at DESC")
    rows = result if result else []
    return [
        {
            "id": r.get("user_id"),
            "email": r.get("email"),
            "role": r.get("role"),
            "name": r.get("name") or r.get("email", "").split("@")[0],
            "status": "active",
            "created_at": str(r.get("created_at")) if r.get("created_at") else None,
        }
        for r in rows
    ]


@router.get("/admin/stats")
async def platform_stats():
    db = await SurrealDBManager.get_db()
    user_result = await db.query("SELECT count() AS total FROM user GROUP ALL")
    user_count = user_result[0]["total"] if user_result else 0

    course_result = await db.query("SELECT count() AS total FROM course GROUP ALL")
    course_count = course_result[0]["total"] if course_result else 0

    doc_result = await db.query("SELECT count() AS total FROM document GROUP ALL")
    doc_count = doc_result[0]["total"] if doc_result else 0

    conv_result = await db.query("SELECT count() AS total FROM (SELECT session_id FROM chat_message GROUP BY session_id) GROUP ALL")
    conv_count = conv_result[0]["total"] if conv_result else 0

    return {
        "total_users": user_count,
        "total_courses": course_count,
        "total_documents": doc_count,
        "total_conversations": conv_count,
    }
