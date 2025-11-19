"""
Utility functions for creating standardized API responses
"""
from typing import TypeVar, Optional, Any
from fastapi import status
from fastapi.responses import JSONResponse
from app.schemas.base import APIResponse, ResponseMetadata, ErrorDetail
from datetime import datetime

DataT = TypeVar("DataT")


def success_response(
    data: Optional[DataT] = None,
    status_code: int = status.HTTP_200_OK,
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Create a successful API response
    
    Args:
        data: Response data payload
        status_code: HTTP status code (default 200)
        request_id: Optional request tracking ID
    
    Returns:
        JSONResponse with standardized format
    """
    response = APIResponse(
        success=True,
        data=data,
        error=None,
        metadata=ResponseMetadata(request_id=request_id)
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(mode='json', exclude_none=True)
    )


def error_response(
    error_code: str,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Create an error API response
    
    Args:
        error_code: Machine-readable error code
        message: Human-readable error message
        status_code: HTTP status code (default 400)
        details: Additional error context
        request_id: Optional request tracking ID
    
    Returns:
        JSONResponse with standardized error format
    """
    # Create error detail dict directly
    error_dict = {
        "code": error_code,
        "message": message
    }
    
    if details:
        error_dict["details"] = details
    
    # Create response with error as dict
    response_data = {
        "success": False,
        "data": None,
        "error": error_dict,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }
    }
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


def created_response(
    data: DataT,
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Create a 201 Created response for resource creation
    
    Args:
        data: Created resource data
        request_id: Optional request tracking ID
    
    Returns:
        JSONResponse with 201 status code
    """
    return success_response(
        data=data,
        status_code=status.HTTP_201_CREATED,
        request_id=request_id
    )


def not_found_response(
    resource: str,
    identifier: str,
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Create a 404 Not Found response
    
    Args:
        resource: Type of resource (e.g., "conversation", "quote")
        identifier: Resource identifier that wasn't found
        request_id: Optional request tracking ID
    
    Returns:
        JSONResponse with 404 status code
    """
    return error_response(
        error_code="NOT_FOUND",
        message=f"{resource.capitalize()} not found: {identifier}",
        status_code=status.HTTP_404_NOT_FOUND,
        details={"resource": resource, "identifier": identifier},
        request_id=request_id
    )


def validation_error_response(
    field: str,
    issue: str,
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Create a 422 Validation Error response
    
    Args:
        field: Field that failed validation
        issue: Description of the validation issue
        request_id: Optional request tracking ID
    
    Returns:
        JSONResponse with 422 status code
    """
    return error_response(
        error_code="VALIDATION_ERROR",
        message=f"Validation failed for field: {field}",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"field": field, "issue": issue},
        request_id=request_id
    )