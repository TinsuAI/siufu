"""Simplified integration tests for authentication - basic coverage."""

import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app


@pytest.mark.integration
class TestAuthEndpoints:
    """Basic integration tests for authentication endpoints."""

    async def test_register_invalid_email_format(self):
        """Test registration with invalid email returns 422."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={"email": "not-an-email", "password": "password123", "full_name": "Test"}
            )
            assert response.status_code == 422

    async def test_register_short_password(self):
        """Test registration with short password returns 422."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={"email": "test@example.com", "password": "short", "full_name": "Test"}
            )
            assert response.status_code == 422

    async def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "nonexistent@example.com", "password": "password123"}
            )
            assert response.status_code == 401
            assert "Invalid email or password" in response.json()["detail"]

    async def test_logout_endpoint_accessible(self):
        """Test logout endpoint is accessible."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/auth/logout")
            assert response.status_code == 200
            assert "message" in response.json()

    async def test_get_current_user_unauthenticated(self):
        """Test /me endpoint returns 401 without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")
            assert response.status_code == 401
            assert "Not authenticated" in response.json()["detail"]

    async def test_get_current_user_invalid_token(self):
        """Test /me endpoint returns 401 with invalid token."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                cookies={"access_token": "invalid.token.here"}
            )
            assert response.status_code == 401

    async def test_protected_endpoint_requires_auth(self):
        """Test protected endpoints require authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/declarations")
            assert response.status_code == 401
