"""
Unit tests for security utilities (JWT and password hashing)
"""
from datetime import timedelta

import pytest
from jose import JWTError

from src.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    """Test password hashing and verification"""

    def test_get_password_hash(self):
        """Test password hashing creates different hashes for same password"""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2  # bcrypt salts should make hashes different
        assert hash1.startswith("$2b$")  # bcrypt hash format

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password("wrongpassword", hashed) is False


class TestJWT:
    """Test JWT token creation and validation"""

    def test_create_access_token(self):
        """Test JWT token creation with payload"""
        data = {"sub": "user123", "role": "admin"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_valid(self):
        """Test token verification with valid token"""
        data = {"sub": "user123", "role": "admin"}
        token = create_access_token(data)

        payload = verify_token(token)

        assert payload["sub"] == "user123"
        assert payload["role"] == "admin"
        assert "exp" in payload  # Expiration should be added

    def test_verify_token_with_custom_expiration(self):
        """Test token creation with custom expiration"""
        data = {"sub": "user123"}
        expires_delta = timedelta(hours=1)
        token = create_access_token(data, expires_delta)

        payload = verify_token(token)

        assert payload["sub"] == "user123"
        assert "exp" in payload

    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        invalid_token = "invalid.token.here"

        with pytest.raises(JWTError):
            verify_token(invalid_token)

    def test_verify_token_expired(self):
        """Test token verification with expired token"""
        data = {"sub": "user123"}
        # Create token that expires immediately (negative time)
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta)

        with pytest.raises(JWTError):
            verify_token(token)
