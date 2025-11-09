"""
API v1 router initialization
"""
from fastapi import APIRouter

from src.api.v1 import auth, declarations, knowledge_base, analytics, health, corrections, companies

# Create main v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(declarations.router, prefix="/declarations", tags=["Declarations"])
api_router.include_router(corrections.router, tags=["Corrections"])  # Story 3.6 Expansion
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])  # Story 3.10 Master Data
api_router.include_router(knowledge_base.router, prefix="/knowledge-base", tags=["Knowledge Base"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(health.router)  # Health checks at /api/v1/health

__all__ = ["api_router"]
