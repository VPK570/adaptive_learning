from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def create(self, email: str, hashed_password: str, role: str) -> User:
        user = User(
            email=email.lower().strip(),
            hashed_password=hashed_password,
            role=role,
        )
        self.session.add(user)
        try:
            await self.session.flush()
        except IntegrityError:
            raise ValueError(f"User with email {email} already exists")
        return user
