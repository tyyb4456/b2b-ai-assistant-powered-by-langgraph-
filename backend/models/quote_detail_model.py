from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Pydantic Models for structured output
class LogisticsCost(BaseModel):
    """Logistics cost breakdown for a supplier"""
    shipping_cost: float = Field(..., description="Shipping cost in USD")
    insurance_cost: float = Field(..., description="Insurance cost in USD")
    customs_duties: float = Field(..., description="Estimated customs duties in USD")
    handling_fees: float = Field(..., description="Port/handling fees in USD")
    total_logistics: float = Field(..., description="Total logistics cost in USD")

class SupplierQuoteOption(BaseModel):
    """Individual supplier option in the quote"""
    supplier_name: str = Field(..., description="Name of the supplier company")
    supplier_location: str = Field(..., description="Supplier's country/region")
    unit_price: float = Field(..., description="Price per unit in USD")
    material_cost: float = Field(..., description="Total material cost (unit_price * quantity)")
    logistics_cost: LogisticsCost = Field(..., description="Breakdown of logistics costs")
    total_landed_cost: float = Field(..., description="Final total cost including all expenses")
    lead_time_days: int = Field(..., description="Delivery timeline in days")
    reliability_score: float = Field(..., description="Supplier reliability score (0-10)")
    overall_score: float = Field(..., description="Weighted overall score (0-100)")
    key_advantages: List[str] = Field(..., description="Key selling points for this supplier")
    potential_risks: List[str] = Field(..., description="Potential concerns or risks")

class QuoteAnalysis(BaseModel):
    """Strategic analysis and recommendations"""
    market_assessment: str = Field(..., description="Overall market conditions and pricing trends")
    recommended_supplier: str = Field(..., description="Primary recommended supplier name")
    recommendation_reasoning: str = Field(..., description="Detailed reasoning for the recommendation")
    risk_factors: List[str] = Field(..., description="Key risks to be aware of")
    negotiation_opportunities: List[str] = Field(..., description="Suggested negotiation points")
    alternative_strategies: List[str] = Field(..., description="Alternative approaches if needed")

class GeneratedQuote(BaseModel):
    """Complete quote document structure"""
    quote_id: str = Field(..., description="Unique quote identifier")
    quote_date: datetime = Field(default_factory=datetime.now, description="Date quote was generated")
    validity_days: int = Field(default=30, description="Quote validity period in days")
    client_summary: str = Field(..., description="Summary of client's requirements")
    supplier_options: List[SupplierQuoteOption] = Field(..., description="List of supplier options (max 4)")
    strategic_analysis: QuoteAnalysis = Field(..., description="Market analysis and recommendations")
    terms_and_conditions: str = Field(..., description="Standard T&C text")
    total_options_count: int = Field(..., description="Number of supplier options provided")
    estimated_savings: Optional[float] = Field(None, description="Potential savings vs market average")
