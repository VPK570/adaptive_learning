from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text

from app.database import Database
from app.stores.user_store import UserStore

router = APIRouter()


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None


def _serialize(db_user):
    return {
        "id": db_user.id,
        "email": db_user.email,
        "role": db_user.role,
        "name": db_user.name or db_user.email.split("@")[0],
        "created_at": db_user.created_at.isoformat() if db_user.created_at else None,
    }


@router.get("/users/me")
async def get_current_user(request: Request):
    user = request.state.user
    async with Database.session() as session:
        store = UserStore(session)
        db_user = await store.get_by_email(user["email"])
        if not db_user:
            raise HTTPException(404, "User not found")
        return _serialize(db_user)


@router.put("/users/me")
async def update_current_user(body: UpdateUserRequest, request: Request):
    user = request.state.user
    email = user["email"]
    async with Database.session() as session:
        store = UserStore(session)
        db_user = await store.get_by_email(email)
        if not db_user:
            raise HTTPException(404, "User not found")

        if body.name is not None:
            await session.execute(
                text("UPDATE users SET name = :name WHERE email = :email"),
                {"name": body.name, "email": email},
            )

        db_user = await store.get_by_email(email)
        return _serialize(db_user)
