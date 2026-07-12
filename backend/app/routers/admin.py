from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_role
from app.database import Database
from app.db import get_db
from app.stores.user_store import UserStore

router = APIRouter(dependencies=[Depends(require_role("admin"))])


@router.get("/admin/users")
async def list_users():
    async with Database.session() as session:
        store = UserStore(session)
        users = await store.get_all()
        return [
            {
                "id": u.id,
                "email": u.email,
                "role": u.role,
                "name": u.name or u.email.split("@")[0],
                "status": "active",
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]


@router.get("/admin/stats")
async def platform_stats():
    async with Database.session() as session:
        store = UserStore(session)
        user_count = await store.count()

    db = await get_db()
    course_result = await db.query("SELECT count() AS total FROM course GROUP ALL")
    course_count = course_result[0]["total"] if course_result else 0

    return {
        "total_users": user_count,
        "total_courses": course_count,
        "total_documents": 0,
        "total_conversations": 0,
    }
