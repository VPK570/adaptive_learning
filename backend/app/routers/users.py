from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.db import SurrealDBManager

router = APIRouter()


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None


def _serialize(row):
    return {
        "id": row.get("user_id"),
        "email": row.get("email"),
        "role": row.get("role"),
        "name": row.get("name") or row.get("email", "").split("@")[0],
        "created_at": str(row.get("created_at")) if row.get("created_at") else None,
    }


@router.get("/users/me")
async def get_current_user(request: Request):
    user = request.state.user
    db = await SurrealDBManager.get_db()
    result = await db.query("SELECT * FROM user WHERE email = $email", {"email": user["email"]})
    rows = result if result else []
    if not rows:
        raise HTTPException(404, "User not found")
    return _serialize(rows[0])


@router.put("/users/me")
async def update_current_user(body: UpdateUserRequest, request: Request):
    user = request.state.user
    email = user["email"]
    db = await SurrealDBManager.get_db()
    result = await db.query("SELECT * FROM user WHERE email = $email", {"email": email})
    rows = result if result else []
    if not rows:
        raise HTTPException(404, "User not found")

    if body.name is not None:
        await db.query("UPDATE user SET name = $name WHERE email = $email", {"name": body.name, "email": email})

    result = await db.query("SELECT * FROM user WHERE email = $email", {"email": email})
    rows = result if result else []
    return _serialize(rows[0])
