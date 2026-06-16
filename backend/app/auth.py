"""Authentication — password hashing and JWT token handling.

Self-hosted JWT auth (no external provider) so user data stays on
university infrastructure, per the project's privacy requirements.

NOTE: The get_current_user dependency is provided but NOT yet attached
to existing routes. The frontend does not send tokens yet, so arming
routes now would break the app. To protect a route later, add:
    user = Depends(get_current_user)
to that route's signature.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.db import get_db

logger = logging.getLogger(__name__)

# bcrypt for password hashing — never store raw passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Tells FastAPI/Swagger where the login endpoint is, so /docs shows an
# "Authorize" button. tokenUrl is relative to the API root.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

VALID_ROLES = {"student", "faculty", "admin"}


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def create_access_token(data: dict[str, Any], expires_minutes: Optional[int] = None) -> str:
    """Create a signed JWT. `data` should include the subject and role."""
    to_encode = data.copy()
    minutes = expires_minutes if expires_minutes is not None else settings.JWT_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT. Raises 401 if invalid or expired."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.info("Token rejected: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_by_email(email: str) -> Optional[dict[str, Any]]:
    db = await get_db()
    res = await db.query(
        "SELECT * FROM users WHERE email = $email LIMIT 1",
        {"email": email.lower().strip()},
    )
    if isinstance(res, list) and res:
        return res[0]
    return None


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> dict[str, Any]:
    """Dependency: returns the current user from the bearer token, or 401.

    Attach to a route to protect it:
        async def my_route(user = Depends(get_current_user)): ...
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )
    return user


def require_role(*allowed_roles: str):
    """Dependency factory for RBAC. Use once auth is armed, e.g.:
        user = Depends(require_role("faculty", "admin"))
    """
    async def _checker(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return user
    return _checker
