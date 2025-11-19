"""
Enhanced Pydantic schemas for comprehensive conversation API responses

These schemas expose all the rich data from AgentState to API consumers
"""
from typing import Optional, Literal, Any, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


# ============================================
# EXTRACTED PARAMETERS DETAILS
# ============================================

class FabricDetailsResponse(BaseModel):
    """Detailed fabric specifications from extraction"""
    type: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    quality_specs: List[str] = Field(default_factory=list)
    color: Optional[str] = None
    width: Optional[float] = None
    composition: Optional[str] = None
    finish: Optional[str] = None
    certifications: List[str] = Field(default_factory=list)


class ExtractedParametersResponse(BaseModel):
    """Complete extracted parameters from user input"""
    item_id: Optional[str] = None
    request_type: Optional[str] = None
    confidence: Optional[float] = None
    fabric_details: Optional[FabricDetailsResponse] = None
    urgency_level: Optional[str] = None
    supplier_preference: Optional[str] = None
    moq_flexibility: Optional[bool] = None
    payment_terms: Optional[str] = None
    additional_notes: Optional[str] = None
    needs_clarification: bool = False
    clarification_questions: List[str] = Field(default_factory=list)
    missing_info: List[str] = Field(default_factory=list)


# ============================================
# SUPPLIER SEARCH RESULTS
# ============================================

class SupplierDetailResponse(BaseModel):
    """Individual supplier details"""
    supplier_id: str
    name: str
    location: str
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    price_per_unit: Optional[float] = None
    currency: str = "USD"
    lead_time_days: Optional[int] = None
    minimum_order_qty: Optional[float] = None
    reputation_score: float = 5.0
    overall_score: float = 0.0
    specialties: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    active: bool = True
    source: Optional[str] = None
    notes: Optional[str] = None


class SupplierSearchResponse(BaseModel):
    """Complete supplier search results"""
    total_suppliers_found: int = 0
    filtered_suppliers: int = 0
    top_recommendations: List[SupplierDetailResponse] = Field(default_factory=list)
    search_strategy: Optional[str] = None
    market_insights: Optional[str] = None
    confidence: Optional[float] = None
    alternative_suggestions: List[str] = Field(default_factory=list)


# ============================================
# QUOTE GENERATION DETAILS
# ============================================

class LogisticsCostResponse(BaseModel):
    """Logistics cost breakdown"""
    shipping_cost: float = 0.0
    insurance_cost: float = 0.0
    customs_duties: float = 0.0
    handling_fees: float = 0.0
    total_logistics: float = 0.0


class SupplierQuoteOptionResponse(BaseModel):
    """Individual supplier option in quote"""
    supplier_name: str
    supplier_location: str
    unit_price: float
    material_cost: float
    logistics_cost: LogisticsCostResponse
    total_landed_cost: float
    lead_time_days: int
    reliability_score: float
    overall_score: float
    key_advantages: List[str] = Field(default_factory=list)
    potential_risks: List[str] = Field(default_factory=list)


class QuoteAnalysisResponse(BaseModel):
    """Strategic analysis from quote generation"""
    market_assessment: Optional[str] = None
    recommended_supplier: Optional[str] = None
    recommendation_reasoning: Optional[str] = None
    risk_factors: List[str] = Field(default_factory=list)
    negotiation_opportunities: List[str] = Field(default_factory=list)
    alternative_strategies: List[str] = Field(default_factory=list)


class GeneratedQuoteResponse(BaseModel):
    """Complete quote details"""
    quote_id: str
    quote_date: datetime
    validity_days: int = 30
    client_summary: Optional[str] = None
    supplier_options: List[SupplierQuoteOptionResponse] = Field(default_factory=list)
    strategic_analysis: Optional[QuoteAnalysisResponse] = None
    total_options_count: int = 0
    estimated_savings: Optional[float] = None


# ============================================
# NEGOTIATION DETAILS
# ============================================

class NegotiationStrategyResponse(BaseModel):
    """Negotiation strategy details"""
    primary_approach: Optional[str] = None
    supporting_arguments: List[str] = Field(default_factory=list)
    tone_assessment: Optional[str] = None
    cultural_considerations: Optional[str] = None
    risk_factors: List[str] = Field(default_factory=list)


