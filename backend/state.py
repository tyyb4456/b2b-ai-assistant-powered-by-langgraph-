from typing import TypedDict, Annotated, Optional, List, Dict, Any
from models.paremeter_extractor_model import ExtractedRequest
from langgraph.graph.message import add_messages
from models.suppliers_detail_model import SupplierSearchResult
from models.quote_detail_model import GeneratedQuote
from models.negotiation_message_detail import DraftedMessage, NegotiationStrategy
from models.message_validation_model import MessageValidationResult, EnhancedMessage
from models.analyze_supplier_response_model import SupplierIntent, ExtractedTerms, NegotiationAnalysis
from models.clarification_models import (
    ClarificationClassification, 
    HistoricalContextResult, 
    InformationValidation, 
    MissingInformation,
    ClarificationResponse
)
from models.contract_model import DraftedContract, ContractTerms, ContractMetadata, RiskAssessment, ComplianceRequirements, FinancialTermsDetail, DeliveryTermsDetail, QualityAssuranceFramework
from models.notify_and_sugest_model import FailureAnalysis, NextStepsRecommendation
from models.scheduale_follow_up_model import FollowUpAnalysis, FollowUpSchedule, FollowUpMessage

class AgentState(TypedDict):
    """
    State structure for the procurement agent workflow.
    This defines the shared data structure passed between all nodes.
    """
    # Core identification
    thread_id: str  # Thread ID for tracking workflow execution
    user_id: str
    session_id: str
    channel: str
    status : str
    recipient_email: str
    active_supplier_id: str  # Current supplier being negotiated with

    messages : Annotated[list, add_messages]

    user_input: str

    # Workflow control
    next_step: str

    # intent classification fields
    intent: str
    intent_confidence: Optional[float] = None
    intent_reasoning: Optional[str] = None



    # Parameter extraction results
    extracted_parameters: ExtractedRequest
    needs_clarification: bool = False
    clarification_questions: Optional[List[str]] = None
    missing_info: Optional[List[str]] = None

    # supplier sourcing fields
    supplier_search_result : SupplierSearchResult
    top_suppliers: Optional[List[Dict[str, Any]]]
    selected_supplier: Optional[Dict[str, Any]]  # User-selected supplier for negotiation

    # quote generation fields
    generated_quote : GeneratedQuote
    quote_document: Optional[str]
    quote_id: Optional[str]
    quote_summary: Optional[Dict[str, Any]]
    supplier_options: Optional[List[Dict[str, Any]]]
    estimated_savings: Optional[float]
    
    # Error handling
    error: Optional[str]
    error_type: Optional[str]
    
    # Timestamp
    timestamp: Optional[str]



    # negotiation starter fields
    negotiation_topic : str
    conversation_tone : str
    negotiation_objective : str


    # negotiation message drafting fields

    drafted_message_data : DraftedMessage
    negotiation_strategy : NegotiationStrategy
    negotiation_messages : Annotated[List[Dict[str, str]], add_messages]
    drafted_message : str
    active_supplier_email : str
    last_message_confidence : Optional[float]
    message_id : Optional[str]
    requires_review : bool
    fallback_options : List[str]

    # message validation fields
    message_validation : MessageValidationResult
    validated_message : str
    validation_passed : bool
    requires_human_review : bool
    validation_issues : Optional[Dict[str, Any]]
    message_enhancement : EnhancedMessage
    original_message : str
    validation_score : Optional[float]
    quality_improvement : Optional[float]
    validation_timestamp : Optional[str]
    enhancement_changes : Optional[List[Dict[str, str]]]
    proactive_clarifications_added : Optional[List[str]]
    remaining_validation_issues : Optional[List[str]]
    review_priority : Optional[str]
    had_critical_issues : bool
    critical_issues_count : int

    # negotiation message sender fields

    email_sent : bool
    quote_sender_agent_messages : List[str]
    pdf_generated : bool


    # supplier response
    negotiation_rounds : int
    supplier_response : str
    supplier_offers = List[str]


    drafted_message_sender_agent : List[str]

    # supplier response analysis fields
    negotiation_history : List[Dict[str, Any]]
    supplier_intent : SupplierIntent
    extracted_terms : ExtractedTerms
    negotiation_analysis : NegotiationAnalysis
    negotiation_advice : str
    negotiation_status : str
    analysis_confidence : Optional[float]
    supplier_offers : List[str]
    last_analysis_timestamp : Optional[str]
    is_follow_up_response : bool
    risk_alerts : List[str]
    requires_attention : bool
    identified_opportunities : List[str]

    # clarification handling fields

    clarification_classification : ClarificationClassification
    clarification_questions : Optional[List[str]]
    confusion_level : str
    is_circular_confusion : bool
    escalation_needed : bool

    # contract initiation fields
    drafted_contract : DraftedContract
    contract_terms : ContractTerms
    contract_metadata : ContractMetadata
    contract_ready : bool
    contract_id : Optional[str]
    contract_confidence : Optional[float]
    requires_legal_review : bool
    risk_assessment : RiskAssessment
    compliance_requirements : ComplianceRequirements 
    financial_terms_detail : FinancialTermsDetail
    delivery_terms_detail : DeliveryTermsDetail
    quality_framework : QualityAssuranceFramework 
    validation_results  : Optional[Dict[str, Any]]
    contract_generation_timestamp : Optional[str] 

    # notify user and suggest next steps fields
    failure_analysis : FailureAnalysis
    next_steps_recommendations : NextStepsRecommendation
    analysis_id : Optional[str]
    alternative_suppliers_list : Optional[List[Dict[str, Any]]]
    recommended_adjustments : List[Dict[str, Any]]
    user_notification : str
    follow_up_required : bool
    priority_level : Optional[str]
    recommendations_confidence : Optional[float]




    # historical clarification context fields

    historical_context : HistoricalContextResult
    found_previous_answers : bool
    information_evolved : bool

    information_validation : InformationValidation
    can_answer_completely : bool
    completeness_score : Optional[float]
    missing_critical_info : List[MissingInformation]
    recommended_action : str

    clarification_response : ClarificationResponse


    # schedual follow-up fields
    follow_up_analysis : FollowUpAnalysis
    follow_up_schedule : FollowUpSchedule
    follow_up_message : FollowUpMessage
    schedule_id : Optional[str]
    message_id : Optional[str]
    follow_up_dates : Optional[List[str]]
    next_follow_up_date : Optional[str]
    follow_up_ready : bool
    last_follow_up_confidence : Optional[float]