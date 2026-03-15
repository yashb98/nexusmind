"""Tests for JWT and password hashing utilities."""

from src.utils.auth import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self) -> None:
        password = "test_password_123"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password(self) -> None:
        hashed = hash_password("correct_password")
        assert not verify_password("wrong_password", hashed)

    def test_different_hashes(self) -> None:
        hashed1 = hash_password("same_password")
        hashed2 = hash_password("same_password")
        assert hashed1 != hashed2  # bcrypt uses random salt


class TestJWT:
    def test_create_and_decode(self) -> None:
        token = create_access_token("user-123", "tenant-456")
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["tenant_id"] == "tenant-456"
        assert "exp" in payload

    def test_invalid_token(self) -> None:
        import pytest
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid.token.here")
        assert exc_info.value.status_code == 401
