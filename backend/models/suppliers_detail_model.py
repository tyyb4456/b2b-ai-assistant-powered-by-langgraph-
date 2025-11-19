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
    search_strategy: str = Field(..., description="Strategy used for this search")
    market_insights: str = Field(..., description="Brief market analysis and recommendations")
    confidence: float = Field(..., description="Confidence in recommendations", ge=0.0, le=1.0)
    alternative_suggestions: Optional[List[str]] = Field(default_factory=list, description="Alternative options if results are limited")
    
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
        description="Detailed market analysis including pricing trends, availability, and recommendations"
    )
    alternative_suggestions: List[str] = Field(
        description="Alternative fabric types or suppliers to consider"
    )
    search_strategy: str = Field(
        description="Description of the filtering strategy used"
    )
    filtering_rationale: str = Field(
        description="Explanation of why certain suppliers were filtered out"
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