class DraftedMessageResponse(BaseModel):
    """Drafted negotiation message"""
    message_id: Optional[str] = None
    recipient: Optional[str] = None
    subject_line: Optional[str] = None
    message_body: Optional[str] = None
    message_type: Optional[str] = None
    priority_level: Optional[str] = None
    expected_response_time: Optional[str] = None
    fallback_options: List[str] = Field(default_factory=list)
    confidence_score: Optional[float] = None


class MessageValidationResponse(BaseModel):
    """Message validation results"""
    clarity_score: Optional[float] = None
    completeness_score: Optional[float] = None
    professionalism_score: Optional[float] = None
    overall_quality_score: Optional[float] = None
    requires_human_review: bool = False
    auto_enhancement_possible: bool = False
    recommended_action: Optional[str] = None
    validation_confidence: Optional[float] = None
    critical_issues_count: int = 0
    high_priority_fixes: List[str] = Field(default_factory=list)


class NegotiationStateResponse(BaseModel):
    """Complete negotiation state"""
    negotiation_rounds: int = 0
    negotiation_status: Optional[str] = None
    negotiation_topic: Optional[str] = None
    conversation_tone: Optional[str] = None
    negotiation_objective: Optional[str] = None
    drafted_message: Optional[DraftedMessageResponse] = None
    negotiation_strategy: Optional[NegotiationStrategyResponse] = None
    message_validation: Optional[MessageValidationResponse] = None
    validated_message: Optional[str] = None
    validation_passed: bool = False
    last_message_confidence: Optional[float] = None
    active_supplier_email: Optional[str] = None
    email_sent: bool = False
    pdf_generated: bool = False


# ============================================
# SUPPLIER RESPONSE ANALYSIS
# ============================================

class SupplierIntentResponse(BaseModel):
    """Supplier's intent classification"""
    intent: Optional[str] = None
    confidence: Optional[float] = None
    sentiment: Optional[str] = None
    urgency_indicators: List[str] = Field(default_factory=list)
    relationship_signals: List[str] = Field(default_factory=list)


class ExtractedTermsResponse(BaseModel):
    """Terms extracted from supplier response"""
    new_price: Optional[float] = None
    price_currency: Optional[str] = None
    price_unit: Optional[str] = None
    new_lead_time: Optional[int] = None
    new_minimum_quantity: Optional[int] = None
    new_payment_terms: Optional[str] = None
    new_incoterms: Optional[str] = None
    new_quantity: Optional[int] = None
    quality_adjustments: Optional[str] = None
    additional_conditions: List[str] = Field(default_factory=list)
    concessions_offered: List[str] = Field(default_factory=list)


class NegotiationAnalysisResponse(BaseModel):
    """Analysis of supplier's response"""
    market_comparison: Optional[str] = None
    movement_analysis: Optional[str] = None
    strategic_assessment: Optional[str] = None
    negotiation_leverage: Optional[str] = None
    recommended_response: Optional[str] = None
    risk_factors: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    confidence_score: Optional[float] = None


class SupplierResponseAnalysisResponse(BaseModel):
    """Complete supplier response analysis"""
    supplier_response: Optional[str] = None
    supplier_intent: Optional[SupplierIntentResponse] = None
    extracted_terms: Optional[ExtractedTermsResponse] = None
    negotiation_analysis: Optional[NegotiationAnalysisResponse] = None
    negotiation_advice: Optional[str] = None
    analysis_confidence: Optional[float] = None
    supplier_offers: List[str] = Field(default_factory=list)
    is_follow_up_response: bool = False
    risk_alerts: List[str] = Field(default_factory=list)
    requires_attention: bool = False
    identified_opportunities: List[str] = Field(default_factory=list)


# ============================================
# CLARIFICATION HANDLING
# ============================================

class ClarificationQuestionResponse(BaseModel):
    """Individual clarification question"""
    question_text: str
    question_type: str
    priority: str
    blocks_negotiation: bool
    complexity: float
    requires_internal_consultation: bool


