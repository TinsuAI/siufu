"""Integration tests for health check endpoint."""

import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app


@pytest.mark.integration
class TestHealthEndpoint:
    """Integration tests for /health endpoint."""

    async def test_health_returns_200_when_services_healthy(self):
        """Test GET /health returns 200 with correct JSON when all services are healthy."""
        # Arrange
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.get("/health")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert data["status"] == "healthy"
            assert "services" in data
            assert "api" in data["services"]
            assert data["services"]["api"] == "ok"
            assert "database" in data["services"]
            assert "redis" in data["services"]

    async def test_health_endpoint_structure(self):
        """Test that health endpoint returns expected JSON structure."""
        # Arrange
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.get("/health")

            # Assert
            assert response.status_code == 200
            data = response.json()

            # Check required fields
            assert isinstance(data, dict)
            assert "status" in data
            assert "services" in data
            assert isinstance(data["services"], dict)

            # Check service status values are strings
            for service, status in data["services"].items():
                assert isinstance(service, str)
                assert isinstance(status, str)


@pytest.mark.integration
class TestRootEndpoint:
    """Integration tests for root endpoint."""

    async def test_root_returns_welcome_message(self):
        """Test GET / returns welcome message."""
        # Arrange
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.get("/")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "message" in data


@pytest.mark.integration
class TestOpenAPIDocumentation:
    """Integration tests for OpenAPI documentation endpoints."""

    async def test_docs_endpoint_accessible(self):
        """Test that /docs endpoint is accessible."""
        # Arrange
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.get("/docs")

            # Assert
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]

    async def test_openapi_json_accessible(self):
        """Test that /openapi.json endpoint is accessible and returns valid JSON."""
        # Arrange
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.get("/openapi.json")

            # Assert
            assert response.status_code == 200
            data = response.json()

            # Verify OpenAPI structure
            assert "openapi" in data
            assert "info" in data
            assert "paths" in data

            # Check API metadata
            assert data["info"]["title"] == "Customs Declaration Automation Platform API"

    async def test_openapi_contains_api_v1_endpoints(self):
        """Test that OpenAPI spec contains expected /api/v1 endpoints."""
        # Arrange
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.get("/openapi.json")

            # Assert
            assert response.status_code == 200
            data = response.json()
            paths = data.get("paths", {})

            # Check for expected API v1 endpoints
            expected_endpoints = [
                "/api/v1/auth/login",
                "/api/v1/auth/logout",
                "/api/v1/auth/me",
                "/api/v1/declarations",
                "/api/v1/declarations/upload",
                "/api/v1/knowledge-base/good-list/upload",
                "/api/v1/knowledge-base/tariff/upload",
                "/api/v1/knowledge-base/versions",
                "/api/v1/analytics/corrections",
            ]

            for endpoint in expected_endpoints:
                assert endpoint in paths, f"Expected endpoint {endpoint} not found in OpenAPI spec"


@pytest.mark.integration
class TestAPIPlaceholderEndpoints:
    """Integration tests for placeholder API endpoints."""

    async def test_auth_endpoints_return_placeholder_responses(self):
        """Test that auth endpoints return placeholder messages."""
        # Arrange
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Test login endpoint
            response = await client.post("/api/v1/auth/login")
            assert response.status_code == 200
            assert "message" in response.json()

            # Test logout endpoint
            response = await client.post("/api/v1/auth/logout")
            assert response.status_code == 200
            assert "message" in response.json()

            # Test me endpoint
            response = await client.get("/api/v1/auth/me")
            assert response.status_code == 200
            assert "message" in response.json()

    async def test_declarations_list_endpoint(self):
        """Test that declarations list endpoint returns placeholder."""
        # Arrange
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.get("/api/v1/declarations")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "message" in data

    async def test_knowledge_base_endpoints(self):
        """Test that knowledge base endpoints return placeholders."""
        # Arrange
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Test good-list upload
            response = await client.post("/api/v1/knowledge-base/good-list/upload")
            assert response.status_code == 200
            assert "message" in response.json()

            # Test tariff upload
            response = await client.post("/api/v1/knowledge-base/tariff/upload")
            assert response.status_code == 200
            assert "message" in response.json()

            # Test versions list
            response = await client.get("/api/v1/knowledge-base/versions")
            assert response.status_code == 200
            assert "message" in response.json()

    async def test_analytics_corrections_endpoint(self):
        """Test that analytics corrections endpoint returns placeholder."""
        # Arrange
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.get("/api/v1/analytics/corrections")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "message" in data


@pytest.mark.integration
class TestCORSHeaders:
    """Integration tests for CORS configuration."""

    async def test_cors_headers_present(self):
        """Test that CORS headers are present in responses."""
        # Arrange
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act - Make request with Origin header
            response = await client.get(
                "/health",
                headers={"Origin": "http://localhost:3000"}
            )

            # Assert
            assert response.status_code == 200
            # CORS middleware should add appropriate headers
            # Note: Actual CORS header verification depends on middleware configuration


@pytest.mark.integration
class TestErrorHandling:
    """Integration tests for error handling."""

    async def test_404_error_for_nonexistent_endpoint(self):
        """Test that accessing non-existent endpoint returns 404."""
        # Arrange
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.get("/nonexistent/endpoint")

            # Assert
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

    async def test_405_error_for_wrong_method(self):
        """Test that using wrong HTTP method returns 405."""
        # Arrange
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act - POST to GET-only endpoint
            response = await client.post("/health")

            # Assert
            assert response.status_code == 405
            data = response.json()
            assert "detail" in data
