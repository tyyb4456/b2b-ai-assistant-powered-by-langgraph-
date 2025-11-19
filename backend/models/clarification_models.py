from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ===== CLARIFICATION CLASSIFICATION =====

class ClarificationQuestion(BaseModel):
    """Individual question extracted from supplier's message"""
    question_text: str = Field(description="The actual question asked")
    question_type: Literal[
        "technical_spec", "pricing", "quantity", "timeline", 
        "payment_terms", "logistics", "quality", "certification",
        "general_info", "confirmation"
    ] = Field(description="Category of the question")
    priority: Literal["critical", "high", "medium", "low"] = Field(
        description="How critical this question is for deal progress"
    )
    blocks_negotiation: bool = Field(
        description="Whether negotiation cannot proceed without this answer"
    )
    complexity: float = Field(
        description="Question complexity score 0-1",
        ge=0.0,
        le=1.0
    )
    requires_internal_consultation: bool = Field(
        description="Whether we need to consult with user/internal team"
    )


class ClarificationClassification(BaseModel):
    """Comprehensive classification of supplier's clarification request"""
    
    # Overall Assessment
    request_type: Literal[
        "technical_specifications",
        "commercial_terms", 
        "timeline_logistics",
        "quality_compliance",
        "mixed_multiple_topics",
        "confirmation_only"
    ] = Field(description="Primary type of clarification request")
    
    # Extracted Questions
    questions: List[ClarificationQuestion] = Field(
        description="All individual questions identified"
    )
    
    # Context Analysis
    supplier_confusion_level: Literal["low", "medium", "high", "severe"] = Field(
        description="How confused the supplier seems"
    )
    
    root_cause_analysis: str = Field(
        description="Why supplier is confused (our message unclear, missing info, etc.)"
    )
    
    previous_clarifications_count: int = Field(
        description="How many times this topic has been clarified before"
    )
    
    is_circular_confusion: bool = Field(
        description="Whether we're going in circles on this topic"
    )
    
    # Urgency Assessment
    urgency_level: Literal["immediate", "high", "medium", "low"] = Field(
        description="How urgently this needs response"
    )
    
    deal_impact: Literal["deal_breaker", "significant", "moderate", "minor"] = Field(
        description="Impact on deal if not resolved"
    )
    
    # Strategic Assessment
    supplier_engagement_signal: Literal[
        "highly_interested",
        "interested", 
        "neutral",
        "losing_interest",
        "frustrated"
    ] = Field(description="What this request signals about supplier's interest")
    
    recommended_response_approach: str = Field(
        description="Strategy for responding to this clarification"
    )
    
    escalation_recommended: bool = Field(
        description="Whether to escalate to human for review"
    )


# ===== HISTORICAL CONTEXT SEARCH =====

class HistoricalAnswer(BaseModel):
    """Previously provided answer found in history"""
    original_question: str = Field(description="Original question that was asked")
    answer_provided: str = Field(description="Answer we gave before")
    when_answered: str = Field(description="When this was answered")
    negotiation_round: int = Field(description="Which round this occurred in")
    was_sufficient: bool = Field(description="Whether answer seemed to satisfy at the time")
    relevance_score: float = Field(
        description="How relevant this is to current question (0-1)",
        ge=0.0,
        le=1.0
    )


class HistoricalContextResult(BaseModel):
    """Results from searching historical context"""
    
    found_previous_answers: bool = Field(
        description="Whether we found previous answers to similar questions"
    )
    
    previous_answers: List[HistoricalAnswer] = Field(
        default_factory=list,
        description="Previously provided answers"
    )
    
    information_evolved: bool = Field(
        description="Whether our terms/info have changed since previous answer"
    )
    
    evolution_details: Optional[str] = Field(
        None,
        description="What changed between then and now"
    )
    
    supplier_behavior_pattern: str = Field(
        description="Pattern in supplier's clarification requests"
    )
    
    recommendation: str = Field(
        description="How to handle based on history"
    )


# ===== INFORMATION AVAILABILITY CHECK =====

class AvailableInformation(BaseModel):
    """Information we have available to answer"""
    field_name: str = Field(description="Name of the field (e.g., 'price', 'lead_time')")
    value: str = Field(description="The actual value")
    source: str = Field(description="Where this info comes from (extracted_params, supplier_data, etc.)")
    confidence: float = Field(description="Confidence in this value 0-1", ge=0.0, le=1.0)
    needs_user_confirmation: bool = Field(description="Whether to confirm with user before sharing")


