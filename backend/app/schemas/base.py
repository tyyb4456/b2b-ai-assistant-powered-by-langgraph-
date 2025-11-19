"""
Base response schemas for consistent API responses
"""
from typing import Generic, TypeVar, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


DataT = TypeVar("DataT")


class ResponseMetadata(BaseModel):
    """Metadata included in every API response"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-03T10:30:00Z",
                "request_id": "req_abc123"
            }
        }


class APIResponse(BaseModel, Generic[DataT]):
    """
    Standardized API response wrapper
    
    All API endpoints should return this format for consistency
    """
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[DataT] = Field(None, description="Response data payload")
    error: Optional[str] = Field(None, description="Error message if success=false")
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"key": "value"},
                "error": None,
                "metadata": {
                    "timestamp": "2025-11-03T10:30:00Z",
                    "request_id": "req_abc123"
                }
            }
        }


class ErrorDetail(BaseModel):
    """Detailed error information"""
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(None, description="Additional error context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input parameters",
                "details": {"field": "quantity", "issue": "must be positive"}
            }
        }


class PaginationMetadata(BaseModel):
    """Pagination metadata for list endpoints"""
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there's a next page")
    has_previous: bool = Field(..., description="Whether there's a previous page")
    
    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20,
                "total_items": 150,
                "total_pages": 8,
                "has_next": True,
                "has_previous": False
            }
        }


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Response wrapper for paginated list endpoints"""
    success: bool = True
    data: list[DataT] = Field(..., description="List of items for current page")
    pagination: PaginationMetadata = Field(..., description="Pagination information")
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)