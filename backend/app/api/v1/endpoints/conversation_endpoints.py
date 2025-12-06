"""
Complete Conversation API Endpoints - All Routes in One File

Provides comprehensive endpoints for conversation management including:
- Standard REST endpoints for CRUD operations
- Detailed data exposure endpoints (comprehensive, quote, negotiation)
- Real-time SSE streaming endpoints
- Utility endpoints for specific data access StartConversationRequest
"""
from typing import Optional, AsyncIterator
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger
import asyncio
# from starlette.responses import StreamingResponse as StarletteStreamingResponse

from app.schemas.conversation_schemas import (
    ConversationComprehensiveResponse,
    QuoteWorkflowResponse,
    NegotiationWorkflowResponse,
    StartConversationRequest,
    ResumeConversationRequest,
    ContinueConversationRequest,
)
from app.schemas.base import APIResponse
from app.utils.response import (
    success_response,
    created_response,
    not_found_response,
    error_response
)
from app.api.deps import (
    get_request_id,
    get_current_user,
    validate_thread_exists
)
from app.services.conversation_service import (
    get_enhanced_conversation_service,
    EnhancedConversationService
)
from datetime import datetime

router = APIRouter(prefix="/conversations", tags=["conversations"])


# ============================================
# DEPENDENCY INJECTION
# ============================================

def get_enhanced_service_dep() -> EnhancedConversationService:
    """Dependency for injecting EnhancedConversationService"""
    return get_enhanced_conversation_service()


# ============================================
# SSE EVENT FORMATTING UTILITIES
# ============================================

"""
FIXED: Backend SSE Streaming for Real-Time Updates
"""

