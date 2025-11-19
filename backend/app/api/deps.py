"""
API Dependencies - Reusable dependencies for FastAPI endpoints

Provides common dependencies like service instances, authentication, etc.
"""
from typing import Optional
from fastapi import Header, HTTPException, status
from loguru import logger

from app.services.conversation_service import get_enhanced_conversation_service, EnhancedConversationService


# ============================================
# Service Dependencies
# ============================================

def get_conversation_service_dep() -> EnhancedConversationService:
    """
    Dependency for injecting ConversationService
    
    Returns:
        ConversationService instance
    """
    return get_enhanced_conversation_service()


# ============================================
# Request Tracking
# ============================================

def get_request_id(
    x_request_id: Optional[str] = Header(None)
) -> Optional[str]:
    """
    Extract request ID from headers for request tracking
    
    Args:
        x_request_id: Optional request ID from X-Request-ID header
    
    Returns:
        Request ID string or None
    """
    return x_request_id


# ============================================
# Authentication (Placeholder for Phase 2)
# ============================================

def get_current_user(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """
    Get current user from authorization header
    
    NOTE: This is a placeholder for Phase 1 (MVP)
    In Phase 3, this will validate JWT tokens and return user info
    
    Args:
        authorization: Authorization header (Bearer token)
    
    Returns:
        User ID string or None
    """
    # For MVP, we'll skip authentication
    # Return a default user ID for testing
    
    if authorization:
        # In production, validate token here
        logger.debug("Authorization header present (not validated in MVP)")
    
    # Return default user for MVP
    return "demo_user"


# ============================================
# Validation Helpers
# ============================================

async def validate_thread_exists(
    thread_id: str,
    service: EnhancedConversationService
) -> None:
    """
    Validate that a thread exists, raise 404 if not
    
    Args:
        thread_id: Thread ID to validate
        service: ConversationService instance
    
    Raises:
        HTTPException: 404 if thread not found
    """
    if not service.conversation_exists(thread_id):
        logger.warning(f"Thread not found: {thread_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation not found: {thread_id}"
        )