"""Tests for auth module — password hashing, JWT tokens, role enforcement."""
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from jose import jwt

os.environ["JWT_SECRET"] = "test_secret_key_for_pytest"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_EXPIRE_MINUTES"] = "60"

from fastapi import HTTPException

from app.auth import (
    VALID_ROLES,
    create_access_token,
    decode_token,
    get_current_user_from_request,
    hash_password,
    require_role,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("securepass123")
        assert hashed != "securepass123"
        assert verify_password("securepass123", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("securepass123")
        assert verify_password("wrongpass", hashed) is False

    def test_verify_empty_password(self):
        hashed = hash_password("securepass123")
        assert verify_password("", hashed) is False

    def test_verify_invalid_hash(self):
        assert verify_password("test", "not_a_valid_hash") is False

    def test_hash_is_different_each_time(self):
        h1 = hash_password("samepass")
        h2 = hash_password("samepass")
        assert h1 != h2


class TestJWTTokens:
    def test_create_and_decode(self):
        token = create_access_token({"sub": "test@test.com", "role": "student"})
        payload = decode_token(token)
        assert payload["sub"] == "test@test.com"
        assert payload["role"] == "student"
        assert "exp" in payload

    def test_decode_expired_token(self):
        token = create_access_token({"sub": "test@test.com"}, expires_minutes=-1)
        with pytest.raises(HTTPException) as exc:
            decode_token(token)
        assert exc.value.status_code == 401

    def test_decode_invalid_signature(self):
        token = jwt.encode({"sub": "test"}, "wrong_secret", algorithm="HS256")
        with pytest.raises(HTTPException) as exc:
            decode_token(token)
        assert exc.value.status_code == 401

    def test_decode_malformed_token(self):
        with pytest.raises(HTTPException) as exc:
            decode_token("not.a.token")
        assert exc.value.status_code == 401

    def test_token_contains_expected_claims(self):
        token = create_access_token({"sub": "a@b.com", "role": "admin"})
        payload = decode_token(token)
        assert payload["sub"] == "a@b.com"
        assert payload["role"] == "admin"

    def test_custom_expiry(self):
        token = create_access_token({"sub": "test"}, expires_minutes=5)
        payload = decode_token(token)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        assert now < exp < now + timedelta(minutes=10)


class TestRequireRole:
    @pytest.mark.asyncio
    async def test_allows_valid_role(self):
        request = AsyncMock()
        request.state.user = {"email": "a@b.com", "role": "admin"}
        checker = require_role("admin", "faculty")
        user = await checker(request)
        assert user["role"] == "admin"

    @pytest.mark.asyncio
    async def test_blocks_wrong_role(self):
        request = AsyncMock()
        request.state.user = {"email": "a@b.com", "role": "student"}
        checker = require_role("admin", "faculty")
        with pytest.raises(HTTPException) as exc:
            await checker(request)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_blocks_unauthenticated(self):
        request = AsyncMock()
        request.state.user = None
        checker = require_role("admin")
        with pytest.raises(HTTPException) as exc:
            await checker(request)
        assert exc.value.status_code == 401


class TestGetCurrentUserFromRequest:
    @pytest.mark.asyncio
    async def test_returns_user_when_present(self):
        request = AsyncMock()
        request.state.user = {"email": "a@b.com", "role": "student"}
        user = await get_current_user_from_request(request)
        assert user["email"] == "a@b.com"

    @pytest.mark.asyncio
    async def test_raises_when_missing(self):
        request = AsyncMock()
        request.state.user = None
        with pytest.raises(HTTPException) as exc:
            await get_current_user_from_request(request)
        assert exc.value.status_code == 401


class TestValidRoles:
    def test_contains_expected_roles(self):
        assert VALID_ROLES == {"student", "faculty", "admin"}
