"""Auth routes — register and login. Issues JWT tokens.

These two routes must stay PUBLIC (no token required) — you can't have a
token before you log in.
"""


from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_user_by_email,
    _create_user,
    VALID_ROLES,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = "student"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str | None = None


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest):
    role = body.role.lower().strip()
    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(sorted(VALID_ROLES))}",
        )

    if len(body.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    existing = await get_user_by_email(body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    try:
        await _create_user(body.email.lower().strip(), hash_password(body.password), role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    token = create_access_token({"sub": body.email.lower().strip(), "role": role})
    return TokenResponse(access_token=token, role=role)


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    # OAuth2PasswordRequestForm uses "username" — we treat it as email.
    user = await get_user_by_email(form.username)
    if not user or not verify_password(form.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user["email"], "role": user.get("role", "student")})
    return TokenResponse(access_token=token, role=user.get("role", "student"), name=user.get("name"))