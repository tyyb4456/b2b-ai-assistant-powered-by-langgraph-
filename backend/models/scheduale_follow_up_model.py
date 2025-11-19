from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Pydantic Models for Structured Output
class FollowUpAnalysis(BaseModel):
    """Analysis of supplier's delay request and follow-up requirements"""
    delay_reason: str = Field(description="Primary reason for supplier's delay (management_approval, production_planning, market_check, internal_consultation, seasonal_factors)")
    delay_type: str = Field(description="Type of delay (decision_time, information_gathering, approval_process, capacity_check)")
    estimated_delay_duration: str = Field(description="Estimated time supplier needs (hours, days, weeks)")
    supplier_commitment_level: str = Field(description="How committed supplier seems (high, medium, low, uncertain)")
    urgency_of_our_timeline: str = Field(description="How urgent our timeline is (flexible, moderate, tight, critical)")
    competitive_risk: str = Field(description="Risk of losing to competitors during delay (low, medium, high)")
    relationship_preservation_importance: str = Field(description="Importance of maintaining this supplier relationship (low, medium, high, critical)")
    market_dynamics_impact: str = Field(description="How market conditions affect the delay decision")

class FollowUpSchedule(BaseModel):
    """Structured follow-up schedule and timing strategy"""
    schedule_id: str = Field(description="Unique identifier for this follow-up schedule")
    primary_follow_up_date: str = Field(description="Main follow-up date (ISO format)")
    follow_up_method: str = Field(description="Method of follow-up (email, phone, video_call, whatsapp)")
    follow_up_intervals: List[str] = Field(description="Sequence of follow-up dates if needed")
    escalation_timeline: Optional[str] = Field(None, description="When to escalate if no response")
    
    # Message strategy
    initial_follow_up_tone: str = Field(description="Tone for first follow-up (understanding, gentle_reminder, professional_urgency)")
    escalation_tone: str = Field(description="Tone for later follow-ups if needed (firm, deadline_focused, alternative_seeking)")
    
    # Content strategy
    value_reinforcement_points: List[str] = Field(description="Key points to reinforce our value proposition")
    urgency_factors_to_mention: List[str] = Field(description="Urgency factors to communicate appropriately")
    relationship_building_elements: List[str] = Field(description="Elements to maintain/build relationship")
    
    # Contingency planning
    alternative_actions: List[str] = Field(description="Alternative actions if supplier remains unresponsive")
    deadline_for_decision: Optional[str] = Field(None, description="Final deadline for supplier decision")
    
    confidence_in_schedule: float = Field(description="Confidence in the follow-up schedule effectiveness (0.0 to 1.0)", ge=0.0, le=1.0)

class FollowUpMessage(BaseModel):
    """Follow-up message to send to supplier"""
    message_id: str = Field(description="Unique identifier for this follow-up message")
    message_type: str = Field(description="Type of follow-up message (gentle_reminder, status_check, deadline_notice, relationship_maintenance)")
    subject_line: str = Field(description="Email subject line or message topic")
    message_body: str = Field(description="Main follow-up message content", min_length=50, max_length=1500)
    
    # Strategic elements
    key_message_points: List[str] = Field(description="Main points covered in the message")
    call_to_action: str = Field(description="Specific action requested from supplier")
    deadline_mentioned: Optional[str] = Field(None, description="Any deadline mentioned in message")
    
    # Relationship management
    relationship_building_language: bool = Field(False, description="Whether message includes relationship-building language")
    cultural_adaptation_notes: Optional[str] = Field(None, description="Cultural considerations applied to message")
    
    # Follow-up logistics
    expected_response_time: str = Field(description="Expected response timeframe (24_hours, 2_3_days, week, longer)")
    next_follow_up_if_no_response: Optional[str] = Field(None, description="Next follow-up date if no response")
    
    message_priority: str = Field(description="Message priority level (low, medium, high)")
    confidence_score: float = Field(description="Confidence in message effectiveness (0.0 to 1.0)", ge=0.0, le=1.0)