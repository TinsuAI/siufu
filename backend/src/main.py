"""
FastAPI application entry point for Customs Declaration Automation Platform
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import settings
from src.core.database import test_db_connection
from src.core.errors import (
    CustomException,
    custom_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)

from src.core.rate_limit import limiter


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Add HSTS header in production only
        if "tinsu.ai" in settings.CORS_ORIGINS:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("Testing database connection...")
    db_connected = await test_db_connection()
    if db_connected:
        print("✓ Database connection successful")
    else:
        print("✗ Database connection failed")

    # Initialize Sentry if DSN is provided
    if settings.SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastAPIIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=0.1,  # 10% of transactions
            integrations=[
                FastAPIIntegration(),
                SqlalchemyIntegration(),
            ],
            environment="development",
        )
        print("✓ Sentry initialized")

    yield
    # Shutdown
    print("Shutting down application...")


app = FastAPI(
    title="Customs Declaration Automation Platform API",
    description="Backend API for automated customs declaration processing with AI-powered document extraction",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware configuration - uses environment variable
allowed_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Exception handlers for RFC 7807 error responses
app.add_exception_handler(CustomException, custom_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Mount API v1 router
from src.api.v1 import api_router

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "message": "Customs Declaration Automation API",
        "status": "operational",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint with dependency verification

    Tests connectivity to critical services:
    - Database (PostgreSQL)
    - Cache (Redis)

    Returns 200 if all services are healthy, 503 otherwise
    """
    import redis
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    health_status = {
        "status": "healthy",
        "services": {
            "api": "ok",
            "database": "unknown",
            "redis": "unknown",
        }
    }

    # Test database connectivity
    try:
        engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        health_status["services"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["database"] = f"error: {str(e)}"

    # Test Redis connectivity
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        r.close()
        health_status["services"]["redis"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["redis"] = f"error: {str(e)}"

    # Return 503 if any service is unhealthy
    if health_status["status"] == "unhealthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )

    return health_status
