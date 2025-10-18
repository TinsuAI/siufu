"""
API v1 router initialization
"""
from fastapi import APIRouter

from src.api.v1 import auth, declarations, knowledge_base, analytics

# Create main v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(declarations.router, prefix="/declarations", tags=["Declarations"])
api_router.include_router(knowledge_base.router, prefix="/knowledge-base", tags=["Knowledge Base"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

__all__ = ["api_router"]