class ClarificationStateResponse(BaseModel):
    """Clarification handling state"""
    request_type: Optional[str] = None
    questions: List[ClarificationQuestionResponse] = Field(default_factory=list)
    supplier_confusion_level: Optional[str] = None
    root_cause_analysis: Optional[str] = None
    urgency_level: Optional[str] = None
    deal_impact: Optional[str] = None
    supplier_engagement_signal: Optional[str] = None
    recommended_response_approach: Optional[str] = None
    escalation_recommended: bool = False
    can_answer_completely: bool = False
    completeness_score: Optional[float] = None


# ============================================
# CONTRACT DETAILS
# ============================================

class ContractTermsResponse(BaseModel):
    """Contract terms summary"""
    fabric_specifications: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    total_value: Optional[float] = None
    currency: str = "USD"
    delivery_terms: Optional[str] = None
    payment_terms: Optional[str] = None
    quality_standards: Optional[str] = None
    penalties_and_incentives: List[str] = Field(default_factory=list)


class ContractMetadataResponse(BaseModel):
    """Contract metadata"""
    contract_id: Optional[str] = None
    contract_type: str = "textile_procurement"
    contract_version: str = "1.0"
    buyer_company: Optional[str] = None
    supplier_company: Optional[str] = None
    creation_date: Optional[str] = None
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    governing_law: str = "International Commercial Law"


class RiskAssessmentResponse(BaseModel):
    """Risk assessment for contract"""
    overall_risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    supplier_reliability_risk: Optional[float] = None
    negotiation_complexity_risk: Optional[float] = None
    financial_risk: Optional[float] = None
    geographic_risk: Optional[float] = None
    quality_risk: Optional[float] = None
    risk_factors: List[str] = Field(default_factory=list)
    mitigation_requirements: List[str] = Field(default_factory=list)
    recommended_clauses: List[str] = Field(default_factory=list)


class ContractStateResponse(BaseModel):
    """Complete contract state"""
    contract_id: Optional[str] = None
    contract_ready: bool = False
    contract_confidence: Optional[float] = None
    requires_legal_review: bool = True
    contract_terms: Optional[ContractTermsResponse] = None
    contract_metadata: Optional[ContractMetadataResponse] = None
    risk_assessment: Optional[RiskAssessmentResponse] = None
    contract_generation_timestamp: Optional[str] = None


# ============================================
# FOLLOW-UP SCHEDULING
# ============================================

class FollowUpAnalysisResponse(BaseModel):
    """Follow-up analysis details"""
    delay_reason: Optional[str] = None
    delay_type: Optional[str] = None
    estimated_delay_duration: Optional[str] = None
    supplier_commitment_level: Optional[str] = None
    urgency_of_our_timeline: Optional[str] = None
    competitive_risk: Optional[str] = None
    relationship_preservation_importance: Optional[str] = None
    market_dynamics_impact: Optional[str] = None


class FollowUpScheduleResponse(BaseModel):
    """Follow-up schedule details"""
    schedule_id: Optional[str] = None
    primary_follow_up_date: Optional[str] = None
    follow_up_method: Optional[str] = None
    follow_up_intervals: List[str] = Field(default_factory=list)
    escalation_timeline: Optional[str] = None
    initial_follow_up_tone: Optional[str] = None
    escalation_tone: Optional[str] = None
    confidence_in_schedule: Optional[float] = None


class FollowUpStateResponse(BaseModel):
    """Complete follow-up state"""
    follow_up_analysis: Optional[FollowUpAnalysisResponse] = None
    follow_up_schedule: Optional[FollowUpScheduleResponse] = None
    schedule_id: Optional[str] = None
    follow_up_dates: List[str] = Field(default_factory=list)
    next_follow_up_date: Optional[str] = None
    follow_up_ready: bool = False
    last_follow_up_confidence: Optional[float] = None


# ============================================
# FAILURE ANALYSIS & RECOMMENDATIONS
# ============================================

class FailureAnalysisResponse(BaseModel):
    """Analysis of negotiation failure"""
    failure_category: Optional[str] = None
    root_causes: List[str] = Field(default_factory=list)
    supplier_constraints: List[str] = Field(default_factory=list)
    market_factors: List[str] = Field(default_factory=list)
    severity: Optional[str] = None