class MissingInformation(BaseModel):
    """Information we need but don't have"""
    field_name: str = Field(description="What information is missing")
    why_needed: str = Field(description="Why supplier needs this info")
    criticality: Literal["critical", "high", "medium", "low"] = Field(
        description="How critical this missing info is"
    )
    possible_workaround: Optional[str] = Field(
        None,
        description="Alternative approach if we can't provide exact answer"
    )
    ask_user: bool = Field(description="Whether to ask user for this information")


class InformationValidation(BaseModel):
    """Validation of what information we can provide"""
    
    can_answer_completely: bool = Field(
        description="Whether we have all info needed to fully answer"
    )
    
    completeness_score: float = Field(
        description="How complete our answer can be (0-1)",
        ge=0.0,
        le=1.0
    )
    
    available_information: List[AvailableInformation] = Field(
        description="Information we have available"
    )
    
    missing_information: List[MissingInformation] = Field(
        description="Information we're missing"
    )
    
    consistency_check_passed: bool = Field(
        description="Whether available info is internally consistent"
    )
    
    consistency_issues: List[str] = Field(
        default_factory=list,
        description="Any inconsistencies found"
    )
    
    recommended_action: Literal[
        "answer_fully",
        "answer_partially", 
        "request_user_input",
        "escalate_to_human"
    ] = Field(description="What to do based on available information")


# ===== CLARIFICATION RESPONSE GENERATION =====

class ResponseSection(BaseModel):
    """Individual section of the clarification response"""
    section_title: str = Field(description="Title of this section")
    section_type: Literal[
        "direct_answer",
        "detailed_explanation",
        "example",
        "table",
        "calculation_breakdown",
        "reference_to_previous"
    ] = Field(description="Type of section")
    content: str = Field(description="Actual content")
    confidence: float = Field(description="Confidence in this answer 0-1", ge=0.0, le=1.0)


class ProactiveAddition(BaseModel):
    """Proactive information to add"""
    topic: str = Field(description="Topic of proactive info")
    content: str = Field(description="The proactive information")
    reasoning: str = Field(description="Why we're adding this proactively")
    priority: int = Field(description="Priority 1-5", ge=1, le=5)


class ClarificationResponse(BaseModel):
    """Comprehensive clarification response"""
    
    # Response Structure
    greeting: str = Field(description="Personalized greeting acknowledging their questions")
    
    main_response_sections: List[ResponseSection] = Field(
        description="Main response sections answering each question"
    )
    
    proactive_additions: List[ProactiveAddition] = Field(
        default_factory=list,
        description="Additional information to prevent future confusion"
    )
    
    examples_provided: List[str] = Field(
        default_factory=list,
        description="Concrete examples included"
    )
    
    references_to_previous: List[str] = Field(
        default_factory=list,
        description="References to previous communications"
    )
    
    closing: str = Field(
        description="Professional closing with call to action"
    )
    
    # Quality Metrics
    clarity_score: float = Field(
        description="Expected clarity of this response 0-1",
        ge=0.0,
        le=1.0
    )
    
    completeness_score: float = Field(
        description="How completely this answers all questions 0-1",
        ge=0.0,
        le=1.0
    )
    
    reduces_confusion_likelihood: float = Field(
        description="Likelihood this prevents further confusion 0-1",
        ge=0.0,
        le=1.0
    )
    
    # Follow-up Management
    anticipates_followup_questions: List[str] = Field(
        default_factory=list,
        description="Questions supplier might ask next"
    )
    
    suggests_next_steps: str = Field(
        description="Clear next steps for supplier"
    )
    
    # Meta Information
    tone: str = Field(description="Tone used (professional, friendly, patient, etc.)")
    estimated_reading_time: str = Field(description="Estimated time to read response")
    confidence_in_resolution: float = Field(
        description="Confidence this will resolve confusion 0-1",
        ge=0.0,
        le=1.0
    )


# ===== CLARIFICATION QUALITY VALIDATION =====

