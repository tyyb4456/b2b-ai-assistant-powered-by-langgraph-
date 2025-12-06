"""
Supplier Request Service - Manages supplier request lifecycle
FIXED: Removed circular import by importing graph_manager inside methods

Add to: app/services/supplier_request_service.py
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database import (
    SupplierRequest, 
    SupplierUser, 
    SupplierResponseHistory,
    WorkflowResumeTrigger,
    SupplierNotification,
    SupplierRequestStatus
)
import uuid


class SupplierRequestService:
    """Service for managing supplier requests and responses"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # ============================================
    # CREATE SUPPLIER REQUEST
    # ============================================
    
    async def create_supplier_request(
        self,
        thread_id: str,
        supplier_id: str,
        request_type: str,
        request_subject: str,
        request_message: str,
        request_context: Optional[Dict[str, Any]] = None,
        priority: str = "medium",
        expires_in_hours: Optional[int] = 72
    ) -> SupplierRequest:
        """Create a new supplier request when workflow pauses"""
        
        logger.info(f"Creating supplier request for thread: {thread_id}, supplier: {supplier_id}")
        
        # Generate unique request ID
        request_id = f"REQ-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours) if expires_in_hours else None
        
        # 🔥 FIX: Import here to avoid circular import
        from app.services.graph_manager import get_graph_manager
        graph_manager = get_graph_manager()
        
        # Get conversation round from graph state
        state = await graph_manager.get_state(thread_id)
        conversation_round = state.get("negotiation_rounds", 1) if state else 1
        
        # Create request
        request = SupplierRequest(
            request_id=request_id,
            thread_id=thread_id,
            conversation_round=conversation_round,
            supplier_id=supplier_id,
            request_type=request_type,
            request_subject=request_subject,
            request_message=request_message,
            request_context=request_context,
            status=SupplierRequestStatus.PENDING.value,
            priority=priority,
            expires_at=expires_at,
            created_at=datetime.utcnow()
        )
        
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        
        logger.success(f"Supplier request created: {request_id}")
        
        # Send notification to supplier
        await self._send_request_notification(request)
        
        return request
    
    # ============================================
    # SUPPLIER RESPONSE HANDLING
    # ============================================
    
    async def submit_supplier_response(
        self,
        request_id: str,
        supplier_user_id: int,
        response_text: str,
        response_type: str,
        response_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit supplier response (store only, do NOT resume workflow)"""
        
        logger.info(f"Processing supplier response for request: {request_id}")
        
        # Fetch request
        request = self.db.query(SupplierRequest).filter(
            SupplierRequest.request_id == request_id
        ).first()
        
        if not request:
            raise ValueError(f"Request not found: {request_id}")
        
        if request.status != SupplierRequestStatus.PENDING.value:
            raise ValueError(f"Request is not pending: {request.status}")
        
        # Update request with response
        request.supplier_response = response_text
        request.response_data = response_data
        request.responded_at = datetime.utcnow()
        request.status = SupplierRequestStatus.RESPONDED.value
        
        # Create response history record
        response_history = SupplierResponseHistory(
            request_id=request_id,
            supplier_user_id=supplier_user_id,
            response_text=response_text,
            response_data=response_data,
            response_type=response_type,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )
        
        self.db.add(response_history)
        self.db.commit()
        
        logger.success(f"Supplier response saved: {request_id}")
        
        # 🔥 UPDATE conversation state with current_request_id so App A can see it
        try:
            from app.services.graph_manager import get_graph_manager
            graph_manager = get_graph_manager()
            
            logger.info(f"submit_supplier_response Attempting to update state for thread: {request.thread_id}")

            # Update current_request_id and current_round_status so App A can see it
            update_dict = {
                'current_request_id': request_id,
                'current_round_status': 'awaiting_supplier_response_review'
            }
            logger.info(f"submit_supplier_response Setting current_request_id to: {request_id}")
            
            # Update the state without running workflow
            success = await graph_manager.update_state(request.thread_id, update_dict)
            
            if success:
                logger.success(f"submit_supplier_response Updated conversation state with current_request_id: {request_id}")
                
                # Verify the update
                updated_state = await graph_manager.get_state(request.thread_id)
                verified_request_id = updated_state.get('current_request_id') if updated_state else None
                logger.info(f"submit_supplier_response VERIFICATION - current_request_id in state now: {verified_request_id}")
            else:
                logger.warning(f"submit_supplier_response State update returned False for thread: {request.thread_id}")
        except Exception as e:
            logger.warning(f"submit_supplier_response Could not update conversation state with request_id: {e}")
            import traceback
            logger.error(f"submit_supplier_response Traceback: {traceback.format_exc()}")
        
        return {
            "request_id": request_id,
            "response_recorded": True,
            "thread_id": request.thread_id,
            "message": "Response stored successfully. Awaiting manual workflow resume."
        }
    
    # ============================================
    # WORKFLOW RESUME TRIGGER
    # ============================================
    
    async def _trigger_workflow_resume(
        self, 
        request: SupplierRequest,
        supplier_response: str
    ) -> Dict[str, Any]:
        """Trigger workflow resume after supplier response"""
        
        logger.info(f"🚀 Triggering workflow resume for thread: {request.thread_id}")
        
        trigger_id = f"TRIG-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        
        # Create trigger record
        trigger = WorkflowResumeTrigger(
            trigger_id=trigger_id,
            thread_id=request.thread_id,
            request_id=request.request_id,
            triggered_at=datetime.utcnow(),
            trigger_type="supplier_response",
            resume_status="pending"
        )
        
        self.db.add(trigger)
        self.db.commit()
        
        try:
            # 🔥 FIX: Import here to avoid circular import
            from app.services.graph_manager import get_graph_manager
            graph_manager = get_graph_manager()
            
            trigger.resume_status = "processing"
            trigger.resume_started_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Resuming workflow: {request.thread_id}")
            
            # Use graph manager's resume method
            events = []
            async for event in graph_manager.resume_with_supplier_response(
                request.thread_id,
                supplier_response
            ):
                events.append(event)
                logger.debug(f"Resume event: {list(event.keys())}")
            
            # Mark as completed
            trigger.resume_status = "completed"
            trigger.resume_completed_at = datetime.utcnow()
            self.db.commit()
            
            logger.success(f"Workflow resumed successfully: {request.thread_id}")
            
            return {
                "triggered": True,
                "status": "completed",
                "trigger_id": trigger_id,
                "events_count": len(events)
            }
            
        except Exception as e:
            logger.error(f"Failed to resume workflow: {e}")
            
            trigger.resume_status = "failed"
            trigger.error_message = str(e)
            trigger.retry_count += 1
            self.db.commit()
            
            return {
                "triggered": True,
                "status": "failed",
                "trigger_id": trigger_id,
                "error": str(e)
            }
    
    # ============================================
    # QUERY METHODS
    # ============================================
    
    def get_supplier_requests(
        self,
        supplier_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[SupplierRequest]:
        """Get supplier requests with filters"""
        query = self.db.query(SupplierRequest)
        
        if supplier_id:
            query = query.filter(SupplierRequest.supplier_id == supplier_id)
        
        if status:
            query = query.filter(SupplierRequest.status == status)
        
        return query.order_by(SupplierRequest.created_at.desc()).limit(limit).offset(offset).all()
    
    def get_request_by_id(self, request_id: str) -> Optional[SupplierRequest]:
        """Get single request by ID"""
        return self.db.query(SupplierRequest).filter(
            SupplierRequest.request_id == request_id
        ).first()
    
    def get_pending_requests_for_supplier(
        self,
        supplier_id: str,
        include_expired: bool = False
    ) -> List[SupplierRequest]:
        """Get all pending requests for a supplier"""
        query = self.db.query(SupplierRequest).filter(
            and_(
                SupplierRequest.supplier_id == supplier_id,
                SupplierRequest.status == SupplierRequestStatus.PENDING.value
            )
        )
        
        if not include_expired:
            query = query.filter(
                or_(
                    SupplierRequest.expires_at.is_(None),
                    SupplierRequest.expires_at > datetime.utcnow()
                )
            )
        
        return query.order_by(SupplierRequest.created_at.desc()).all()
    
    # ============================================
    # NOTIFICATION METHODS
    # ============================================
    
    async def _send_request_notification(self, request: SupplierRequest):
        """Send notification to supplier users"""
        logger.info(f"📧 Sending notification for request: {request.request_id}")
        
        # Get supplier users
        supplier_users = self.db.query(SupplierUser).filter(
            and_(
                SupplierUser.supplier_id == request.supplier_id,
                SupplierUser.is_active == True
            )
        ).all()
        
        for user in supplier_users:
            notification = SupplierNotification(
                notification_id=f"NOTIF-{uuid.uuid4().hex[:12].upper()}",
                supplier_user_id=user.id,
                request_id=request.request_id,
                notification_type="new_request",
                title=f"New Request: {request.request_subject}",
                message=f"You have a new {request.request_type} request. Priority: {request.priority}",
                channel="in_app",
                sent_at=datetime.utcnow()
            )
            
            self.db.add(notification)
        
        # Mark notification sent
        request.notification_sent_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.success(f"Notifications sent to {len(supplier_users)} users")
    
    # ============================================
    # EXPIRATION HANDLING
    # ============================================
    
    def expire_old_requests(self) -> int:
        """Mark expired requests - run periodically"""
        expired_count = self.db.query(SupplierRequest).filter(
            and_(
                SupplierRequest.status == SupplierRequestStatus.PENDING.value,
                SupplierRequest.expires_at.isnot(None),
                SupplierRequest.expires_at < datetime.utcnow()
            )
        ).update({
            "status": SupplierRequestStatus.EXPIRED.value
        })
        
        self.db.commit()
        
        if expired_count > 0:
            logger.warning(f"Expired {expired_count} old requests")
        
        return expired_count


# Global service instance
def get_supplier_request_service(db: Session) -> SupplierRequestService:
    """Dependency injection for FastAPI"""
    return SupplierRequestService(db)