from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Pydantic Models for structured output
class NegotiationStrategy(BaseModel):
    """Strategic framework for the negotiation approach"""
    primary_approach: str = Field(
        ..., 
        description="Main negotiation strategy (volume-based, market-rate, partnership, urgency, reciprocity)"
    )
    supporting_arguments: List[str] = Field(
        ..., 
        description="List of 2-3 key supporting arguments to justify the request"
    )
    tone_assessment: str = Field(
        ..., 
        description="Recommended tone (collaborative, assertive, relationship-focused, data-driven)"
    )
    cultural_considerations: Optional[str] = Field(
        None, 
        description="Cultural adjustments needed for this supplier's region"
    )
    risk_factors: List[str] = Field(
        default_factory=list, 
        description="Potential risks or sensitivities to avoid in messaging"
    )

class DraftedMessage(BaseModel):
    """Complete negotiation message with metadata"""
    message_id: str = Field(..., description="Unique identifier for this message")
    recipient: str = Field(..., description="Supplier contact information or identifier")
    subject_line: Optional[str] = Field(None, description="Email subject line if applicable")
    message_body: str = Field(..., description="Complete message text ready for transmission")
    message_type: str = Field(..., description="Type of negotiation message (counter_offer, terms_adjustment, clarification)")
    priority_level: str = Field(..., description="Message priority (high, medium, low)")
    expected_response_time: Optional[str] = Field(None, description="Expected supplier response timeframe")
    fallback_options: List[str] = Field(
        default_factory=list, 
        description="Alternative approaches if this message doesn't get desired response"
    )
    confidence_score: float = Field(
        ..., 
        description="Confidence in message effectiveness (0.0 to 1.0)", 
        ge=0.0, 
        le=1.0
    )