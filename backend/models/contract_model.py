from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ContractTerms(BaseModel):
    """Contract terms extracted from negotiation"""
    fabric_specifications: str = Field(
        ..., 
        description="Final fabric specifications (type, quality, GSM, etc.) as structured text"
    )
    quantity: int = Field(..., description="Final agreed quantity in meters/yards")
    unit_price: float = Field(..., description="Final unit price per meter/yard")
    total_value: float = Field(..., description="Total contract value")
    currency: str = Field(default="USD", description="Contract currency")
    
    delivery_terms: str = Field(
        ..., 
        description="Delivery timeline, shipping terms, incoterms as structured text"
    )
    payment_terms: str = Field(
        ..., 
        description="Payment schedule, methods, advance percentage as structured text"
    )
    quality_standards: str = Field(
        default="Standard quality control procedures", 
        description="Quality control, testing, certification requirements as structured text"
    )
    
    penalties_and_incentives: List[str] = Field(
        default_factory=list,
        description="List of penalty clauses for delays, quality issues, and incentives"
    )
    force_majeure: Optional[str] = Field(
        None,
        description="Force majeure clause details"
    )
    dispute_resolution: Optional[str] = Field(
        None,
        description="Dispute resolution mechanism"
    )

class ContractMetadata(BaseModel):
    """Contract metadata and tracking information"""
    contract_id: str = Field(..., description="Unique contract identifier")
    contract_type: str = Field(
        default="textile_procurement", 
        description="Type of contract"
    )
    contract_version: str = Field(default="1.0", description="Version number")
    
    buyer_company: str = Field(
        ..., 
        description="Buyer company details as structured text" 
    )
    supplier_company: str = Field(
        ..., 
        description="Supplier company details as structured text"
    )
    
    creation_date: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Contract creation timestamp in ISO format"
    )
    effective_date: Optional[str] = Field(
        None,
        description="Contract effective date in ISO format"
    )
    expiry_date: Optional[str] = Field(
        None,
        description="Contract expiry date in ISO format"
    )
    
    governing_law: str = Field(
        default="International Commercial Law",
        description="Governing law for the contract"
    )
    jurisdiction: Optional[str] = Field(
        None,
        description="Legal jurisdiction"
    )

class DraftedContract(BaseModel):
    """Complete drafted contract with all components"""
    contract_id: str = Field(..., description="Unique contract identifier")
    contract_title: str = Field(..., description="Contract title")
    
    # Core contract content
    preamble: str = Field(..., description="Contract introduction and parties")
    terms_and_conditions: str = Field(..., description="Main contract body")
    schedules_and_annexures: List[str] = Field(
        default_factory=list,
        description="Additional schedules, specifications, annexures as text"
    )
    signature_block: str = Field(..., description="Signature section")
    
    # Contract structure - using string representation instead of nested models
    contract_terms_summary: str = Field(..., description="Summary of structured contract terms")
    contract_metadata_summary: str = Field(..., description="Summary of contract metadata")
    
    # Review and approval
    review_status: str = Field(
        default="draft",
        description="Review status (draft, under_review, approved, executed)"
    )
    review_comments: List[str] = Field(
        default_factory=list,
        description="Review comments and feedback"
    )
    
    # Quality and compliance
    compliance_checklist: str = Field(
        default="Standard compliance requirements",
        description="Compliance requirements checklist as structured text"
    )
    legal_review_required: bool = Field(
        default=True,
        description="Whether legal review is required"
    )
    
    # Generation metadata
    confidence_score: float = Field(
        ..., 
        description="Confidence in contract completeness and accuracy (0.0 to 1.0)",
        ge=0.0, 
        le=1.0
    )
    generation_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Contract generation timestamp in ISO format"
    )
    
    # Next steps
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="Recommended next steps for contract execution"
    )

class ContractTemplate(BaseModel):
    """Template configuration for contract generation"""
    template_id: str = Field(..., description="Template identifier")
    template_name: str = Field(..., description="Template name")
    industry: str = Field(default="textile", description="Industry sector")
    contract_type: str = Field(..., description="Type of contract")
    
    # Template structure
    sections: List[str] = Field(..., description="Main contract sections")
    mandatory_clauses: List[str] = Field(..., description="Mandatory legal clauses")
    optional_clauses: List[str] = Field(..., description="Optional clauses")
    
    # Customization
    customizable_fields: str = Field(
        default="Standard customizable fields",
        description="Fields that can be customized as structured text"
    )
    default_terms: str = Field(
        default="Standard default terms",
        description="Default terms and values as structured text"
    )
    
    # Legal compliance
    jurisdiction_requirements: str = Field(
        default="Standard jurisdiction requirements",
        description="Jurisdiction-specific requirements as structured text"
    )
    compliance_standards: List[str] = Field(
        default_factory=list,
        description="Applicable compliance standards"
    )