class AlternativeSupplierResponse(BaseModel):
    """Alternative supplier recommendation"""
    supplier_name: str
    location: str
    estimated_price: Optional[float] = None
    lead_time_days: Optional[int] = None
    reliability_score: float
    why_better: str
    contact_priority: str


class NegotiationAdjustmentResponse(BaseModel):
    """Suggested negotiation adjustment"""
    parameter: str
    current_value: str
    suggested_value: str
    rationale: str
    success_probability: float


class NextStepsResponse(BaseModel):
    """Next steps recommendations"""
    failure_analysis: Optional[FailureAnalysisResponse] = None
    immediate_actions: List[str] = Field(default_factory=list)
    short_term_strategies: List[str] = Field(default_factory=list)
    long_term_approaches: List[str] = Field(default_factory=list)
    alternative_suppliers: List[AlternativeSupplierResponse] = Field(default_factory=list)
    negotiation_adjustments: List[NegotiationAdjustmentResponse] = Field(default_factory=list)
    budget_impact: Optional[str] = None
    confidence_score: Optional[float] = None
    priority_ranking: List[str] = Field(default_factory=list)


# ============================================
# COMPREHENSIVE CONVERSATION RESPONSE
# ============================================

class ConversationComprehensiveResponse(BaseModel):
    """COMPREHENSIVE conversation state with ALL details"""
    
    # Basic Info
    thread_id: str
    status: str
    intent: Optional[str] = None
    intent_confidence: Optional[float] = None
    next_step: Optional[str] = None
    is_paused: bool = False
    requires_human_review: bool = False
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Extracted Parameters
    extracted_parameters: Optional[ExtractedParametersResponse] = None
    
    # Supplier Search Results
    supplier_search: Optional[SupplierSearchResponse] = None
    
    # Quote Details (if quote workflow)
    quote: Optional[GeneratedQuoteResponse] = None
    
    # Negotiation Details (if negotiation workflow)
    negotiation: Optional[NegotiationStateResponse] = None
    
    # Supplier Response Analysis (if received response)
    supplier_response_analysis: Optional[SupplierResponseAnalysisResponse] = None
    
    # Clarification State (if clarification needed)
    clarification: Optional[ClarificationStateResponse] = None
    
    # Contract Details (if contract initiated)
    contract: Optional[ContractStateResponse] = None
    
    # Follow-up Details (if scheduled)
    follow_up: Optional[FollowUpStateResponse] = None
    
    # Next Steps Recommendations (if provided)
    next_steps_recommendations: Optional[NextStepsResponse] = None
    
    # Error Information
    error: Optional[str] = None
    error_type: Optional[str] = None


# ============================================
# WORKFLOW STAGE RESPONSES (for specific stages)
# ============================================

class QuoteWorkflowResponse(BaseModel):
    """Response for quote generation workflow"""
    thread_id: str
    status: str
    intent: str = "get_quote"
    extracted_parameters: Optional[ExtractedParametersResponse] = None
    supplier_search: Optional[SupplierSearchResponse] = None
    quote: Optional[GeneratedQuoteResponse] = None
    email_sent: bool = False
    pdf_generated: bool = False
    is_paused: bool = False
    created_at: datetime
    updated_at: datetime


class NegotiationWorkflowResponse(BaseModel):
    """Response for negotiation workflow"""
    thread_id: str
    status: str
    intent: str = "negotiate"
    negotiation: NegotiationStateResponse
    supplier_response_analysis: Optional[SupplierResponseAnalysisResponse] = None
    clarification: Optional[ClarificationStateResponse] = None
    contract: Optional[ContractStateResponse] = None
    follow_up: Optional[FollowUpStateResponse] = None
    next_steps_recommendations: Optional[NextStepsResponse] = None
    is_paused: bool = False
    created_at: datetime
    updated_at: datetime


"""
Pydantic schemas for conversation/workflow API endpoints
These define the API contracts (request/response models)
"""

# ============================================
# REQUEST MODELS (Input from client)
# ============================================

