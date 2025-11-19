"""
API v1 Router - Aggregates all v1 endpoints
"""
from fastapi import APIRouter
from app.api.v1.endpoints import health
from app.api.v1.endpoints import conversation_endpoints

# Create main v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router)
api_router.include_router(conversation_endpoints.router)

# Future routers will be added here:
# api_router.include_router(quotes.router)
# api_router.include_router(suppliers.router)