from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class AmbiguityIssue(BaseModel):
    """Detected ambiguity in the message"""
    issue_type: str = Field(
        description="Type of ambiguity (specification, pricing, timeline, quality, quantity)"
    )
    location: str = Field(
        description="Where in the message this occurs (specific text snippet)"
    )
    severity: str = Field(
        description="Severity level: critical, high, medium, low"
    )
    suggestion: str = Field(
        description="Recommended clarification or additional detail to add"
    )
    auto_fixable: bool = Field(
        description="Whether this can be automatically fixed"
    )


class MissingInformation(BaseModel):
    """Critical information missing from the message"""
    missing_field: str = Field(
        description="What information is missing (e.g., 'price_currency', 'delivery_date')"
    )
    importance: str = Field(
        description="How critical this is: critical, high, medium, low"
    )
    context: str = Field(
        description="Why this information is needed"
    )
    available_in_state: bool = Field(
        description="Whether this info exists in the agent state"
    )
    suggested_value: Optional[str] = Field(
        None,
        description="Suggested value if available in state"
    )


class JargonTerm(BaseModel):
    """Industry jargon that might need explanation"""
    term: str = Field(description="The jargon term (e.g., 'GSM', 'MOQ')")
    explanation: str = Field(description="Plain language explanation")
    should_add_definition: bool = Field(
        description="Whether to add inline definition"
    )
    context_appropriateness: float = Field(
        description="How appropriate this term is for this supplier (0-1)",
        ge=0.0,
        le=1.0
    )


class ContradictionIssue(BaseModel):
    """Contradictory information detected"""
    contradiction_type: str = Field(
        description="Type: price_inconsistency, timeline_conflict, quantity_mismatch, etc."
    )
    conflicting_statements: List[str] = Field(
        description="The conflicting statements identified"
    )
    severity: str = Field(description="critical, high, medium, low")
    resolution_suggestion: str = Field(
        description="How to resolve this contradiction"
    )


class ProactiveClarification(BaseModel):
    """Proactive clarification to add based on patterns"""
    topic: str = Field(description="Topic of clarification (e.g., 'payment_terms')")
    reason: str = Field(
        description="Why this clarification is recommended"
    )
    suggested_addition: str = Field(
        description="The text to add to the message"
    )
    placement: str = Field(
        description="Where to add this: 'after_pricing', 'after_timeline', 'end_of_message'"
    )
    priority: int = Field(
        description="Priority 1-5, where 1 is most important",
        ge=1,
        le=5
    )


class MessageValidationResult(BaseModel):
    """Comprehensive validation analysis of the drafted message"""
    
    # Overall Assessment
    clarity_score: float = Field(
        description="Overall message clarity (0-1)",
        ge=0.0,
        le=1.0
    )
    completeness_score: float = Field(
        description="Information completeness (0-1)",
        ge=0.0,
        le=1.0
    )
    professionalism_score: float = Field(
        description="Professional quality (0-1)",
        ge=0.0,
        le=1.0
    )
    overall_quality_score: float = Field(
        description="Weighted overall quality score (0-1)",
        ge=0.0,
        le=1.0
    )
    
    # Detected Issues
    ambiguities: List[AmbiguityIssue] = Field(
        default_factory=list,
        description="Ambiguous statements that need clarification"
    )
    missing_information: List[MissingInformation] = Field(
        default_factory=list,
        description="Critical information that's missing"
    )
    jargon_terms: List[JargonTerm] = Field(
        default_factory=list,
        description="Industry jargon that might need explanation"
    )
    contradictions: List[ContradictionIssue] = Field(
        default_factory=list,
        description="Contradictory information detected"
    )
    proactive_clarifications: List[ProactiveClarification] = Field(
        default_factory=list,
        description="Recommended proactive clarifications to add"
    )
    
    # Recommendations
    requires_human_review: bool = Field(
        description="Whether human review is needed (score < 0.5 or critical issues)"
    )
    auto_enhancement_possible: bool = Field(
        description="Whether message can be automatically enhanced"
    )
    recommended_action: str = Field(
        description="send_as_is, auto_enhance, human_review_required, major_revision_needed"
    )
    
    # Meta
    validation_confidence: float = Field(
        description="Confidence in this validation analysis (0-1)",
        ge=0.0,
        le=1.0
    )
    critical_issues_count: int = Field(
        description="Number of critical issues detected"
    )
    high_priority_fixes: List[str] = Field(
        default_factory=list,
        description="List of high-priority fixes to make"
    )


class EnhancedMessage(BaseModel):
    """The enhanced version of the message after validation"""
    
    original_message: str = Field(description="Original drafted message")
    enhanced_message: str = Field(description="Enhanced version with improvements")
    
    changes_made: List[Dict[str, str]] = Field(
        description="List of changes: {change_type, before, after, reason}"
    )
    
    added_clarifications: List[str] = Field(
        default_factory=list,
        description="Proactive clarifications that were added"
    )
    
    removed_ambiguities: List[str] = Field(
        default_factory=list,
        description="Ambiguities that were resolved"
    )
    
    improvement_summary: str = Field(
        description="Summary of improvements made"
    )
    
    quality_improvement: float = Field(
        description="How much quality improved (0-1 scale)",
        ge=0.0,
        le=1.0
    )
    
    final_quality_score: float = Field(
        description="Final quality score after enhancements",
        ge=0.0,
        le=1.0
    )
    
    ready_to_send: bool = Field(
        description="Whether message is now ready to send"
    )
    
    remaining_issues: List[str] = Field(
        default_factory=list,
        description="Issues that still need human attention"
    )