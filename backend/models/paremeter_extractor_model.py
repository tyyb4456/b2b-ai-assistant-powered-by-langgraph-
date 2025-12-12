from typing import List, Dict, Any
from pydantic import BaseModel, Field

# Define Pydantic Models for Structured Output
class FabricDetails(BaseModel):
    """Structured fabric specifications extracted from user input"""
    type: str = Field(None, description="Type of fabric (cotton, silk, polyester, denim, etc.)")
    quantity: float = Field(None, description="Numeric quantity requested")
    unit: str = Field(None, description="Unit of measurement (meters, tons, rolls, yards)")
    quality_specs: List[str] = Field(default_factory=list, description="Quality specifications (GSM, organic, recycled, waterproof, etc.)")
    color: str = Field(None, description="Color or pattern requirement")
    width: float = Field(None, description="Fabric width in inches or cm", gt=0)
    composition: str = Field(None, description="Fabric composition (e.g., '100% cotton', '80/20 cotton/polyester')")
    finish: str = Field(None, description="Special fabric finish (e.g., 'pre-shrunk', 'mercerized', 'enzyme washed')")
    certifications: List[str] = Field(default_factory=list, description="Required certifications (GOTS, OEKO-TEX, etc.)")

class LogisticsDetails(BaseModel):
    """Delivery and logistics requirements"""
    destination: str = Field(None, description="Delivery destination")
    timeline: str = Field(None, description="Delivery timeline or urgency")
    timeline_days: int = Field(None, description="Specific number of days if mentioned")

class PriceConstraints(BaseModel):
    """Budget and pricing constraints"""
    max_price: float = Field(None, description="Maximum price per unit")
    currency: str = Field(None, description="Currency (USD, EUR, etc.)")
    price_unit: str = Field(None, description="Price unit (per meter, per kg, etc.)")

class ExtractedRequest(BaseModel):
    """Complete structured representation of user's trading request"""
    item_id: str = Field(description="Unique identifier for this request")
    request_type: str = Field(description="Type of request (get_quote, find_supplier, negotiate, etc.)")
    confidence: float = Field(..., description="Overall confidence in the extraction (0.0 to 1.0)", ge=0.0, le=1.0)
    fabric_details: FabricDetails
    logistics_details: LogisticsDetails
    price_constraints: PriceConstraints
    urgency_level: str = Field("medium", description="Urgency level: low, medium, high, urgent")
    supplier_preference: str = Field(None, description="Preferred supplier region or specific supplier name")
    moq_flexibility: bool = Field(None, description="Whether user is flexible with minimum order quantities")
    payment_terms: str = Field(None, description="Preferred payment terms (e.g., 'Net 30', 'Letter of Credit')")
    additional_notes: str = Field(None, description="Any additional requirements or notes")
    needs_clarification: bool = Field(False, description="Whether the request needs follow-up questions")
    clarification_questions: List[str] = Field(default_factory=list, description="Specific questions to ask for clarification")
    
    detailed_extraction: str = Field(
        ..., 
        description=(
            "A friendly, conversational message directly to the user summarizing what was understood. Format:\n\n"
            "**Structure:**\n"
            "1. Start with: 'Perfect! Here's what I've gathered from your request:'\n"
            "2. List the extracted details in natural language:\n"
            "   - Fabric type and specs (if available)\n"
            "   - Quantity and units (if available)\n"
            "   - Delivery timeline (if available)\n"
            "   - Budget constraints (if available)\n"
            "   - Special requirements (certifications, quality specs, etc.)\n"
            "**Tone:** Professional but friendly, clear and organized, action-oriented.\n"
            "**Avoid:** Technical jargon, saying 'you requested', robotic language.\n"
            "**Example:** 'Perfect! Here's what I've gathered: You're looking for 10,000 meters of organic cotton fabric "
            "(GSM 180) with GOTS certification, delivery to Pakistan within 45 days, and a budget of $4-5 per meter. "
        )
    )
    
    missing_info: List[str] = Field(
        default_factory=list, 
        description="List of important parameters that couldn't be extracted (technical list for internal use)"
    )