async def stream_workflow_events(
    service: EnhancedConversationService,
    thread_id: str,
    initial_state: Optional[dict] = None,
    workflow_type: str = "start"
) -> AsyncIterator[bytes]:  # 🔥 Changed from str to bytes
    """
    Stream workflow execution events as SSE
    
    FIXED: Yield bytes to ensure proper streaming without buffering
    """
    try:
        # Send connection established event
        event_data = format_sse_event("connected", {
            "thread_id": thread_id,
            "workflow_type": workflow_type,
            "timestamp": datetime.utcnow().isoformat()
        })
        logger.info(f"[SSE] Sending connected event, size: {len(event_data)}")
        yield event_data.encode('utf-8')  # 🔥 Encode to bytes
        await asyncio.sleep(0.1)  # 🔥 CRITICAL: Force immediate flush to client
        
        logger.info(f"[SSE] Starting stream for thread: {thread_id}")
        
        # Choose the right workflow method
        if workflow_type == "start":
            events_generator = service.graph_manager.execute_workflow(
                thread_id, 
                initial_state
            )
        elif workflow_type == "resume":
            supplier_response = initial_state.get("supplier_response", "")
            events_generator = service.graph_manager.resume_with_supplier_response(
                thread_id,
                supplier_response
            )
        elif workflow_type == "continue":
            user_input = initial_state.get("user_input", "")
            updates = {"user_input": user_input}
            events_generator = service.graph_manager.continue_workflow(
                thread_id,
                updates
            )
        else:
            raise ValueError(f"Unknown workflow_type: {workflow_type}")
        
        # Process workflow events
        async for event in events_generator:
            logger.debug(f"[SSE] Raw event: {type(event)}")
            
            # Check for errors first
            if isinstance(event, dict) and "error" in event:
                logger.error(f"[SSE] Workflow error: {event['error']}")
                event_data = format_sse_event("error", {
                    "thread_id": thread_id,
                    "error": str(event["error"])
                })
                yield event_data.encode('utf-8')
                await asyncio.sleep(0.1)  # 🔥 Force flush
                break

            # Skip LangGraph tuple events (these are commands like interrupts, not state updates)
            if isinstance(event, tuple):
                logger.debug(f"[SSE] Skipping LangGraph command tuple: {type(event)}")
                continue
            
            
            # LangGraph format: {"node_name": {...state_updates...}}
            if not isinstance(event, dict) or not event:
                logger.warning(f"[SSE] Skipping invalid event: {type(event)}")
                continue
            
            # Extract node name (first key)
            node_name = next(iter(event.keys()))
            node_data = event[node_name]
            
            logger.info(f"[SSE] Processing node: {node_name}")
            
            # Ensure node_data is a dict
            if not isinstance(node_data, dict):
                logger.warning(f"[SSE] Node data is not dict: {type(node_data)}")
                if hasattr(node_data, 'model_dump'):
                    node_data = node_data.model_dump()
                elif hasattr(node_data, 'dict'):
                    node_data = node_data.dict()
                else:
                    # Skip events where we can't extract a dict
                    logger.warning(f"[SSE] Cannot convert node_data to dict, skipping")
                    continue
            
            # Send node progress event
            event_data = format_sse_event("node_progress", {
                "node": node_name,
                "status": node_data.get("status", "processing"),
                "intent": node_data.get("intent"),
                "next_step": node_data.get("next_step")
            })
            logger.info(f"[SSE] Sending node_progress event, size: {len(event_data)}")
            yield event_data.encode('utf-8')
            await asyncio.sleep(0.15)  # 🔥 INCREASED: Force flush between events (150ms for visibility)
            
            # Extract and send messages
            messages = node_data.get("messages")
            if messages:
                logger.debug(f"[SSE] Found messages: {type(messages)}")
                
                if isinstance(messages, list):
                    message_list = messages
                elif isinstance(messages, str):
                    message_list = [messages]
                elif hasattr(messages, '__iter__'):
                    message_list = list(messages)
                else:
                    message_list = [messages]
                
                for msg in message_list:
                    msg_content = None
                    msg_role = "assistant"
                    
                    if isinstance(msg, dict):
                        msg_content = msg.get("content", "")
                        msg_role = msg.get("role", "assistant")
                    elif isinstance(msg, str):
                        msg_content = msg
                    elif hasattr(msg, 'content'):
                        msg_content = msg.content
                        msg_role = getattr(msg, 'role', 'assistant')
                    else:
                        logger.warning(f"[SSE] Unknown message type: {type(msg)}")
                        continue
                    
                    if msg_content:
                        event_data = format_sse_event("message", {
                            "node": node_name,
                            "role": msg_role,
                            "content": str(msg_content)[:500],
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        logger.info(f"[SSE] Sending message event, size: {len(event_data)}")
                        yield event_data.encode('utf-8')
                        await asyncio.sleep(0.1)  # 🔥 Force flush
            
            # Send specific events for important nodes
            if node_name == "classify_intent":
                intent = node_data.get("intent")
                if intent:
                    logger.info(f"[SSE] Intent classified: {intent}")
                    event_data = format_sse_event("intent_classified", {
                        "node": node_name,
                        "intent": intent,
                        "confidence": node_data.get("intent_confidence", 0)
                    })
                    yield event_data.encode('utf-8')
            
            elif node_name == "extract_parameters":
                params = node_data.get("extracted_parameters")
                if params:
                    logger.info(f"[SSE] Parameters extracted")
                    params_dict = service._to_dict(params)
                    fabric_details = params_dict.get("fabric_details", {}) if params_dict else {}
                    
                    event_data = format_sse_event("parameters_extracted", {
                        "node": node_name,
                        "parameters": {
                            "fabric_type": fabric_details.get("type"),
                            "quantity": fabric_details.get("quantity"),
                            "unit": fabric_details.get("unit"),
                        }
                    })
                    yield event_data.encode('utf-8')
            
            elif node_name == "search_suppliers_direct_sql":
                suppliers = node_data.get("top_suppliers", [])
                if suppliers:
                    logger.info(f"[SSE] Found {len(suppliers)} suppliers")
                    supplier_list = []
                    for s in suppliers[:3]:
                        s_dict = service._to_dict(s)
                        if s_dict:
                            supplier_list.append({
                                "name": s_dict.get("name"),
                                "location": s_dict.get("location"),
                                "price": s_dict.get("price_per_unit")
                            })
                    
                    event_data = format_sse_event("suppliers_found", {
                        "node": node_name,
                        "count": len(suppliers),
                        "suppliers": supplier_list
                    })
                    yield event_data.encode('utf-8')
            
            elif node_name == "generate_quote":
                quote_id = node_data.get("quote_id")
                if quote_id:
                    logger.info(f"[SSE] Quote generated: {quote_id}")
                    event_data = format_sse_event("quote_generated", {
                        "node": node_name,
                        "quote_id": quote_id,
                        "estimated_savings": node_data.get("estimated_savings")
                    })
                    yield event_data.encode('utf-8')
            
            elif node_name == "draft_negotiation_message":
                drafted_msg = node_data.get("drafted_message")
                if drafted_msg:
                    logger.info(f"[SSE] Negotiation message drafted")
                    event_data = format_sse_event("message_drafted", {
                        "node": node_name,
                        "message_id": node_data.get("message_id"),
                        "confidence": node_data.get("last_message_confidence")
                    })
                    yield event_data.encode('utf-8')
            
            elif node_name == "analyze_supplier_response":
                intent = node_data.get("supplier_intent")
                if intent:
                    logger.info(f"[SSE] Supplier response analyzed")
                    intent_dict = service._to_dict(intent)
                    event_data = format_sse_event("response_analyzed", {
                        "node": node_name,
                        "intent": intent_dict.get("intent") if intent_dict else None,
                        "sentiment": intent_dict.get("sentiment") if intent_dict else None
                    })
                    yield event_data.encode('utf-8')
            
            # Small delay between events - forces buffer flush
            await asyncio.sleep(0.15)  # 🔥 INCREASED for better visibility
        
        # Get final state and send completion
        logger.info(f"[SSE] Workflow generator exhausted, fetching final state")
        await asyncio.sleep(0.2)
        
        final_state = await service.graph_manager.get_state(thread_id)
        is_paused = await service.graph_manager.is_workflow_paused(thread_id)
        
        logger.info(f"[SSE] Final state - status: {final_state.get('status') if final_state else 'unknown'}, paused: {is_paused}")
        
        event_data = format_sse_event("workflow_complete", {
            "thread_id": thread_id,
            "status": final_state.get("status") if final_state else "completed",
            "is_paused": is_paused,
            "next_step": final_state.get("next_step") if final_state else None
        })
        yield event_data.encode('utf-8')
        
        # Send close event
        event_data = format_sse_event("close", {
            "thread_id": thread_id,
            "message": "Stream completed successfully"
        })
        yield event_data.encode('utf-8')
        
        logger.success(f"[SSE] Stream completed for thread: {thread_id}")
        
    except Exception as e:
        logger.error(f"[SSE] Error streaming workflow for {thread_id}: {e}", exc_info=True)
        event_data = format_sse_event("error", {
            "thread_id": thread_id,
            "error": str(e)
        })
        yield event_data.encode('utf-8')


def format_sse_event(event_type: str, data: dict) -> str:
    """
    Format data as Server-Sent Event with explicit keepalive
    
    Format includes comment to trigger buffer flush
    """
    # 🔥 Include event type INSIDE the data
    data_with_type = {"type": event_type, **data}
    json_data = json.dumps(data_with_type, default=str)
    
    # 🔥 Add a comment line BEFORE the data to force buffer flush
    # Comments are ignored by SSE parsers but force TCP packet transmission
    event_str = f": ping\ndata: {json_data}\n\n"
    
    logger.debug(f"[SSE] Formatting event: {event_type}, length: {len(event_str)}")
    
    return event_str

# ============================================
# STANDARD REST ENDPOINTS
# ============================================

# @router.post(
#     "",
#     response_model=APIResponse[dict],
#     status_code=status.HTTP_201_CREATED,
#     summary="Start a new conversation",
#     description="Initialize a new conversation workflow with user input"
# )
# async def start_conversation(
#     request: StartConversationRequest,
#     service: EnhancedConversationService = Depends(get_enhanced_service_dep),
#     request_id: Optional[str] = Depends(get_request_id),
#     user_id: Optional[str] = Depends(get_current_user)
# ):
#     """
#     Start a new conversation workflow
    
#     **Request Body:**
#     - user_input: Initial user message (required)
#     - recipient_email: Email for quote delivery (optional)
#     - channel: Communication channel (default: "api")
    
#     **Returns:**
#     - thread_id: Unique conversation identifier
#     - status: Current workflow status
#     - intent: Classified user intent
#     - is_paused: Whether workflow is waiting for input
#     """
#     logger.info(f"Starting new conversation for user: {user_id}")
    
#     try:
#         result = await service.start_conversation(
#             user_input=request.user_input,
#             recipient_email=request.recipient_email,
#             channel=request.channel,
#             user_id=user_id
#         )
        
#         logger.success(f"Conversation started: {result['thread_id']}")
        
#         return created_response(
#             data=result,
#             request_id=request_id
#         )
        
#     except Exception as e:
#         logger.error(f"Failed to start conversation: {e}")
#         return error_response(
#             error_code="WORKFLOW_EXECUTION_FAILED",
#             message=f"Failed to start conversation: {str(e)}",
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             request_id=request_id
#         )


@router.get(
    "",
    response_model=APIResponse[list[dict]],
    summary="List conversations",
    description="Get a list of conversations (optionally filtered by user)"
)
async def list_conversations(
    limit: int = 20,
    service: EnhancedConversationService = Depends(get_enhanced_service_dep),
    request_id: Optional[str] = Depends(get_request_id),
    user_id: Optional[str] = Depends(get_current_user)
):
    """
    List conversations
    
    **Query Parameters:**
    - limit: Maximum number of conversations to return (default: 20)
    
    **Returns:**
    - List of conversation summaries with:
      - thread_id
      - status
      - intent
      - preview (first 100 chars)
      - timestamps
    """
    logger.debug(f"Listing conversations for user: {user_id}")
    
    conversations = await service.list_conversations(
        user_id=user_id,
        limit=limit
    )
    
    return success_response(
        data=conversations,
        request_id=request_id
    )


# @router.post(
#     "/{thread_id}/resume",
#     response_model=APIResponse[dict],
#     summary="Resume conversation with supplier response",
#     description="Resume a paused conversation with supplier's response"
# )
# async def resume_conversation(
#     thread_id: str,
#     request: ResumeConversationRequest,
#     service: EnhancedConversationService = Depends(get_enhanced_service_dep),
#     request_id: Optional[str] = Depends(get_request_id),
#     user_id: Optional[str] = Depends(get_current_user)
# ):
#     """
#     Resume a paused conversation with supplier response
    
#     **Path Parameters:**
#     - thread_id: Conversation identifier
    
#     **Request Body:**
#     - supplier_response: Supplier's response message
    
#     **Returns:**
#     - Updated conversation status
#     - New negotiation round number
#     - Whether still paused (for multi-round negotiations)
    
#     **Use Cases:**
#     - Continue negotiation after supplier responds
#     - Handle multi-round negotiations
#     - Progress towards contract or alternative actions
#     """
#     logger.info(f"Resuming conversation: {thread_id}")
    
#     try:
#         result = await service.resume_with_supplier_response(
#             thread_id=thread_id,
#             supplier_response=request.supplier_response
#         )
        
#         logger.success(f"Conversation resumed: {thread_id}")
        
#         return success_response(
#             data=result,
#             request_id=request_id
#         )
        
#     except ValueError as e:
#         logger.warning(f"Invalid resume request: {e}")
#         return error_response(
#             error_code="INVALID_OPERATION",
#             message=str(e),
#             status_code=status.HTTP_400_BAD_REQUEST,
#             request_id=request_id
#         )
#     except Exception as e:
#         logger.error(f"Failed to resume conversation: {e}")
#         return error_response(
#             error_code="WORKFLOW_EXECUTION_FAILED",
#             message=f"Failed to resume conversation: {str(e)}",
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             request_id=request_id
#         )


# @router.post(
#     "/{thread_id}/continue",
#     response_model=APIResponse[dict],
#     summary="Continue conversation with new input",
#     description="Continue an existing conversation with new user message"
# )
# async def continue_conversation(
#     thread_id: str,
#     request: ContinueConversationRequest,
#     service: EnhancedConversationService = Depends(get_enhanced_service_dep),
#     request_id: Optional[str] = Depends(get_request_id),
#     user_id: Optional[str] = Depends(get_current_user)
# ):
#     """
#     Continue conversation with new user input
    
#     **Path Parameters:**
#     - thread_id: Conversation identifier
    
#     **Request Body:**
#     - user_input: New user message
    
#     **Returns:**
#     - Updated conversation status
    
#     **Use Cases:**
#     - Start new quote request in same conversation
#     - Modify requirements
#     - Ask follow-up questions
#     """
#     logger.info(f"Continuing conversation: {thread_id}")
    
#     try:
#         result = await service.continue_conversation(
#             thread_id=thread_id,
#             user_input=request.user_input
#         )
        
#         logger.success(f"Conversation continued: {thread_id}")
        
#         return success_response(
#             data=result,
#             request_id=request_id
#         )
        
#     except ValueError as e:
#         logger.warning(f"Invalid continue request: {e}")
#         return error_response(
#             error_code="INVALID_OPERATION",
#             message=str(e),
#             status_code=status.HTTP_400_BAD_REQUEST,
#             request_id=request_id
#         )
#     except Exception as e:
#         logger.error(f"Failed to continue conversation: {e}")
#         return error_response(
#             error_code="WORKFLOW_EXECUTION_FAILED",
#             message=f"Failed to continue conversation: {str(e)}",
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             request_id=request_id
#         )


# ============================================
# DETAILED DATA EXPOSURE ENDPOINTS
# ============================================

@router.get(
    "/{thread_id}/comprehensive",
    response_model=APIResponse[ConversationComprehensiveResponse],
    summary="Get COMPREHENSIVE conversation details",
    description="Retrieve ALL conversation data including extracted parameters, suppliers, quotes, negotiation state, contracts, etc."
)
async def get_conversation_comprehensive(
    thread_id: str,
    service: EnhancedConversationService = Depends(get_enhanced_service_dep),
    request_id: Optional[str] = Depends(get_request_id),
    user_id: Optional[str] = Depends(get_current_user)
):
    """
    Get COMPREHENSIVE conversation information with ALL state data
    
    **Path Parameters:**
    - thread_id: Conversation identifier
    
    **Returns:**
    - Complete conversation state including:
      - Extracted parameters (fabric details, quantity, specs, etc.)
      - Supplier search results with scores and market insights
      - Full quote details with supplier options and analysis
      - Negotiation state (strategy, messages, validation)
      - Supplier response analysis (intent, terms, recommendations)
      - Clarification handling details
      - Contract generation data
      - Follow-up schedules
      - Next steps recommendations
      - And much more!
    
    **Use Cases:**
    - Display comprehensive dashboard for a conversation
    - Debug/audit workflow state
    - Generate detailed reports
    - Analytics and insights
    """
    logger.debug(f"Retrieving comprehensive conversation: {thread_id}")
    
    conversation = await service.get_conversation_comprehensive(thread_id)
    
    if not conversation:
        return not_found_response(
            resource="conversation",
            identifier=thread_id,
            request_id=request_id
        )
    
    return success_response(
        data=conversation,
        request_id=request_id
    )


@router.get(
    "/{thread_id}/quote",
    response_model=APIResponse[QuoteWorkflowResponse],
    summary="Get quote workflow details",
    description="Retrieve detailed information for quote generation workflow"
)
async def get_quote_workflow(
    thread_id: str,
    service: EnhancedConversationService = Depends(get_enhanced_service_dep),
    request_id: Optional[str] = Depends(get_request_id),
    user_id: Optional[str] = Depends(get_current_user)
):
    """
    Get detailed quote workflow information
    
    **Path Parameters:**
    - thread_id: Conversation identifier
    
    **Returns:**
    - Extracted parameters (fabric type, quantity, specs)
    - Supplier search results with rankings
    - Complete quote with:
      - Multiple supplier options
      - Cost breakdowns (material + logistics)
      - Lead times and reliability scores
      - Strategic analysis and recommendations
      - Negotiation opportunities
    - Email/PDF generation status
    
    **Use Cases:**
    - Display quote results to buyer
    - Compare supplier options
    - Show cost analysis
    - Track quote delivery status
    """
    logger.debug(f"Retrieving quote workflow: {thread_id}")
    
    quote_details = await service.get_quote_workflow_details(thread_id)
    
    if not quote_details:
        return not_found_response(
            resource="quote workflow",
            identifier=thread_id,
            request_id=request_id
        )
    
    return success_response(
        data=quote_details,
        request_id=request_id
    )


@router.get(
    "/{thread_id}/negotiation",
    response_model=APIResponse[NegotiationWorkflowResponse],
    summary="Get negotiation workflow details",
    description="Retrieve detailed information for negotiation workflow"
)
async def get_negotiation_workflow(
    thread_id: str,
    service: EnhancedConversationService = Depends(get_enhanced_service_dep),
    request_id: Optional[str] = Depends(get_request_id),
    user_id: Optional[str] = Depends(get_current_user)
):
    """
    Get detailed negotiation workflow information
    
    **Path Parameters:**
    - thread_id: Conversation identifier
    
    **Returns:**
    - Negotiation state:
      - Current round number
      - Negotiation topic and objective
      - Drafted messages with confidence scores
      - Negotiation strategy and approach
      - Message validation results
    - Supplier response analysis:
      - Intent classification (accept/reject/counteroffer/clarification/delay)
      - Sentiment analysis
      - Extracted terms (price, lead time, payment, etc.)
      - Strategic recommendations
    - Clarification handling (if needed)
    - Contract details (if accepted)
    - Follow-up schedule (if delayed)
    - Next steps recommendations (if rejected)
    
    **Use Cases:**
    - Monitor negotiation progress
    - Review negotiation strategy
    - Understand supplier's position
    - Get tactical recommendations
    - Track multi-round negotiations
    """
    logger.debug(f"Retrieving negotiation workflow: {thread_id}")
    
    negotiation_details = await service.get_negotiation_workflow_details(thread_id)
    
    if not negotiation_details:
        return not_found_response(
            resource="negotiation workflow",
            identifier=thread_id,
            request_id=request_id
        )
    
    return success_response(
        data=negotiation_details,
        request_id=request_id
    )


# ============================================
# UTILITY ENDPOINTS - SPECIFIC DATA ACCESS
# ============================================

@router.get(
    "/{thread_id}/status",
    response_model=APIResponse[dict],
    summary="Get quick conversation status",
    description="Get basic status information without full details"
)
async def get_conversation_status(
    thread_id: str,
    service: EnhancedConversationService = Depends(get_enhanced_service_dep),
    request_id: Optional[str] = Depends(get_request_id)
):
    """
    Get quick conversation status (lighter than comprehensive endpoint)
    
    Returns basic info: status, intent, is_paused, next_step
    """
    state = await service.graph_manager.get_state(thread_id)
    
    if not state:
        return not_found_response(
            resource="conversation",
            identifier=thread_id,
            request_id=request_id
        )
    
    is_paused = await service.graph_manager.is_workflow_paused(thread_id)
    
    return success_response(
        data={
            "thread_id": thread_id,
            "status": state.get("status", "unknown"),
            "intent": state.get("intent"),
            "next_step": state.get("next_step"),
            "is_paused": is_paused,
            "requires_human_review": state.get("requires_human_review", False)
        },
        request_id=request_id
    )


@router.get(
    "/{thread_id}/extracted-parameters",
    response_model=APIResponse[dict],
    summary="Get extracted parameters only",
    description="Get just the extracted parameters from the conversation"
)
async def get_extracted_parameters(
    thread_id: str,
    service: EnhancedConversationService = Depends(get_enhanced_service_dep),
    request_id: Optional[str] = Depends(get_request_id)
):
    """
    Get only extracted parameters
    
    Useful for quick parameter review without loading full state
    """
    state = await service.graph_manager.get_state(thread_id)
    
    if not state:
        return not_found_response(
            resource="conversation",
            identifier=thread_id,
            request_id=request_id
        )
    
    extracted_params = service._map_extracted_parameters(state.get('extracted_parameters'))
    
    return success_response(
        data=extracted_params,
        request_id=request_id
    )


@router.get(
    "/{thread_id}/suppliers",
    response_model=APIResponse[dict],
    summary="Get supplier search results only",
    description="Get just the supplier search results from the conversation"
)
async def get_suppliers(
    thread_id: str,
    service: EnhancedConversationService = Depends(get_enhanced_service_dep),
    request_id: Optional[str] = Depends(get_request_id)
):
    """
    Get only supplier search results
    
    Useful for supplier comparison without full conversation data
    """
    state = await service.graph_manager.get_state(thread_id)
    
    if not state:
        return not_found_response(
            resource="conversation",
            identifier=thread_id,
            request_id=request_id
        )
    
    supplier_search = service._map_supplier_search(
        state.get('supplier_search_result'),
        state.get('top_suppliers')
    )
    
    return success_response(
        data=supplier_search,
        request_id=request_id
    )

# need improvements here
@router.get(
    "/{thread_id}/messages",
    response_model=APIResponse[dict],
    summary="Get all messages from a conversation",
    description="Retrieve the complete message history for a conversation"
)
async def get_conversation_messages(
    thread_id: str,
    service: EnhancedConversationService = Depends(get_enhanced_service_dep),
    request_id: Optional[str] = Depends(get_request_id),
    user_id: Optional[str] = Depends(get_current_user)
):
    """
    Get all messages from a conversation
    
    **Path Parameters:**
    - thread_id: Conversation identifier
    
    **Returns:**
    - List of messages with role, content, and timestamps
    
    **Use Cases:**
    - Load chat history when user opens conversation
    - Display previous messages before streaming new ones
    - Reconstruct conversation timeline
    """
    logger.debug(f"Retrieving messages for conversation: {thread_id}")
    
    state = await service.graph_manager.get_state(thread_id)
    
    if not state:
        return not_found_response(
            resource="conversation",
            identifier=thread_id,
            request_id=request_id
        )
    
    # Extract messages from state
    messages = state.get("messages", [])
    
    # Format messages
    formatted_messages = []
    for msg in messages if isinstance(messages, list) else []:
        if isinstance(msg, dict):
            formatted_messages.append({
                "role": msg.get("role", "assistant"),
                "content": msg.get("content", ""),
                "timestamp": msg.get("timestamp"),
                "node": msg.get("node")
            })
        elif isinstance(msg, str):
            formatted_messages.append({
                "role": "assistant",
                "content": msg,
                "timestamp": None,
                "node": None
            })
    
    return success_response(
        data={
            "thread_id": thread_id,
            "messages": formatted_messages,
            "total_count": len(formatted_messages)
        },
        request_id=request_id
    )


# ============================================
# SSE STREAMING ENDPOINTS
# ============================================

@router.post(
    "/stream",
    summary="Start conversation with real-time streaming",
    description="Initialize a new conversation and stream all events in real-time",
    tags=["streaming"]
)
async def start_conversation_stream(
    request: StartConversationRequest,
    service: EnhancedConversationService = Depends(get_enhanced_service_dep),
    user_id: Optional[str] = Depends(get_current_user)
):
    """Start a new conversation with real-time SSE streaming"""
    logger.info(f"Starting streaming conversation for user: {user_id}")
    
    # Generate thread ID
    thread_id = service.generate_thread_id(user_id)
    
    # Prepare initial state
    initial_state = {
        "thread_id": thread_id,
        "user_input": request.user_input,
        "status": "starting",
        "channel": request.channel,
    }

    logger.info(f"Initial state for streaming start: {initial_state}")
    
    if request.recipient_email:
        initial_state["recipient_email"] = request.recipient_email
    
    # 🔥 Return StreamingResponse with aggressive anti-buffering headers
    return StreamingResponse(
        stream_workflow_events(
            service=service,
            thread_id=thread_id,
            initial_state=initial_state,
            workflow_type="start"
        ),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-store, no-transform, must-revalidate",
            "Connection": "keep-alive",
            "Content-Encoding": "none",
            "X-Accel-Buffering": "no",
            "Transfer-Encoding": "chunked",
            "Content-Type": "text/event-stream; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


@router.post(
    "/{thread_id}/stream/resume",
    summary="Resume conversation with streaming",
    description="Resume a paused conversation with supplier response and stream updates",
    tags=["streaming"]
)
async def resume_conversation_stream(
    thread_id: str,
    request: ResumeConversationRequest,
    service: EnhancedConversationService = Depends(get_enhanced_service_dep),
    user_id: Optional[str] = Depends(get_current_user)
):
    """Resume a paused conversation with real-time streaming"""
    logger.info(f"Resuming streaming conversation: {thread_id}")
    
    # Check if thread exists
    if not await service.conversation_exists(thread_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation not found: {thread_id}"
        )
    
    # Check if paused
    if not await service.graph_manager.is_workflow_paused(thread_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Conversation is not paused: {thread_id}"
        )
    
    async def event_generator():
        """Async generator that yields SSE events"""
        try:
            async for event_data in stream_workflow_events(
                service=service,
                thread_id=thread_id,
                initial_state={"supplier_response": request.supplier_response},
                workflow_type="resume"
            ):
                yield event_data
                await asyncio.sleep(0.001)
        except Exception as e:
            logger.error(f"Error in event generator: {e}")
            yield format_sse_event("error", {
                "thread_id": thread_id,
                "error": str(e)
            }).encode('utf-8')
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-store, no-transform, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Transfer-Encoding": "chunked",
            "Content-Encoding": "none",
            "Content-Type": "text/event-stream; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


@router.post(
    "/{thread_id}/stream/continue",
    summary="Continue conversation with streaming",
    description="Continue an existing conversation with new input and stream updates",
    tags=["streaming"]
)
async def continue_conversation_stream(
    thread_id: str,
    request: ContinueConversationRequest,
    service: EnhancedConversationService = Depends(get_enhanced_service_dep),
    user_id: Optional[str] = Depends(get_current_user)
):
    """Continue a conversation with real-time streaming"""
    logger.info(f"Continuing streaming conversation: {thread_id}")
    
    # Check if thread exists
    if not await service.conversation_exists(thread_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation not found: {thread_id}"
        )
    
    async def event_generator():
        """Async generator that yields SSE events"""
        try:
            async for event_data in stream_workflow_events(
                service=service,
                thread_id=thread_id,
                initial_state={"user_input": request.user_input},
                workflow_type="continue"
            ):
                yield event_data
                await asyncio.sleep(0.001)
        except Exception as e:
            logger.error(f"Error in event generator: {e}")
            yield format_sse_event("error", {
                "thread_id": thread_id,
                "error": str(e)
            }).encode('utf-8')
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, no-transform, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Encoding": "none",
            "Transfer-Encoding": "chunked",
            "Content-Type": "text/event-stream; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


@router.post(
    "/{thread_id}/select-supplier",
    response_model=APIResponse[dict],
    summary="Select a supplier for negotiation",
    description="User selects a supplier from the top suppliers list to proceed with negotiation"
)
async def select_supplier(
    thread_id: str,
    supplier_data: dict,
    service: EnhancedConversationService = Depends(get_enhanced_service_dep),
    request_id: Optional[str] = Depends(get_request_id)
):
    """
    Select a supplier from the top suppliers list
    
    **Path Parameters:**
    - thread_id: Conversation identifier
    
    **Request Body:**
    - supplier_data: The selected supplier object (must include name, email, location, etc.)
    
    **Returns:**
    - Updated conversation state with selected_supplier set
    
    **Use Cases:**
    - User clicks on a supplier from the list to start negotiation
    - Selected supplier is saved to state for message drafting
    """
    try:
        state = await service.graph_manager.get_state(thread_id)
        
        if not state:
            return not_found_response(
                resource="conversation",
                identifier=thread_id,
                request_id=request_id
            )
        
        # Update state with selected supplier
        state['selected_supplier'] = supplier_data
        state['active_supplier_id'] = supplier_data.get('supplier_id', supplier_data.get('id', ''))
        
        await service.graph_manager.update_state(thread_id, state)
        
        return success_response(
            data={
                "message": f"Supplier {supplier_data.get('name', 'Unknown')} selected",
                "selected_supplier": supplier_data,
                "thread_id": thread_id
            },
            request_id=request_id
        )
    except Exception as e:
        logger.error(f"Error selecting supplier: {str(e)}")
        return error_response(
            message=f"Error selecting supplier: {str(e)}",
            request_id=request_id
        )


@router.get(
    "/stream/test",
    summary="Test SSE streaming",
    description="Simple test endpoint to verify SSE streaming works",
    tags=["streaming"]
)

async def test_stream():
    """Test SSE streaming with simple counter"""
    
    async def generate():
        for i in range(10):
            event_data = f"event: test\ndata: {json.dumps({'count': i, 'message': f'Event {i}'})}\n\n"
            logger.info(f"[TEST-SSE] Sending event {i}")
            yield event_data.encode('utf-8')
            await asyncio.sleep(0.5)  # Wait 500ms between events
        
        # Send completion
        event_data = f"event: complete\ndata: {json.dumps({'message': 'Test complete'})}\n\n"
        yield event_data.encode('utf-8')
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, no-transform, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Encoding": "none",
            "Transfer-Encoding": "chunked",
            "Content-Type": "text/event-stream; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )