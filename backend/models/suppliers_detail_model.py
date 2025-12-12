from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ContactInfo(BaseModel):
    """Contact information structure"""
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    contact_person: Optional[str] = None


class CertificationDetail(BaseModel):
    """Detailed certification information"""
    certification_name: str
    issued_by: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    is_verified: bool = False


class FabricTypeDetail(BaseModel):
    """Detailed fabric type information"""
    fabric_name: str
    fabric_category: Optional[str] = None
    gsm: Optional[int] = None
    composition: Optional[str] = None
    width_cm: Optional[float] = None
    price_per_unit: Optional[float] = None
    min_order_qty: Optional[float] = None
    lead_time_days: Optional[int] = None


class SupplierPerformanceMetrics(BaseModel):
    """Performance metrics for a supplier"""
    year: Optional[int] = None
    quarter: Optional[int] = None
    avg_lead_time: Optional[float] = None
    reliability_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    avg_price: Optional[float] = None
    on_time_delivery_rate: Optional[float] = Field(None, ge=0.0, le=100.0)
    defect_rate: Optional[float] = Field(None, ge=0.0, le=100.0)
    total_orders: Optional[int] = 0
    successful_orders: Optional[int] = 0
    communication_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    quality_score: Optional[float] = Field(None, ge=0.0, le=10.0)


class Supplier(BaseModel):
    """Individual supplier recommendation with scoring details"""
    
    # Core Identity
    supplier_id: str = Field(..., description="Unique supplier identifier")
    name: str = Field(..., description="Supplier company name")
    location: str = Field(..., description="Supplier location/country")
    
    # Contact Information (use individual fields instead of dict)
    email: Optional[str] = Field(None, description="Contact email address")
    phone: Optional[str] = Field(None, description="Contact phone number")
    website: Optional[str] = Field(None, description="Supplier website")
    contact_person: Optional[str] = Field(None, description="Primary contact person")
    
    # Pricing and Logistics
    price_per_unit: Optional[float] = Field(None, description="Price per unit (meter/kg/yard)")
    currency: str = Field(default="USD", description="Currency for pricing")
    lead_time_days: Optional[int] = Field(None, description="Production + shipping lead time in days")
    minimum_order_qty: Optional[float] = Field(None, description="Minimum order quantity")
    
    # Reputation and Status
    reputation_score: float = Field(default=5.0, description="Reliability score (0-10)", ge=0.0, le=10.0)
    active: bool = Field(default=True, description="Is the supplier currently active?")
    
    # Specializations
    specialties: List[str] = Field(default_factory=list, description="Supplier specializations")
    certifications: List[str] = Field(default_factory=list, description="Available certifications (names only)")
    
    # Additional Information
    source: Optional[str] = Field(None, description="Source of supplier data (internal, alibaba, etc.)")
    notes: Optional[str] = Field(None, description="Additional notes about this supplier")
    
    # Scoring (computed field)
    overall_score: float = Field(default=0.0, description="Weighted overall score", ge=0.0, le=100.0)
    
    # Detailed relationships (optional, populated when needed)
    performance_history: Optional[List[SupplierPerformanceMetrics]] = Field(None, description="Historical performance data")
    certification_details: Optional[List[CertificationDetail]] = Field(None, description="Detailed certification info")
    fabric_types: Optional[List[FabricTypeDetail]] = Field(None, description="Available fabric types")
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_contacted: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "supplier_id": "SUP001",
                "name": "Premium Textile Mills",
                "location": "Turkey",
                "email": "sales@premiumtextile.com",
                "price_per_unit": 4.50,
                "currency": "USD",
                "lead_time_days": 20,
                "minimum_order_qty": 5000,
                "reputation_score": 8.5,
                "specialties": ["organic cotton", "sustainable fabrics"],
                "certifications": ["GOTS", "OEKO-TEX"],
                "active": True,
                "overall_score": 85.5
            }
        }


class SupplierSearchResult(BaseModel):
    """Complete supplier sourcing results with analysis"""
    request_id: str = Field(..., description="Reference to the original request")
    total_suppliers_found: int = Field(..., description="Total number of suppliers found")
    filtered_suppliers: int = Field(..., description="Number after filtering")
    top_recommendations: List[Supplier] = Field(..., description="Top ranked suppliers (max 10)")
    
    search_strategy: str = Field(
        ..., 
        description="Brief user-friendly explanation of search and filtering approach"
    )
    
    market_insights: str = Field(
        ..., 
        description="Main assistant message summarizing results, market conditions, and next steps"
    )
    
    confidence: float = Field(..., description="Confidence in recommendations", ge=0.0, le=1.0)
    
    alternative_suggestions: Optional[List[str]] = Field(
        default_factory=list, 
        description="Alternative options if results are limited"
    )
    
    # Additional metadata
    search_timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    search_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "REQ123",
                "total_suppliers_found": 15,
                "filtered_suppliers": 8,
                "top_recommendations": [],
                "search_strategy": "Multi-source with high urgency weighting",
                "market_insights": "Strong supplier availability with competitive pricing",
                "confidence": 0.85,
                "alternative_suggestions": ["Consider polyester blends as alternative"]
            }
        }

class SupplierAnalysis(BaseModel):
    """AI analysis of suppliers with filtering and insights"""
    filtered_supplier_ids: List[str] = Field(
        description="List of supplier IDs that best match requirements after intelligent filtering"
    )
    top_supplier_ids: List[str] = Field(
        description="Top 5-10 supplier IDs ranked by overall fit"
    )
    
    market_insights: str = Field(
        description=(
            "A friendly, conversational message directly to the user summarizing supplier search results. Format:\n\n"
            "**Structure:**\n"
            "1. Start with results summary: 'Great news! I found [X] suppliers who match your requirements.'\n"
            "2. Provide market context:\n"
            "   - Pricing trends: 'Current market prices range from $X-Y per meter'\n"
            "   - Availability: 'Strong availability' / 'Limited options due to [reason]'\n"
            "   - Lead times: 'Typical delivery is X-Y days'\n"
            "3. Highlight top recommendations:\n"
            "   - 'The top matches include suppliers from [regions] with [key strengths]'\n"
            "   - Mention standout features: certifications, reliability scores, competitive pricing\n"
            "4. Note any trade-offs or considerations:\n"
            "   - 'If you're flexible on [parameter], you could get better [benefit]'\n"
            "5. End with next steps: 'I'll now prepare detailed quotes from these suppliers.'\n\n"
            "**Tone:** Informative, optimistic (when results are good), honest (if challenges exist), action-oriented.\n"
            "**Avoid:** Technical jargon, supplier IDs in the message, overly formal language.\n"
            "**Example:** 'Great news! I found 8 suppliers who can provide organic cotton fabric within your specs. "
            "Current market pricing is running $4.20-$5.50/meter for GOTS-certified material. The top matches include "
            "established suppliers from Turkey and India with 8.5+ reliability scores and 25-30 day lead times. "
            "I'll now prepare detailed quotes comparing pricing, delivery terms, and certifications.'"
        )
    )
    
    alternative_suggestions: List[str] = Field(
        description=(
            "List of alternative approaches if results are limited. Examples:\n"
            "- 'Consider polyester blends as a cost-effective alternative'\n"
            "- 'Increasing quantity to 15,000m could unlock better pricing'\n"
            "- 'Extending timeline by 2 weeks opens up 5 more high-quality suppliers'\n"
            "Keep suggestions actionable and business-focused."
        )
    )
    
    search_strategy: str = Field(
        description=(
            "A brief, user-friendly explanation of how suppliers were found and filtered. Format:\n"
            "'I searched for suppliers specializing in [fabric type] with [key requirements], "
            "then filtered based on [criteria] to ensure the best matches for your needs.'\n"
            "Keep it simple - 1-2 sentences max. This provides transparency without overwhelming detail."
        )
    )
    
    filtering_rationale: str = Field(
        description=(
            "Technical explanation of filtering logic (internal use only - not shown to user). "
            "Example: 'Filtered out 12 suppliers: 5 due to MOQ mismatch, 4 lacking required certifications, "
            "3 with reliability scores below 6.0'"
        )
    )



class SupplierCreateRequest(BaseModel):
    """Request model for creating a new supplier"""
    # Core fields
    supplier_id: str
    name: str
    location: str
    
    # Contact (removed duplicates from Supplier)
    contact_person: Optional[str] = None
    
    # Pricing & Logistics (removed duplicates)
    currency: str = "USD"
    
    # Reputation
    reputation_score: float = 5.0
    active: bool = True
    source: Optional[str] = "internal"
    
    # Lists as strings for easier API input
    specialties: Optional[str] = None  # comma-separated
    certifications: Optional[str] = None  # comma-separated
    notes: Optional[str] = None


class SupplierUpdateRequest(BaseModel):
    """Request model for updating supplier information"""
    # Only unique fields or ones that make sense to update
    name: Optional[str] = None
    location: Optional[str] = None
    reputation_score: Optional[float] = None
    active: Optional[bool] = None
    notes: Optional[str] = None