class ContractReview(BaseModel):
    """Contract review and feedback structure"""
    review_id: str = Field(..., description="Review session identifier")
    reviewer_type: str = Field(..., description="Type of reviewer (legal, business, technical)")
    reviewer_info: str = Field(..., description="Reviewer information as structured text")
    
    review_date: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Review completion date in ISO format"
    )
    
    # Review results
    overall_status: str = Field(
        ...,
        description="Overall review status (approved, rejected, needs_revision)"
    )
    risk_assessment: str = Field(
        ...,
        description="Risk level (low, medium, high, critical)"
    )
    
    # Detailed feedback
    section_feedback: str = Field(
        default="No specific section feedback",
        description="Section-wise feedback with issues and suggestions as structured text"
    )
    missing_clauses: List[str] = Field(
        default_factory=list,
        description="Identified missing clauses"
    )
    problematic_terms: List[str] = Field(
        default_factory=list,
        description="Problematic terms with explanations"
    )
    
    # Recommendations
    priority_changes: List[str] = Field(
        default_factory=list,
        description="High priority changes required"
    )
    suggested_improvements: List[str] = Field(
        default_factory=list,
        description="Suggested improvements"
    )
    
    # Next steps
    next_review_required: bool = Field(
        default=False,
        description="Whether another review cycle is needed"
    )
    approval_authority: Optional[str] = Field(
        None,
        description="Required approval authority level"
    )


class RiskAssessment(BaseModel):
    """Comprehensive risk assessment for contract"""
    overall_risk_level: str = Field(description="low, medium, high, critical")
    risk_score: float = Field(description="0-100 risk score", ge=0, le=100)
    
    supplier_reliability_risk: float = Field(description="Risk from supplier reputation")
    negotiation_complexity_risk: float = Field(description="Risk from difficult negotiations")
    financial_risk: float = Field(description="Risk from contract value and payment terms")
    geographic_risk: float = Field(description="Risk from supplier location/jurisdiction")
    quality_risk: float = Field(description="Risk related to product specifications")
    
    risk_factors: List[str] = Field(description="Identified risk factors")
    mitigation_requirements: List[str] = Field(description="Required risk mitigation measures")
    recommended_clauses: List[str] = Field(description="Recommended protective clauses")


class ComplianceRequirements(BaseModel):
    """Compliance and certification requirements"""
    required_certifications: List[str] = Field(description="Certifications that must be maintained")
    industry_standards: List[str] = Field(description="Applicable industry standards")
    testing_requirements: List[str] = Field(description="Required testing protocols")
    inspection_level: str = Field(description="normal, enhanced, strict")
    third_party_inspection_required: bool = Field(description="Whether 3rd party inspection needed")
    
    geographic_compliance: Dict[str, Any] = Field(description="Location-specific requirements")
    documentation_requirements: List[str] = Field(description="Required documentation")


class FinancialTermsDetail(BaseModel):
    """Detailed financial terms structure"""
    payment_milestones: List[Dict[str, Any]] = Field(description="Milestone-based payment schedule")
    currency_terms: str = Field(description="Currency and exchange rate provisions")
    credit_period_days: int = Field(description="Credit period in days")
    late_payment_interest_rate: float = Field(description="Annual interest rate for late payments")
    bank_guarantee_required: bool = Field(description="Whether bank guarantee needed")
    bank_guarantee_amount_percentage: Optional[float] = Field(None, description="BG amount as % of contract")
    price_escalation_clause: Optional[str] = Field(None, description="Price adjustment provisions")
    retention_amount_percentage: Optional[float] = Field(None, description="Retention for quality assurance")


class DeliveryTermsDetail(BaseModel):
    """Detailed delivery and logistics terms"""
    order_date: str = Field(description="Contract/order date")
    production_start_date: str = Field(description="Expected production start")
    inspection_date: str = Field(description="Pre-shipment inspection date")
    shipment_date: str = Field(description="Expected shipment date")
    delivery_date: str = Field(description="Expected delivery date")
    
    incoterm: str = Field(description="Delivery Incoterm (FOB, CIF, etc.)")
    incoterm_responsibilities: str = Field(description="Detailed responsibilities breakdown")
    partial_shipment_allowed: bool = Field(description="Whether partial shipments permitted")
    partial_shipment_conditions: Optional[str] = Field(None, description="Conditions for partial shipments")
    
    shipping_method: str = Field(description="Sea freight, air freight, etc.")
    insurance_responsibility: str = Field(description="Who bears insurance cost and arranges it")
    required_shipping_documents: List[str] = Field(description="Required shipping documentation")


class QualityAssuranceFramework(BaseModel):
    """Comprehensive quality assurance requirements"""
    aql_level: str = Field(description="Acceptable Quality Limit level")
    sampling_procedure: str = Field(description="Sampling methodology")
    
    pre_production_sample_required: bool = Field(description="Whether PPS approval needed")
    in_line_inspection_required: bool = Field(description="During production inspection")
    pre_shipment_inspection_required: bool = Field(description="Final inspection before shipment")
    
    third_party_inspector: Optional[str] = Field(None, description="Designated inspection agency")
    inspection_standards: List[str] = Field(description="Standards to be followed")
    
    test_requirements: List[str] = Field(description="Specific tests to be conducted")
    defect_tolerance: Dict[str, float] = Field(description="Tolerance levels for different defect types")
    acceptance_criteria: str = Field(description="Clear acceptance/rejection criteria")
    remedy_for_rejection: str = Field(description="Remedy if goods rejected")
