from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field

# Pydantic Models for Structured Output
class AlternativeSupplier(BaseModel):
    """Alternative supplier recommendation"""
    supplier_name: str = Field(..., description="Name of alternative supplier")
    location: str = Field(..., description="Supplier location/country")
    estimated_price: Optional[float] = Field(None, description="Estimated price per unit")
    lead_time_days: Optional[int] = Field(None, description="Estimated lead time in days")
    reliability_score: float = Field(..., description="Reliability score 1-10", ge=1, le=10)
    why_better: str = Field(..., description="Why this supplier might be better for this situation")
    contact_priority: Literal["high", "medium", "low"] = Field("medium", description="Priority for contacting this supplier")

class NegotiationAdjustment(BaseModel):
    """Specific adjustment recommendation for retry"""
    parameter: str = Field(..., description="What to adjust (price, quantity, timeline, terms)")
    current_value: str = Field(..., description="Current value that failed")
    suggested_value: str = Field(..., description="Suggested new value")
    rationale: str = Field(..., description="Why this adjustment might work")
    success_probability: float = Field(..., description="Estimated success probability 0-1", ge=0, le=1)

class MarketStrategy(BaseModel):
    """Market-based strategy recommendation"""
    strategy_name: str = Field(..., description="Name of the strategy")
    description: str = Field(..., description="Detailed description of the strategy")
    timeline: str = Field(..., description="Expected timeline for this strategy")
    requirements: List[str] = Field(default_factory=list, description="What's needed to execute this strategy")
    success_likelihood: Literal["high", "medium", "low"] = Field("medium", description="Likelihood of success")

class FailureAnalysis(BaseModel):
    """Analysis of why the negotiation failed"""
    failure_category: Literal[
        "price_mismatch", 
        "timeline_conflict", 
        "quality_standards", 
        "quantity_constraints",
        "supplier_capacity",
        "market_conditions",
        "relationship_issues",
        "unknown"
    ] = Field(..., description="Primary category of failure")
    root_causes: List[str] = Field(..., description="Identified root causes of failure")
    supplier_constraints: List[str] = Field(default_factory=list, description="Supplier-specific constraints that led to failure")
    market_factors: List[str] = Field(default_factory=list, description="Market factors that contributed to failure")
    severity: Literal["minor", "moderate", "severe"] = Field("moderate", description="Severity of the negotiation failure")

class NextStepsRecommendation(BaseModel):
    """Comprehensive next steps recommendation"""
    failure_analysis: FailureAnalysis
    immediate_actions: List[str] = Field(..., description="Actions to take immediately (within 24-48 hours)")
    short_term_strategies: List[str] = Field(..., description="Strategies for next 1-2 weeks")
    long_term_approaches: List[str] = Field(..., description="Long-term approaches for next 1-3 months")
    alternative_suppliers: List[AlternativeSupplier] = Field(default_factory=list, description="Recommended alternative suppliers")
    negotiation_adjustments: List[NegotiationAdjustment] = Field(default_factory=list, description="Adjustments to retry with same supplier")
    market_strategies: List[MarketStrategy] = Field(default_factory=list, description="Market-based strategies")
    budget_impact: Optional[str] = Field(None, description="Expected impact on budget/timeline")
    confidence_score: float = Field(..., description="Confidence in recommendations 0-1", ge=0, le=1)
    priority_ranking: List[str] = Field(..., description="Priority ranking of recommended approaches")