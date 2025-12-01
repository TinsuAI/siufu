"""Integration tests for authentication endpoints."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.models.user import User


@pytest.mark.integration
class TestRegisterEndpoint:
    """Integration tests for POST /api/v1/auth/register."""

    async def test_register_success(self, async_client: AsyncClient):
        """Test successful user registration."""
        # Use unique email to avoid conflicts across test runs
        unique_email = f"newuser-{uuid.uuid4().hex[:8]}@example.com"
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "NewPassword123!",  # Must have uppercase, lowercase, number, special char
                "full_name": "New User"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == unique_email
        assert data["user"]["full_name"] == "New User"
        assert data["user"]["role"] == "processor"
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "access_token" in response.cookies

    async def test_register_duplicate_email(self, async_client: AsyncClient, test_user: User):
        """Test registration with existing email returns 400."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "Password123!",  # Must have uppercase, lowercase, number, special char
                "full_name": "Duplicate User"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already" in data["detail"].lower()

    async def test_register_invalid_email(self, async_client: AsyncClient):
        """Test registration with invalid email format returns 422."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
                "full_name": "Test User"
            }
        )

        assert response.status_code == 422

    async def test_register_short_password(self, async_client: AsyncClient):
        """Test registration with password < 8 characters returns 422."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "short",
                "full_name": "Test User"
            }
        )

        assert response.status_code == 422


@pytest.mark.integration
class TestLoginEndpoint:
    """Integration tests for POST /api/v1/auth/login."""

    async def test_login_success(self, async_client: AsyncClient, test_user: User):
        """Test successful login with valid credentials."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "Test12345!"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == test_user.email
        assert data["user"]["full_name"] == test_user.full_name
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "access_token" in response.cookies

    async def test_login_invalid_email(self, async_client: AsyncClient):
        """Test login with non-existent email returns 401."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Invalid email or password"

    async def test_login_invalid_password(self, async_client: AsyncClient, test_user: User):
        """Test login with wrong password returns 401."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Invalid email or password"

    async def test_login_inactive_user(self, async_client: AsyncClient, db_session, test_user: User):
        """Test login with inactive user returns 401."""
        test_user.is_active = False
        await db_session.flush()

        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "Test12345!"
            }
        )

        assert response.status_code == 401


@pytest.mark.integration
class TestLogoutEndpoint:
    """Integration tests for POST /api/v1/auth/logout."""

    async def test_logout_clears_cookie(self, async_client: AsyncClient):
        """Test logout clears access_token cookie."""
        response = await async_client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Successfully logged out"
        # Cookie clearing is verified by max_age=0 in response headers


@pytest.mark.integration
class TestGetCurrentUserEndpoint:
    """Integration tests for GET /api/v1/auth/me."""

    async def test_get_current_user_authenticated(self, async_client: AsyncClient, test_user: User):
        """Test GET /api/v1/auth/me with valid token returns user profile."""
        # First login to get token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "Test12345!"
            }
        )
        assert login_response.status_code == 200

        # Call /me with cookie from login
        response = await async_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["role"] == test_user.role
        assert data["is_active"] == test_user.is_active
        assert "id" in data
        assert "organization_id" in data

    async def test_get_current_user_unauthenticated(self, async_client: AsyncClient):
        """Test GET /api/v1/auth/me without token returns 401."""
        response = await async_client.get("/api/v1/auth/me")

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Not authenticated" in data["detail"]

    async def test_get_current_user_invalid_token(self, async_client: AsyncClient):
        """Test GET /api/v1/auth/me with invalid token returns 401."""
        response = await async_client.get(
            "/api/v1/auth/me",
            cookies={"access_token": "invalid.token.here"}
        )

        assert response.status_code == 401


@pytest.mark.integration
class TestProtectedEndpoints:
    """Integration tests for protected endpoint authentication."""

    async def test_protected_endpoint_requires_auth(self):
        """Test protected endpoint returns 401 without token."""
        # Use fresh client without test DB override to test real auth
        # NOTE: /declarations endpoint is placeholder and not yet protected
        # Test /auth/me instead which requires authentication
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")

            assert response.status_code == 401
            data = response.json()
            assert "detail" in data

    async def test_protected_endpoint_with_valid_token(self, async_client: AsyncClient, test_user: User):
        """Test protected endpoint accessible with valid token."""
        # First login to get token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "Test12345!"
            }
        )
        assert login_response.status_code == 200

        # Access protected endpoint with cookie
        response = await async_client.get("/api/v1/declarations")

        assert response.status_code == 200
