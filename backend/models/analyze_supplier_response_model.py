from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field

# Pydantic Models for structured analysis   
class SupplierIntent(BaseModel):
    """Classification of supplier's response intent and sentiment"""
    intent: Literal["accept", "counteroffer", "reject", "clarification_request", "delay"] = Field(
        ..., 
        description="Primary intent of supplier's response"
    )
    confidence: float = Field(
        ..., 
        description="Confidence in intent classification (0.0 to 1.0)", 
        ge=0.0, 
        le=1.0
    )
    sentiment: Literal["positive", "neutral", "negative", "frustrated", "cooperative"] = Field(
        ..., 
        description="Overall sentiment and tone of the message"
    )
    urgency_indicators: List[str] = Field(
        default_factory=list, 
        description="Phrases indicating time pressure or urgency"
    )
    relationship_signals: List[str] = Field(
        default_factory=list, 
        description="Phrases indicating relationship status (positive/negative)"
    )

class ExtractedTerms(BaseModel):
    """New terms proposed by supplier in counteroffer"""
    new_price: Optional[float] = Field(None, description="New price per unit")
    price_currency: Optional[str] = Field(None, description="Currency for pricing")
    price_unit: Optional[str] = Field(None, description="Unit for pricing (per meter, per kg, etc.)")
    new_lead_time: Optional[int] = Field(None, description="New lead time in days")
    new_minimum_quantity: Optional[int] = Field(None, description="New minimum order quantity")
    new_payment_terms: Optional[str] = Field(None, description="Modified payment terms")
    new_incoterms: Optional[str] = Field(None, description="New shipping/delivery terms")
    new_quantity : Optional[int] = Field(None, description="New quantity offered")
    quality_adjustments: Optional[str] = Field(None, description="Any quality specification changes")
    additional_conditions: List[str] = Field(
        default_factory=list, 
        description="Any additional conditions or requirements"
    )
    concessions_offered: List[str] = Field(
        default_factory=list, 
        description="What the supplier is offering as value-adds"
    )

class NegotiationAnalysis(BaseModel):
    """Strategic analysis of supplier's response"""
    market_comparison: str = Field(
        ..., 
        description="How new terms compare to market benchmarks"
    )
    movement_analysis: str = Field(
        ..., 
        description="Analysis of supplier's movement from previous position"
    )
    strategic_assessment: str = Field(
        ..., 
        description="Overall strategic assessment of the offer"
    )
    negotiation_leverage: str = Field(
        ..., 
        description="Assessment of current negotiation leverage and position"
    )
    recommended_response: str = Field(
        ..., 
        description="Specific tactical recommendation for next response"
    )
    risk_factors: List[str] = Field(
        default_factory=list, 
        description="Potential risks or red flags identified"
    )
    opportunities: List[str] = Field(
        default_factory=list, 
        description="Opportunities or positive signals to leverage"
    )
    confidence_score: float = Field(
        ..., 
        description="Confidence in the analysis and recommendations, from 0.0 to 1.0",
    )