class ClarificationQualityIssue(BaseModel):
    """Issue identified in clarification quality check"""
    issue_type: Literal[
        "ambiguity",
        "inconsistency", 
        "incomplete_answer",
        "too_technical",
        "missing_example",
        "unclear_next_steps",
        "contradicts_previous"
    ] = Field(description="Type of issue")
    
    severity: Literal["critical", "high", "medium", "low"] = Field(
        description="Severity of the issue"
    )
    
    location: str = Field(description="Where in the response this occurs")
    
    issue_description: str = Field(description="Description of the issue")
    
    suggested_fix: str = Field(description="How to fix this issue")
    
    auto_fixable: bool = Field(description="Whether this can be auto-fixed")


class ClarificationQualityValidation(BaseModel):
    """Quality validation of clarification response before sending"""
    
    # Overall Quality Scores
    overall_quality_score: float = Field(
        description="Overall quality 0-1",
        ge=0.0,
        le=1.0
    )
    
    clarity_score: float = Field(description="Clarity score 0-1", ge=0.0, le=1.0)
    completeness_score: float = Field(description="Completeness score 0-1", ge=0.0, le=1.0)
    consistency_score: float = Field(description="Consistency score 0-1", ge=0.0, le=1.0)
    helpfulness_score: float = Field(description="Helpfulness score 0-1", ge=0.0, le=1.0)
    
    # Issues Found
    issues: List[ClarificationQualityIssue] = Field(
        default_factory=list,
        description="Issues identified"
    )
    
    critical_issues_count: int = Field(description="Number of critical issues")
    
    # Validation Checks
    all_questions_answered: bool = Field(description="Whether all questions are answered")
    unanswered_questions: List[str] = Field(
        default_factory=list,
        description="Questions that weren't answered"
    )
    
    consistency_with_history: bool = Field(
        description="Whether response is consistent with previous communications"
    )
    
    inconsistencies_found: List[str] = Field(
        default_factory=list,
        description="Inconsistencies with previous messages"
    )
    
    appropriate_detail_level: bool = Field(
        description="Whether level of detail is appropriate"
    )
    
    includes_examples: bool = Field(description="Whether helpful examples are included")
    
    clear_next_steps: bool = Field(description="Whether next steps are clear")
    
    # Recommendations
    ready_to_send: bool = Field(description="Whether ready to send as-is")
    
    recommended_action: Literal[
        "send_as_is",
        "auto_enhance",
        "human_review_required",
        "major_revision_needed"
    ] = Field(description="Recommended action")
    
    enhancement_suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for enhancement"
    )
    
    # Confidence
    validation_confidence: float = Field(
        description="Confidence in this validation 0-1",
        ge=0.0,
        le=1.0
    )


# ===== ENHANCED CLARIFICATION RESPONSE =====

class EnhancedClarificationResponse(BaseModel):
    """Enhanced version of clarification after quality improvements"""
    
    original_response: str = Field(description="Original response text")
    enhanced_response: str = Field(description="Enhanced response text")
    
    improvements_made: List[Dict[str, str]] = Field(
        description="List of improvements: {improvement_type, description}"
    )
    
    added_elements: List[str] = Field(
        default_factory=list,
        description="Elements added (examples, tables, references, etc.)"
    )
    
    removed_ambiguities: List[str] = Field(
        default_factory=list,
        description="Ambiguities that were clarified"
    )
    
    quality_improvement: float = Field(
        description="How much quality improved 0-1",
        ge=0.0,
        le=1.0
    )
    
    final_quality_score: float = Field(
        description="Final quality score after enhancement 0-1",
        ge=0.0,
        le=1.0
    )
    
    ready_to_send: bool = Field(description="Whether ready to send now")
    
    remaining_concerns: List[str] = Field(
        default_factory=list,
        description="Concerns that still need attention"
    )


# ===== CLARIFICATION TRACKING =====

class ClarificationThread(BaseModel):
    """Track clarification conversation threads"""
    thread_id: str = Field(description="Unique thread identifier")
    topic: str = Field(description="Main topic of clarification")
    first_question_date: datetime = Field(description="When first asked")
    rounds: int = Field(description="Number of clarification rounds")
    status: Literal["open", "resolved", "escalated", "circular"] = Field(
        description="Current status"
    )
    resolution_quality: Optional[float] = Field(
        None,
        description="Quality of resolution if resolved 0-1"
    )