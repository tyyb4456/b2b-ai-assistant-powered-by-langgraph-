"""
FastAPI Application Entry Point - Root Level

Run with: uvicorn main:app --reload
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import api_router
from app.services.graph_manager import get_graph_manager
from app.utils.response import error_response


# ============================================
# Lifespan Management (Startup/Shutdown)
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events
    
    Startup:
    - Initialize logging
    - Initialize LangGraph
    - Load necessary resources
    
    Shutdown:
    - Clean up database connections
    - Close external connections
    """
    # Startup
    logger.info("-" * 40)
    logger.info("Starting B2B Textile Procurement API")
    logger.info(f"Version: {settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info("-" * 40)
    
    # Initialize graph manager (creates connection)
    graph_manager = get_graph_manager()
    logger.success("LangGraph initialized")
    
    yield
    
    # Shutdown
    logger.info("-" * 30)
    logger.info("Shutting down B2B Textile Procurement API")
    graph_manager.cleanup()
    logger.success("Cleanup completed")
    logger.info("-" * 30)


# ============================================
# Create FastAPI Application
# ============================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    debug=settings.DEBUG
)


# ============================================
# Middleware Configuration
# ============================================

# CORS Middleware - Allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip Compression Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ============================================
# Request Logging Middleware
# ============================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code}")
    return response


# ============================================
# Include Routers
# ============================================

# Include API v1 router
app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX
)


# ============================================
# Root Endpoint
# ============================================

@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint - API information
    
    Returns basic API information and links to documentation
    """
    return {
        "message": "B2B Textile Procurement API",
        "version": settings.APP_VERSION,
        "status": "running",
        "documentation": {
            "interactive": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "endpoints": {
            "health": f"{settings.API_V1_PREFIX}/health",
            "conversations": f"{settings.API_V1_PREFIX}/conversations"
        }
    }


# ============================================
# Exception Handlers
# ============================================

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions"""
    logger.warning(f"ValueError: {exc}")
    return error_response(
        error_code="INVALID_VALUE",
        message=str(exc),
        status_code=400
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error("Unexpected error occurred", exc_info=True)
    return error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        status_code=500,
        details={"error": str(exc)} if settings.DEBUG else None
    )