class StartConversationRequest(BaseModel):
    """Request to start a new conversation/workflow"""
    user_input: str = Field(
        ..., 
        min_length=1, 
        max_length=5000,
        description="User's message to start the conversation",
        examples=["I need a quote for 5,000 meters of organic cotton canvas"]
    )
    recipient_email: Optional[EmailStr] = Field(
        None,
        description="Email address to send quote/documents (optional)"
    )
    channel: str = Field(
        default="api",
        description="Communication channel (api, web, mobile)",
        examples=["api", "web"]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_input": "I need a quote for 5,000 meters of organic cotton canvas",
                "recipient_email": "buyer@company.com",
                "channel": "api"
            }
        }


class ResumeConversationRequest(BaseModel):
    """Request to resume a paused conversation (e.g., with supplier response)"""
    supplier_response: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Supplier's response message to continue negotiation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "supplier_response": "We can offer $4.20 per meter with 30-day lead time"
            }
        }


class ContinueConversationRequest(BaseModel):
    """Request to continue conversation with new user input"""
    user_input: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="New user message to continue the conversation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_input": "Can you improve the lead time to 20 days?"
            }
        }


# ============================================
# RESPONSE MODELS (Output to client)
# ============================================

class ConversationStatusResponse(BaseModel):
    """Current status of a conversation"""
    thread_id: str = Field(..., description="Unique conversation identifier")
    status: str = Field(..., description="Current workflow status")
    intent: Optional[str] = Field(None, description="Classified user intent")
    next_step: Optional[str] = Field(None, description="Next workflow step")
    is_paused: bool = Field(..., description="Whether workflow is waiting for input")
    created_at: datetime = Field(..., description="When conversation started")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "thread_id": "user123_abc-def-456",
                "status": "message_drafted",
                "intent": "negotiate",
                "next_step": "send_negotiation_message",
                "is_paused": False,
                "created_at": "2025-11-03T10:00:00Z",
                "updated_at": "2025-11-03T10:05:30Z"
            }
        }


class ConversationDetailResponse(BaseModel):
    """Detailed conversation state including extracted data"""
    thread_id: str
    status: str
    intent: Optional[str] = None
    intent_confidence: Optional[float] = None
    
    # Extracted parameters
    extracted_parameters: Optional[dict[str, Any]] = None
    
    # Quote information (if generated)
    quote_id: Optional[str] = None
    quote_summary: Optional[dict[str, Any]] = None
    
    # Negotiation information (if negotiating)
    negotiation_rounds: Optional[int] = None
    negotiation_status: Optional[str] = None
    drafted_message: Optional[str] = None
    
    # Workflow state
    next_step: Optional[str] = None
    is_paused: bool = False
    requires_human_review: bool = False
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "thread_id": "user123_abc-def",
                "status": "quote_generated",
                "intent": "get_quote",
                "intent_confidence": 0.95,
                "extracted_parameters": {
                    "fabric_type": "cotton canvas",
                    "quantity": 5000,
                    "unit": "meters"
                },
                "quote_id": "Q-20251103-001",
                "next_step": "send_quote_email",
                "is_paused": False,
                "created_at": "2025-11-03T10:00:00Z",
                "updated_at": "2025-11-03T10:05:30Z"
            }
        }


class ConversationListItem(BaseModel):
    """Summary of a conversation for list views"""
    thread_id: str
    status: str
    intent: Optional[str] = None
    preview: str = Field(..., description="First 100 chars of user input")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "thread_id": "user123_abc-def",
                "status": "completed",
                "intent": "get_quote",
                "preview": "I need a quote for 5,000 meters of organic cotton canvas",
                "created_at": "2025-11-03T10:00:00Z",
                "updated_at": "2025-11-03T10:05:30Z"
            }
        }


class WorkflowEventResponse(BaseModel):
    """Single workflow event/step completion"""
    event_name: str = Field(..., description="Name of the workflow step")
    status: Literal["started", "completed", "failed"] = Field(..., description="Event status")
    data: Optional[dict[str, Any]] = Field(None, description="Event-specific data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_name": "extract_parameters",
                "status": "completed",
                "data": {
                    "fabric_type": "cotton canvas",
                    "quantity": 5000
                },
                "timestamp": "2025-11-03T10:02:15Z"
            }
        }