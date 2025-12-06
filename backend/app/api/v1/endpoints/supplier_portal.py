"""
Supplier Portal API Endpoints

Add to: app/api/v1/endpoints/supplier_portal.py
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from loguru import logger

from app.api.deps import get_db, get_current_supplier_user
from app.services.supplier_request_service import get_supplier_request_service
from app.utils.response import success_response, created_response, error_response
from database import SupplierUser, SupplierRequest
from loguru import logger

router = APIRouter(prefix="/supplier", tags=["supplier-portal"])

# ============================================
# REQUEST MODELS
# ============================================

class SupplierLoginRequest(BaseModel):
    email: EmailStr
    password: str


class SupplierResponseSubmit(BaseModel):
    response_text: str
    response_type: str  # accept, counteroffer, reject, clarification, delay
    response_data: Optional[dict] = None


# ============================================
# AUTHENTICATION
# ============================================

@router.post("/login")
async def supplier_login(
    credentials: SupplierLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Supplier user login
    
    Returns JWT token for authentication
    """
    # TODO: Implement proper JWT authentication
    # For now, simplified version
    
    user = db.query(SupplierUser).filter(
        SupplierUser.email == credentials.email,
        SupplierUser.is_active == True
    ).first()
    
    if not user:
        logger.warning(f"Failed login attempt for email: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    
    # TODO: Verify password hash
    if user.password_hash != credentials.password:
        logger.warning(f"Invalid password for user: {credentials.email}")
    
    # Update last login
    from datetime import datetime
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    return success_response(data={
        "access_token": f"token_{user.id}_{user.supplier_id}",  # Simplified
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "supplier_id": user.supplier_id,
            "role": user.role
        }
    })


# ============================================
# SUPPLIER REQUESTS
# ============================================

@router.get("/requests")
async def get_my_requests(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: SupplierUser = Depends(get_current_supplier_user),
    db: Session = Depends(get_db)
):
    """
    Get all requests for the logged-in supplier
    """
    service = get_supplier_request_service(db)
    
    requests = service.get_supplier_requests(
        supplier_id=current_user.supplier_id,
        status=status,
        limit=limit,
        offset=offset
    )
    
    return success_response(data={
        "requests": [
            {
                "request_id": req.request_id,
                "thread_id": req.thread_id,
                "request_type": req.request_type,
                "request_subject": req.request_subject,
                "request_message": req.request_message,
                "request_context": req.request_context,
                "status": req.status,
                "priority": req.priority,
                "created_at": req.created_at.isoformat(),
                "expires_at": req.expires_at.isoformat() if req.expires_at else None,
                "conversation_round": req.conversation_round
            }
            for req in requests
        ],
        "total": len(requests)
    })


@router.get("/requests/pending")
async def get_pending_requests(
    current_user: SupplierUser = Depends(get_current_supplier_user),
    db: Session = Depends(get_db)
):
    """
    Get all pending requests for supplier (dashboard view)
    """
    service = get_supplier_request_service(db)
    
    requests = service.get_pending_requests_for_supplier(
        supplier_id=current_user.supplier_id,
        include_expired=False
    )
    
    return success_response(data={
        "pending_requests": [
            {
                "request_id": req.request_id,
                "request_type": req.request_type,
                "request_subject": req.request_subject,
                "priority": req.priority,
                "created_at": req.created_at.isoformat(),
                "expires_at": req.expires_at.isoformat() if req.expires_at else None
            }
            for req in requests
        ],
        "count": len(requests)
    })


@router.get("/requests/{request_id}")
async def get_request_detail(
    request_id: str,
    current_user: SupplierUser = Depends(get_current_supplier_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific request
    """
    service = get_supplier_request_service(db)
    
    request = service.get_request_by_id(request_id)
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Verify ownership
    if request.supplier_id != current_user.supplier_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return success_response(data={
        "request_id": request.request_id,
        "thread_id": request.thread_id,
        "request_type": request.request_type,
        "request_subject": request.request_subject,
        "request_message": request.request_message,
        "request_context": request.request_context,
        "status": request.status,
        "priority": request.priority,
        "conversation_round": request.conversation_round,
        "created_at": request.created_at.isoformat(),
        "expires_at": request.expires_at.isoformat() if request.expires_at else None,
        "supplier_response": request.supplier_response,
        "response_data": request.response_data,
        "responded_at": request.responded_at.isoformat() if request.responded_at else None
    })


# ============================================
# SUBMIT RESPONSE
# ============================================

@router.post("/requests/{request_id}/respond")
async def submit_response(
    request_id: str,
    response: SupplierResponseSubmit,
    request: Request,
    current_user: SupplierUser = Depends(get_current_supplier_user),
    db: Session = Depends(get_db)
):
    """
    Submit supplier response (only store, do NOT resume workflow)
    
    This endpoint:
    1. Saves supplier response
    2. Updates request status to "responded"
    3. Does NOT trigger workflow resume
    4. Frontend will manually resume workflow when ready
    """
    logger.info(f"📝 Supplier response received for request: {request_id}")
    logger.info(f"Response Type: {response.response_type}")
    logger.info(f"Response Text: {response.response_text}")
    logger.info(f"Response Data: {response.response_data}")
    
    service = get_supplier_request_service(db)
    
    # Verify request exists and belongs to supplier
    req = service.get_request_by_id(request_id)
    
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if req.supplier_id != current_user.supplier_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if req.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Request is not pending: {req.status}"
        )
    
    # Submit response (store only, no auto-resume)
    try:
        result = await service.submit_supplier_response(
            request_id=request_id,
            supplier_user_id=current_user.id,
            response_text=response.response_text,
            response_type=response.response_type,
            response_data=response.response_data,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        logger.success(f"✅ Response stored (not auto-resumed): {request_id}")
        
        return success_response(data=result)
        
    except Exception as e:
        logger.error(f"❌ Failed to submit response: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit response: {str(e)}"
        )


# ============================================
# MANUAL WORKFLOW RESUME
# ============================================

@router.post("/requests/{request_id}/resume-workflow")
async def resume_workflow(
    request_id: str,
    db: Session = Depends(get_db)
):
    """
    Manually resume workflow after supplier response (called from frontend)
    
    This endpoint is called by the buyer's frontend (App A) to manually
    resume the workflow after reviewing the supplier's response.
    """
    logger.info(f"🚀 Manual workflow resume requested for request: {request_id}")
    
    service = get_supplier_request_service(db)
    
    # Verify request exists
    req = service.get_request_by_id(request_id)
    
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if req.status != "responded":
        raise HTTPException(
            status_code=400,
            detail=f"Request must be in 'responded' status to resume, current: {req.status}"
        )
    
    # Trigger workflow resume
    try:
        resume_result = await service._trigger_workflow_resume(
            req,
            req.supplier_response
        )
        
        logger.success(f"✅ Workflow resumed successfully: {request_id}")
        
        return success_response(data={
            "request_id": request_id,
            "thread_id": req.thread_id,
            "workflow_resumed": True,
            "resume_status": resume_result["status"],
            "trigger_id": resume_result["trigger_id"]
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to resume workflow: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume workflow: {str(e)}"
        )


# ============================================
# NOTIFICATIONS
# ============================================

@router.get("/notifications")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 20,
    current_user: SupplierUser = Depends(get_current_supplier_user),
    db: Session = Depends(get_db)
):
    """
    Get notifications for supplier user
    """
    from database import SupplierNotification
    
    query = db.query(SupplierNotification).filter(
        SupplierNotification.supplier_user_id == current_user.id
    )
    
    if unread_only:
        query = query.filter(SupplierNotification.is_read == False)
    
    notifications = query.order_by(
        SupplierNotification.sent_at.desc()
    ).limit(limit).all()
    
    return success_response(data={
        "notifications": [
            {
                "notification_id": notif.notification_id,
                "notification_type": notif.notification_type,
                "title": notif.title,
                "message": notif.message,
                "request_id": notif.request_id,
                "sent_at": notif.sent_at.isoformat(),
                "is_read": notif.is_read,
                "read_at": notif.read_at.isoformat() if notif.read_at else None
            }
            for notif in notifications
        ],
        "count": len(notifications)
    })


@router.post("/notifications/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: str,
    current_user: SupplierUser = Depends(get_current_supplier_user),
    db: Session = Depends(get_db)
):
    """
    Mark notification as read
    """
    from database import SupplierNotification
    from datetime import datetime
    
    notification = db.query(SupplierNotification).filter(
        SupplierNotification.notification_id == notification_id,
        SupplierNotification.supplier_user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.commit()
    
    return success_response(message="Notification marked as read")
