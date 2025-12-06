from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState
from models.contract_model import DraftedContract, ContractTerms, ContractMetadata, ComplianceRequirements, RiskAssessment, FinancialTermsDetail, DeliveryTermsDetail, QualityAssuranceFramework
from dotenv import load_dotenv
import uuid
from datetime import datetime, timedelta
import json
from loguru import logger
load_dotenv()



def extract_comprehensive_context(state: AgentState) -> Dict[str, Any]:
    """
    Extract comprehensive context from negotiation with proper model parsing
    """
    
    # Extract supplier data
    supplier_data = state.get('top_suppliers', [])

    # Check if user has selected a supplier, otherwise fall back to first supplier
    selected_supplier = state.get('selected_supplier', None)

    
    if selected_supplier:
        # Use the user-selected supplier
        active_supplier = selected_supplier
        logger.info("Using user-selected supplier for profile.")
    elif supplier_data and len(supplier_data) > 0:
        # Fall back to first supplier if no selection made
        active_supplier = supplier_data[0]
        logger.info("No user-selected supplier, using first supplier from search results.")
    else:
        active_supplier = None
    
    # Extract negotiation history
    negotiation_history = state.get('negotiation_history', [])
    negotiation_messages = state.get('negotiation_messages', [])
    
    # Analyze negotiation journey
    negotiation_analysis = analyze_negotiation_journey(
        negotiation_history, 
        negotiation_messages,
        state
    )
    
    # Extract original request parameters (properly handle ExtractedRequest model)
    extracted_params = state.get('extracted_parameters', {})
    if isinstance(extracted_params, dict):
        fabric_details = extracted_params.get('fabric_details', {})
        logistics_details = extracted_params.get('logistics_details', {})
        price_constraints = extracted_params.get('price_constraints', {})
    else:
        # If it's a Pydantic model, access attributes
        fabric_details = extracted_params.fabric_details.model_dump() if hasattr(extracted_params, 'fabric_details') else {}
        logistics_details = extracted_params.logistics_details.model_dump() if hasattr(extracted_params, 'logistics_details') else {}
        price_constraints = extracted_params.price_constraints.model_dump() if hasattr(extracted_params, 'price_constraints') else {}
    
    # Extract generated quote data (properly handle GeneratedQuote model)
    generated_quote = state.get('generated_quote')
    if generated_quote:
        if isinstance(generated_quote, dict):
            quote_data = generated_quote
        else:
            # It's a Pydantic model
            quote_data = generated_quote.model_dump() if hasattr(generated_quote, 'model_dump') else {}
    else:
        quote_data = {}
    
    # Extract final negotiated terms
    extracted_terms = state.get('extracted_terms', {})
    if not isinstance(extracted_terms, dict):
        extracted_terms = extracted_terms.model_dump() if hasattr(extracted_terms, 'model_dump') else {}
    
    # Determine final pricing
    negotiated_price = extracted_terms.get('new_price')
    quote_price = quote_data.get('unit_price') or quote_data.get('price_per_unit')
    supplier_quoted_price = active_supplier.get('price_per_unit')
    
    final_unit_price = negotiated_price or quote_price or supplier_quoted_price or 10.0
    
    # Determine final quantity
    negotiated_quantity = extracted_terms.get('new_quantity')
    original_quantity = fabric_details.get('quantity')
    final_quantity = negotiated_quantity or original_quantity or 5000
    
    # Calculate total value
    total_contract_value = final_quantity * final_unit_price
    
    # Determine final lead time
    negotiated_lead_time = extracted_terms.get('new_lead_time')
    supplier_lead_time = active_supplier.get('lead_time_days')
    original_timeline_days = logistics_details.get('timeline_days')
    final_lead_time = negotiated_lead_time or supplier_lead_time or original_timeline_days or 45
    
    # Buyer company information (try to extract from state or use defaults)
    buyer_email = state.get('recipient_email', 'buyer@company.com')
    buyer_company_name = state.get('buyer_company_name', 'Your Company Name')
    
    # Build comprehensive context
    context = {
        'fabric_specifications': {
            'fabric_type': fabric_details.get('type', 'Textile material'),
            'quantity': final_quantity,
            'unit': fabric_details.get('unit', 'meters'),
            'quality_specs': fabric_details.get('quality_specs', []),
            'certifications': fabric_details.get('certifications', []),
            'composition': fabric_details.get('composition'),
            'color': fabric_details.get('color'),
            'width': fabric_details.get('width'),
            'finish': fabric_details.get('finish'),
            'gsm': extract_gsm_from_specs(fabric_details.get('quality_specs', []))
        },
        
        'pricing_terms': {
            'unit_price': final_unit_price,
            'currency': price_constraints.get('currency', 'USD'),
            'total_value': total_contract_value,
            'original_target_price': price_constraints.get('max_price'),
            'negotiated_from': supplier_quoted_price,
            'negotiated_to': final_unit_price,
            'savings_achieved': calculate_savings_percentage(supplier_quoted_price, final_unit_price)
        },
        
        'delivery_requirements': {
            'lead_time_days': final_lead_time,
            'destination': logistics_details.get('destination', 'Buyer warehouse'),
            'timeline': logistics_details.get('timeline', 'As agreed'),
            'urgency_level': extracted_params.get('urgency_level', 'medium') if isinstance(extracted_params, dict) else 'medium'
        },
        
        'supplier_information': {
            'supplier_id': active_supplier.get('supplier_id', 'SUP_001'),
            'name': active_supplier.get('name', 'Supplier Company'),
            'location': active_supplier.get('location', 'Unknown'),
            'country': extract_country_from_location(active_supplier.get('location', '')),
            'email': active_supplier.get('email', 'supplier@company.com'),
            'phone': active_supplier.get('phone', '+X-XXX-XXX-XXXX'),
            'reliability_score': active_supplier.get('reputation_score', 5.0),
            'certifications': active_supplier.get('certifications', []),
            'specialties': active_supplier.get('specialties', []),
            'source': active_supplier.get('source', 'internal')
        },
        
        'buyer_information': {
            'company_name': buyer_company_name,
            'email': buyer_email,
            'contact_person': 'Procurement Manager',
            'address': 'Buyer Company Address',
            'phone': '+1-XXX-XXX-XXXX'
        },
        
        'negotiation_context': negotiation_analysis,
        
        'payment_constraints': extracted_params.get('payment_terms') if isinstance(extracted_params, dict) else None,
        
        'quote_reference': {
            'quote_id': quote_data.get('quote_id'),
            'quote_date': quote_data.get('generation_date'),
            'quoted_price': quote_price
        }
    }
    logger.info(f"Comprehensive context extraction complete. and the length is {len(json.dumps(context))} characters.")
    
    return context


def analyze_negotiation_journey(
    history: List[Dict[str, Any]], 
    messages: List[Dict[str, str]],
    state: AgentState
) -> Dict[str, Any]:
    """
    Analyze the complete negotiation journey to extract insights
    """
    
    analysis = {
        'total_rounds': len(history),
        'negotiation_difficulty': 'easy',  # Default
        'key_discussion_points': [],
        'concessions_made': [],
        'contentious_issues': [],
        'relationship_quality': 'neutral',
        'supplier_responsiveness': 'good'
    }
    
    if not history:
        return analysis
    
    # Analyze difficulty based on rounds
    if analysis['total_rounds'] >= 5:
        analysis['negotiation_difficulty'] = 'very_difficult'
    elif analysis['total_rounds'] >= 3:
        analysis['negotiation_difficulty'] = 'moderate'
    elif analysis['total_rounds'] >= 2:
        analysis['negotiation_difficulty'] = 'normal'
    
    # Extract key discussion points from history
    for round_data in history:
        intent = round_data.get('intent', '')
        
        if intent == 'counteroffer':
            analysis['key_discussion_points'].append('Price negotiation')
        elif intent == 'clarification_request':
            analysis['key_discussion_points'].append('Specification clarification')
        elif intent == 'delay':
            analysis['key_discussion_points'].append('Timeline discussion')
    
    # Analyze sentiment from negotiation analysis
    negotiation_analysis = state.get('negotiation_analysis', {})
    if isinstance(negotiation_analysis, dict):
        sentiment_indicators = negotiation_analysis.get('opportunities', [])
        if sentiment_indicators and len(sentiment_indicators) > 0:
            analysis['relationship_quality'] = 'positive'
        
        risk_factors = negotiation_analysis.get('risk_factors', [])
        if risk_factors and len(risk_factors) > 2:
            analysis['relationship_quality'] = 'cautious'
    
    # Extract concessions from final vs initial terms
    extracted_terms = state.get('extracted_terms', {})
    if isinstance(extracted_terms, dict):
        if extracted_terms.get('concessions_offered'):
            analysis['concessions_made'] = extracted_terms['concessions_offered']

    logger.info(f"Negotiation journey analysis complete, length of key points: {len(analysis['key_discussion_points'])}")
    
    return analysis


def extract_gsm_from_specs(quality_specs: List[str]) -> Optional[int]:
    """Extract GSM value from quality specifications"""
    for spec in quality_specs:
        if 'gsm' in spec.lower():
            # Try to extract number
            import re
            match = re.search(r'(\d+)\s*gsm', spec.lower())
            if match:
                return int(match.group(1))
    return None


def extract_country_from_location(location: str) -> str:
    """Extract country name from location string"""
    if not location:
        return "Unknown"
    
    # Common patterns: "City, Country" or just "Country"
    parts = location.split(',')
    return parts[-1].strip() if parts else location


def calculate_savings_percentage(original: Optional[float], final: Optional[float]) -> Optional[float]:
    """Calculate percentage savings achieved through negotiation"""
    if not original or not final or original == 0:
        return None
    
    savings = ((original - final) / original) * 100
    return max(0, savings)  # Only positive savings


# ============================================================================
# RISK ASSESSMENT ENGINE
# ============================================================================

def assess_contract_risk(context: Dict[str, Any]) -> RiskAssessment:
    """
    Comprehensive risk assessment for contract generation
    """
    
    supplier_info = context['supplier_information']
    pricing = context['pricing_terms']
    negotiation = context['negotiation_context']
    
    # Calculate individual risk scores (0-100, where 100 is highest risk)
    
    # 1. Supplier reliability risk
    reliability_score = supplier_info['reliability_score']  # 0-10 scale
    supplier_reliability_risk = (10 - reliability_score) * 10  # Convert to 0-100
    
    # 2. Negotiation complexity risk
    difficulty_map = {'easy': 10, 'normal': 25, 'moderate': 50, 'very_difficult': 80}
    negotiation_complexity_risk = difficulty_map.get(negotiation['negotiation_difficulty'], 25)
    
    # 3. Financial risk
    contract_value = pricing['total_value']
    if contract_value > 1000000:
        financial_risk = 80
    elif contract_value > 500000:
        financial_risk = 60
    elif contract_value > 100000:
        financial_risk = 40
    else:
        financial_risk = 20
    
    # 4. Geographic risk (based on supplier country)
    supplier_country = supplier_info['country'].lower()
    high_risk_regions = ['unknown', 'somalia', 'yemen', 'syria']
    medium_risk_regions = ['afghanistan', 'libya', 'iraq']
    
    if any(region in supplier_country for region in high_risk_regions):
        geographic_risk = 80
    elif any(region in supplier_country for region in medium_risk_regions):
        geographic_risk = 60
    else:
        geographic_risk = 20
    
    # 5. Quality risk (based on specifications complexity and certifications)
    certifications_required = len(context['fabric_specifications']['certifications'])
    if certifications_required >= 3:
        quality_risk = 60
    elif certifications_required >= 2:
        quality_risk = 40
    else:
        quality_risk = 20
    
    # Calculate weighted overall risk score
    weights = {
        'supplier': 0.30,
        'negotiation': 0.15,
        'financial': 0.25,
        'geographic': 0.15,
        'quality': 0.15
    }
    
    overall_risk_score = (
        supplier_reliability_risk * weights['supplier'] +
        negotiation_complexity_risk * weights['negotiation'] +
        financial_risk * weights['financial'] +
        geographic_risk * weights['geographic'] +
        quality_risk * weights['quality']
    )
    
    # Determine risk level
    if overall_risk_score >= 70:
        risk_level = 'critical'
    elif overall_risk_score >= 50:
        risk_level = 'high'
    elif overall_risk_score >= 30:
        risk_level = 'medium'
    else:
        risk_level = 'low'
    
    # Identify risk factors
    risk_factors = []
    if supplier_reliability_risk > 50:
        risk_factors.append(f"Low supplier reliability score ({reliability_score}/10)")
    if negotiation_complexity_risk > 50:
        risk_factors.append(f"Difficult negotiation process ({negotiation['total_rounds']} rounds)")
    if financial_risk > 50:
        risk_factors.append(f"High contract value (${contract_value:,.2f})")
    if geographic_risk > 50:
        risk_factors.append(f"High-risk supplier location ({supplier_info['country']})")
    if quality_risk > 50:
        risk_factors.append(f"Complex quality requirements ({certifications_required} certifications)")
    
    # Determine mitigation requirements
    mitigation_requirements = []
    recommended_clauses = []
    
    if risk_level in ['high', 'critical']:
        mitigation_requirements.append("Mandatory third-party pre-shipment inspection")
        mitigation_requirements.append("Bank guarantee or Letter of Credit required")
        mitigation_requirements.append("Stricter penalty clauses for delays and quality issues")
        mitigation_requirements.append("Enhanced quality control with in-line inspections")
        
        recommended_clauses.append("Performance Bond Clause (10-15% of contract value)")
        recommended_clauses.append("Stringent Force Majeure Provisions")
        recommended_clauses.append("Enhanced Liability Caps")
        
    elif risk_level == 'medium':
        mitigation_requirements.append("Pre-shipment inspection required")
        mitigation_requirements.append("Standard penalty clauses")
        
        recommended_clauses.append("Standard Indemnification Clause")
        recommended_clauses.append("Reasonable Force Majeure Provisions")
    
    else:  # low risk
        mitigation_requirements.append("Self-inspection with reporting")
        mitigation_requirements.append("Standard payment terms")
        
        recommended_clauses.append("Standard Commercial Terms")
    
    # Add specific recommendations based on individual risks
    if supplier_reliability_risk > 40:
        recommended_clauses.append("Supplier Performance Monitoring Clause")
        recommended_clauses.append("Right to Audit Supplier Facilities")
    
    if financial_risk > 50:
        recommended_clauses.append("Price Escalation Protection Clause")
        recommended_clauses.append("Currency Fluctuation Protection")
    
    if quality_risk > 40:
        recommended_clauses.append("Detailed Quality Specifications Annexure")
        recommended_clauses.append("Sample Approval Requirements")
        recommended_clauses.append("Testing Protocol Specifications")

    logger.warning(f"Risk assessment complete with overall risk level: {risk_level} and score: {overall_risk_score:.2f}")
    
    return RiskAssessment(
        overall_risk_level=risk_level,
        risk_score=overall_risk_score,
        supplier_reliability_risk=supplier_reliability_risk,
        negotiation_complexity_risk=negotiation_complexity_risk,
        financial_risk=financial_risk,
        geographic_risk=geographic_risk,
        quality_risk=quality_risk,
        risk_factors=risk_factors,
        mitigation_requirements=mitigation_requirements,
        recommended_clauses=recommended_clauses
    )


# ============================================================================
# COMPLIANCE & STANDARDS DETERMINATION
# ============================================================================

def determine_compliance_requirements(
    context: Dict[str, Any],
    risk_assessment: RiskAssessment
) -> ComplianceRequirements:
    """
    Determine compliance, certification, and quality standards requirements
    """
    
    fabric_specs = context['fabric_specifications']
    supplier_info = context['supplier_information']
    
    # Extract required certifications from original request
    required_certifications = fabric_specs.get('certifications', [])
    
    # Verify supplier has these certifications
    supplier_certifications = supplier_info.get('certifications', [])
    
    # Add warning if supplier missing required certifications
    missing_certs = [cert for cert in required_certifications if cert not in supplier_certifications]
    if missing_certs:
        # Add clause requiring certification acquisition
        required_certifications.append(
            f"Supplier must obtain {', '.join(missing_certs)} within 90 days of contract signing"
        )
    
    # Determine industry standards based on fabric type
    fabric_type = fabric_specs['fabric_type'].lower()
    industry_standards = []
    
    if 'organic' in fabric_type or 'GOTS' in required_certifications:
        industry_standards.extend(['GOTS Certification', 'USDA Organic Standards'])
    if 'cotton' in fabric_type:
        industry_standards.extend(['ISO 3801 (Woven Fabrics)', 'ASTM D3776 (Mass per Unit Area)'])
    if 'polyester' in fabric_type:
        industry_standards.append('ISO 2076 (Textile Fiber Identification)')
    
    # Always include these
    industry_standards.extend([
        'ISO 9001 Quality Management',
        'OEKO-TEX Standard 100 (or equivalent)',
        'ISO 3071 (Color Fastness Testing)'
    ])
    
    # Determine testing requirements
    testing_requirements = [
        'Fabric composition analysis',
        'GSM (Weight) verification',
        'Width measurement',
        'Color fastness to washing',
        'Color fastness to light',
        'Dimensional stability (shrinkage) test',
        'Tensile strength test',
        'Tear strength test'
    ]
    
    # Add specific tests based on fabric type
    if 'waterproof' in str(fabric_specs.get('quality_specs', [])).lower():
        testing_requirements.append('Water resistance test (ISO 4920)')
    
    # Determine inspection level based on risk
    if risk_assessment.overall_risk_level in ['high', 'critical']:
        inspection_level = 'strict'
        third_party_required = True
    elif risk_assessment.overall_risk_level == 'medium':
        inspection_level = 'enhanced'
        third_party_required = True
    else:
        inspection_level = 'normal'
        third_party_required = False
    
    # Geographic compliance requirements
    buyer_country = 'United States'  # Default, should be extracted
    supplier_country = supplier_info['country']
    
    geographic_compliance = {
        'import_regulations': f'{buyer_country} import regulations for textiles',
        'export_regulations': f'{supplier_country} export regulations',
        'customs_requirements': 'Harmonized System (HS) Code classification',
        'trade_agreements': 'Check applicable FTA benefits',
        'restricted_substances': 'REACH compliance (if EU), CPSIA (if US)'
    }
    
    # Required documentation
    documentation_requirements = [
        'Commercial Invoice',
        'Packing List',
        'Bill of Lading / Airway Bill',
        'Certificate of Origin',
        'Quality Certificate',
        'Test Reports (as specified)',
        'Insurance Certificate (if CIF/CIP)',
        'Inspection Certificate (if required)'
    ]
    
    if required_certifications:
        documentation_requirements.append(f'Certification documents: {", ".join(required_certifications)}')

    logger.info(f"Compliance requirements determined with {len(required_certifications)} certifications and {len(industry_standards)} standards.")  
    
    return ComplianceRequirements(
        required_certifications=required_certifications,
        industry_standards=list(set(industry_standards)),  # Remove duplicates
        testing_requirements=testing_requirements,
        inspection_level=inspection_level,
        third_party_inspection_required=third_party_required,
        geographic_compliance=geographic_compliance,
        documentation_requirements=documentation_requirements
    )


# ============================================================================
# FINANCIAL TERMS STRUCTURING
# ============================================================================

def structure_financial_terms(
    context: Dict[str, Any],
    risk_assessment: RiskAssessment
) -> FinancialTermsDetail:
    """
    Structure detailed financial terms with milestones and risk-based adjustments
    """
    
    pricing = context['pricing_terms']
    delivery = context['delivery_requirements']
    
    total_value = pricing['total_value']
    currency = pricing['currency']
    
    # Determine payment structure based on risk level
    risk_level = risk_assessment.overall_risk_level
    
    if risk_level in ['high', 'critical']:
        # High risk: Stricter payment terms
        advance_pct = 40
        bank_guarantee_required = True
        bank_guarantee_pct = 10
        retention_pct = 10
        
        payment_milestones = [
            {
                'milestone': 'Order Confirmation',
                'percentage': 40,
                'amount': total_value * 0.40,
                'trigger': 'Within 7 days of contract signing',
                'payment_method': 'Wire Transfer / Letter of Credit'
            },
            {
                'milestone': 'Production Completion & Pre-Shipment Inspection Pass',
                'percentage': 40,
                'amount': total_value * 0.40,
                'trigger': 'Upon successful PSI and submission of shipping documents',
                'payment_method': 'Wire Transfer'
            },
            {
                'milestone': 'Goods Receipt & Inspection Pass',
                'percentage': 10,
                'amount': total_value * 0.10,
                'trigger': 'Within 15 days of delivery and acceptance',
                'payment_method': 'Wire Transfer'
            },
            {
                'milestone': 'Final Retention Release',
                'percentage': 10,
                'amount': total_value * 0.10,
                'trigger': 'After 90 days of use with no quality issues',
                'payment_method': 'Wire Transfer'
            }
        ]
        
    elif risk_level == 'medium':
        # Medium risk: Balanced terms
        advance_pct = 30
        bank_guarantee_required = False
        bank_guarantee_pct = None
        retention_pct = 5
        
        payment_milestones = [
            {
                'milestone': 'Order Confirmation',
                'percentage': 30,
                'amount': total_value * 0.30,
                'trigger': 'Within 7 days of contract signing',
                'payment_method': 'Wire Transfer'
            },
            {
                'milestone': 'Pre-Shipment Inspection Pass',
                'percentage': 65,
                'amount': total_value * 0.65,
                'trigger': 'Upon successful PSI and presentation of shipping documents',
                'payment_method': 'Wire Transfer / LC'
            },
            {
                'milestone': 'Final Payment',
                'percentage': 5,
                'amount': total_value * 0.05,
                'trigger': 'Within 30 days of delivery and acceptance',
                'payment_method': 'Wire Transfer'
            }
        ]
        
    else:  # low risk
        # Low risk: Flexible terms
        advance_pct = 30
        bank_guarantee_required = False
        bank_guarantee_pct = None
        retention_pct = 0
        
        payment_milestones = [
            {
                'milestone': 'Order Confirmation',
                'percentage': 30,
                'amount': total_value * 0.30,
                'trigger': 'Within 7 days of contract signing',
                'payment_method': 'Wire Transfer'
            },
            {
                'milestone': 'Balance Payment',
                'percentage': 70,
                'amount': total_value * 0.70,
                'trigger': 'Against shipping documents (Net 30 from shipment)',
                'payment_method': 'Wire Transfer'
            }
        ]
    
    logger.info(f"Financial terms structured for risk level: {risk_level} with {len(payment_milestones)} milestones.")
    
    # Currency terms
    currency_terms = f"""
    All payments shall be made in {currency}. 
    Exchange rate: As per the prevailing rate on the date of invoice.
    Currency risk: Borne by Buyer unless otherwise specified.
    Payment method: International wire transfer to supplier's designated bank account.
    Bank charges: Buyer pays originating bank charges, Supplier pays receiving bank charges.
    """
    
    # Credit period
    credit_period_days = 30  # Default Net 30
    
    # Late payment interest (risk-adjusted)
    if risk_level in ['high', 'critical']:
        late_payment_interest_rate = 18.0  # 18% per annum
    elif risk_level == 'medium':
        late_payment_interest_rate = 12.0  # 12% per annum
    else:
        late_payment_interest_rate = 8.0  # 8% per annum
    
    # Price escalation clause (for long lead times)
    lead_time = delivery['lead_time_days']
    if lead_time > 90:
        price_escalation_clause = f"""
        If the delivery period exceeds {lead_time} days due to causes beyond supplier's control,
        the supplier may request price revision based on documented cost increases.
        Any price adjustment requires mutual written agreement.
        """
    else:
        price_escalation_clause = None

    logger.info("Financial terms structuring complete.")
    
    return FinancialTermsDetail(
        payment_milestones=payment_milestones,
        currency_terms=currency_terms.strip(),
        credit_period_days=credit_period_days,
        late_payment_interest_rate=late_payment_interest_rate,
        bank_guarantee_required=bank_guarantee_required,
        bank_guarantee_amount_percentage=bank_guarantee_pct,
        price_escalation_clause=price_escalation_clause,
        retention_amount_percentage=retention_pct
    )


# ============================================================================
# DELIVERY TERMS STRUCTURING
# ============================================================================

def structure_delivery_terms(
    context: Dict[str, Any],
    risk_assessment: RiskAssessment
) -> DeliveryTermsDetail:
    """
    Structure detailed delivery terms with calculated dates and responsibilities
    """
    
    delivery = context['delivery_requirements']
    supplier_info = context['supplier_information']
    fabric_specs = context['fabric_specifications']
    
    # Calculate milestone dates
    order_date = datetime.now()
    lead_time_days = delivery['lead_time_days']
    
    # Add buffer based on supplier reliability
    reliability_score = supplier_info['reliability_score']
    if reliability_score < 6:
        buffer_days = 10  # Add 10-day buffer for unreliable suppliers
    elif reliability_score < 8:
        buffer_days = 5   # Add 5-day buffer
    else:
        buffer_days = 0   # No buffer for reliable suppliers
    
    adjusted_lead_time = lead_time_days + buffer_days
    
    # Calculate dates
    production_start_date = order_date + timedelta(days=7)  # 1 week for order processing
    production_duration = int(adjusted_lead_time * 0.6)  # 60% for production
    inspection_date = production_start_date + timedelta(days=production_duration)
    shipment_date = inspection_date + timedelta(days=3)  # 3 days post-inspection
    
    # Shipping duration based on method
    supplier_country = supplier_info['country'].lower()
    if 'china' in supplier_country or 'vietnam' in supplier_country or 'bangladesh' in supplier_country:
        shipping_days = 30  # Sea freight from Asia
    elif 'turkey' in supplier_country or 'portugal' in supplier_country:
        shipping_days = 20  # From Europe/Middle East
    else:
        shipping_days = 25  # Default
    
    delivery_date = shipment_date + timedelta(days=shipping_days)
    
    # Determine Incoterm based on risk and value
    contract_value = context['pricing_terms']['total_value']
    if contract_value > 100000:
        incoterm = 'CIF'  # Supplier arranges insurance for high-value
        insurance_responsibility = 'Supplier arranges and pays for insurance; Buyer is beneficiary'
    else:
        incoterm = 'FOB'  # Standard for lower values
        insurance_responsibility = 'Buyer responsible for insurance from port of loading'
    
    # Incoterm responsibilities breakdown
    if incoterm == 'FOB':
        incoterm_responsibilities = """
        FOB (Free On Board) - Port of Loading:
        
        SUPPLIER RESPONSIBILITIES:
        - Deliver goods on board the vessel at the port of loading
        - Handle export customs clearance
        - Pay all costs until goods are on board (including loading)
        - Provide export documentation
        
        BUYER RESPONSIBILITIES:
        - Arrange and pay for main carriage (sea freight)
        - Arrange and pay for insurance
        - Handle import customs clearance
        - Pay all costs from vessel departure
        - Unloading at destination port
        
        RISK TRANSFER: When goods pass ship's rail at port of loading
        """
    else:  # CIF
        incoterm_responsibilities = """
        CIF (Cost, Insurance and Freight) - Destination Port:
        
        SUPPLIER RESPONSIBILITIES:
        - Deliver goods on board vessel at port of loading
        - Handle export customs clearance
        - Pay for sea freight to destination port
        - Arrange and pay for minimum insurance coverage
        - Provide shipping and insurance documents
        
        BUYER RESPONSIBILITIES:
        - Handle import customs clearance
        - Pay import duties and taxes
        - Unloading at destination port
        - Transportation from port to final destination
        
        RISK TRANSFER: When goods pass ship's rail at port of loading
        (Note: Supplier pays freight and insurance but risk transfers at loading)
        """
    
    # Partial shipment policy
    quantity = fabric_specs['quantity']
    if quantity > 10000:
        partial_shipment_allowed = True
        partial_shipment_conditions = """
        Partial shipments are permitted under the following conditions:
        - Each shipment must be at least 20% of total order quantity
        - Maximum of 3 partial shipments allowed
        - Each shipment must meet all quality standards independently
        - Pro-rata payment for each accepted shipment
        - All shipments must be completed within the contracted delivery period
        - Supplier must notify Buyer of partial shipment plan at least 14 days in advance
        """
    else:
        partial_shipment_allowed = False
        partial_shipment_conditions = None
    
    # Shipping method
    if delivery['urgency_level'] == 'urgent':
        shipping_method = 'Air Freight (if agreed and price adjusted)'
    else:
        shipping_method = 'Sea Freight (Full Container Load - FCL preferred)'
    
    # Required shipping documents
    required_shipping_documents = [
        'Commercial Invoice (3 originals + 3 copies)',
        'Packing List (3 copies)',
        'Bill of Lading (Full set of originals)',
        'Certificate of Origin (Form A if applicable)',
        'Inspection Certificate (if required)',
        'Quality Test Reports',
        'Insurance Policy/Certificate (if CIF/CIP terms)'
    ]
    
    if fabric_specs.get('certifications'):
        required_shipping_documents.append(f"Certification Documents: {', '.join(fabric_specs['certifications'])}")
    
    logger.info(f"Delivery terms structuring complete. Calculated delivery date: {delivery_date.strftime('%Y-%m-%d')}, Incoterm: {incoterm}")
    
    return DeliveryTermsDetail(
        order_date=order_date.strftime('%Y-%m-%d'),
        production_start_date=production_start_date.strftime('%Y-%m-%d'),
        inspection_date=inspection_date.strftime('%Y-%m-%d'),
        shipment_date=shipment_date.strftime('%Y-%m-%d'),
        delivery_date=delivery_date.strftime('%Y-%m-%d'),
        incoterm=incoterm,
        incoterm_responsibilities=incoterm_responsibilities.strip(),
        partial_shipment_allowed=partial_shipment_allowed,
        partial_shipment_conditions=partial_shipment_conditions.strip() if partial_shipment_conditions else None,
        shipping_method=shipping_method,
        insurance_responsibility=insurance_responsibility,
        required_shipping_documents=required_shipping_documents
    )


# ============================================================================
# QUALITY ASSURANCE FRAMEWORK
# ============================================================================

def structure_quality_framework(
    context: Dict[str, Any],
    compliance: ComplianceRequirements,
    risk_assessment: RiskAssessment
) -> QualityAssuranceFramework:
    """
    Structure comprehensive quality assurance framework
    """
    
    fabric_specs = context['fabric_specifications']
    
    # Determine AQL level based on risk and fabric type
    risk_level = risk_assessment.overall_risk_level
    
    if risk_level in ['high', 'critical']:
        aql_level = 'AQL 1.5 (Stringent)'
    elif risk_level == 'medium':
        aql_level = 'AQL 2.5 (Normal)'
    else:
        aql_level = 'AQL 4.0 (General)'
    
    # Sampling procedure
    sampling_procedure = f"""
    Sampling Method: Random sampling as per ISO 2859-1
    Acceptable Quality Level: {aql_level}
    
    Sample size determination:
    - For lots up to 3,200 units: Sample size 125 units
    - For lots 3,201-10,000 units: Sample size 200 units
    - For lots over 10,000 units: Sample size 315 units
    
    Inspection procedure:
    - Random selection from different production batches
    - Visual inspection for all samples
    - Physical testing on representative samples
    - Documentation of all findings with photographs
    """
    
    # Inspection requirements based on risk
    if risk_level in ['high', 'critical']:
        pre_production_sample_required = True
        in_line_inspection_required = True
        pre_shipment_inspection_required = True
        third_party_inspector = 'SGS, Bureau Veritas, Intertek, or approved equivalent'
    elif risk_level == 'medium':
        pre_production_sample_required = True
        in_line_inspection_required = False
        pre_shipment_inspection_required = True
        third_party_inspector = 'Recommended but optional (SGS, Bureau Veritas, or equivalent)'
    else:
        pre_production_sample_required = True
        in_line_inspection_required = False
        pre_shipment_inspection_required = True
        third_party_inspector = None
    
    # Inspection standards
    inspection_standards = compliance.industry_standards.copy()
    inspection_standards.extend([
        'ASTM D3776 - Mass Per Unit Area',
        'ASTM D5034 - Breaking Strength',
        'AATCC 61 - Colorfastness to Washing',
        'ISO 105-B02 - Colorfastness to Light'
    ])
    
    # Test requirements from compliance
    test_requirements = compliance.testing_requirements
    
    # Defect tolerance levels
    defect_tolerance = {
        'critical_defects': 0.0,  # 0% tolerance for critical defects
        'major_defects': 2.5,     # 2.5% tolerance for major defects
        'minor_defects': 4.0      # 4.0% tolerance for minor defects
    }
    
    if risk_level in ['high', 'critical']:
        defect_tolerance['major_defects'] = 1.5  # Stricter for high risk
        defect_tolerance['minor_defects'] = 2.5
    
    # Acceptance criteria
    acceptance_criteria = f"""
    ACCEPTANCE CRITERIA:
    
    The goods shall be accepted if:
    1. All critical defects = 0% (absolute requirement)
    2. Major defects ≤ {defect_tolerance['major_defects']}% of inspected quantity
    3. Minor defects ≤ {defect_tolerance['minor_defects']}% of inspected quantity
    4. All test results meet specified parameters:
       - GSM: Within ±5% of specified value
       - Width: Within ±2% of specified value
       - Color: Within Delta E ≤ 1.5 for solid colors
       - Shrinkage: Maximum 3% for pre-shrunk fabric
    5. All required certifications are valid and provided
    6. Packaging is intact and labeled correctly
    
    DEFECT CLASSIFICATION:
    - Critical: Defects that render the fabric unusable (holes, severe stains, wrong composition)
    - Major: Defects that significantly reduce usability (color shade variation, GSM deviation >5%, width issues)
    - Minor: Defects that do not affect functionality (minor stitching irregularities, small marks)
    """
    
    # Remedy for rejection
    remedy_for_rejection = f"""
    REJECTION AND REMEDY PROCEDURES:
    
    If goods fail inspection:
    
    1. IMMEDIATE ACTIONS:
       - Inspector issues Non-Conformance Report (NCR) within 24 hours
       - Supplier notified immediately with detailed findings and photographic evidence
       - Shipment held pending resolution
    
    2. REMEDY OPTIONS (Supplier's choice, subject to Buyer approval):
       
       Option A - REPAIR/REWORK:
       - Supplier repairs/sorts defective goods at supplier's facility
       - Re-inspection required after rework (costs borne by Supplier)
       - Timeline: Within 7 days of rejection notice
       
       Option B - REPLACEMENT:
       - Supplier manufactures and provides replacement goods meeting specifications
       - Re-inspection required
       - Timeline: Within {context['delivery_requirements']['lead_time_days']} days of rejection notice
       - Original rejected goods returned to Supplier at Supplier's cost
       
       Option C - PRICE REDUCTION:
       - Mutually agreed price reduction based on severity of defects
       - Buyer retains goods with price adjustment (for minor issues only)
       - Requires written agreement from both parties
       
       Option D - CANCELLATION:
       - Contract cancellation for goods that cannot be remedied
       - Full refund of payments made for rejected portion
       - Supplier liable for inspection costs and any documented losses
    
    3. COST ALLOCATION:
       - All inspection costs for rejected goods: Supplier
       - Re-inspection costs: Supplier
       - Shipping costs for rejected goods return: Supplier
       - Replacement goods shipping: Supplier (if FOB, upgraded to include freight)
    
    4. PENALTY FOR REPEATED REJECTION:
       - Second rejection: Supplier pays 5% penalty on rejected portion value
       - Third rejection: Buyer has right to terminate contract with full refund plus 10% penalty
    """

    logger.info(f"Quality assurance framework structured for risk level: {risk_level} with AQL: {aql_level}")
    
    return QualityAssuranceFramework(
        aql_level=aql_level,
        sampling_procedure=sampling_procedure.strip(),
        pre_production_sample_required=pre_production_sample_required,
        in_line_inspection_required=in_line_inspection_required,
        pre_shipment_inspection_required=pre_shipment_inspection_required,
        third_party_inspector=third_party_inspector,
        inspection_standards=inspection_standards,
        test_requirements=test_requirements,
        defect_tolerance=defect_tolerance,
        acceptance_criteria=acceptance_criteria.strip(),
        remedy_for_rejection=remedy_for_rejection.strip()
    )


# ============================================================================
# ENHANCED CONTRACT GENERATION WITH AI
# ============================================================================

def create_enhanced_contract_terms_prompt():
    """Enhanced prompt for structuring contract terms with all details"""
    
    system_prompt = """You are an expert legal AI assistant specializing in B2B textile procurement contracts. You have been provided with comprehensive context including risk assessment, compliance requirements, financial details, delivery terms, and quality frameworks.

Your task is to structure all these elements into a cohesive ContractTerms format that will be used to generate the final contract document.

**CRITICAL REQUIREMENTS:**

1. **Fabric Specifications**: Structure as detailed text including:
   - Fabric type, composition, GSM
   - Quality specifications and tolerances
   - Color, width, finish requirements
   - All certifications required

2. **Financial Terms**: Incorporate the detailed payment milestones, currency terms, late payment provisions, and any bank guarantee requirements

3. **Delivery Terms**: Include calculated milestone dates, Incoterm responsibilities, partial shipment policies, and required documentation

4. **Quality Standards**: Integrate AQL levels, inspection procedures, testing requirements, and acceptance criteria

5. **Penalties & Incentives**: Based on risk level, structure appropriate:
   - Delay penalties (percentage per day/week)
   - Quality failure remedies
   - Early delivery incentives (if applicable)

6. **Force Majeure**: Comprehensive list of events and procedures

7. **Dispute Resolution**: Clear escalation procedure and arbitration mechanism

Ensure all terms are specific, measurable, and enforceable."""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Structure comprehensive contract terms using this detailed context:

**FABRIC SPECIFICATIONS:**
{fabric_specifications}

**FINANCIAL TERMS DETAIL:**
{financial_terms}

**DELIVERY TERMS DETAIL:**
{delivery_terms}

**QUALITY FRAMEWORK:**
{quality_framework}

**RISK ASSESSMENT:**
Risk Level: {risk_level}
Risk Score: {risk_score}
Risk Factors: {risk_factors}
Mitigation Required: {mitigation_requirements}
Recommended Clauses: {recommended_clauses}

**COMPLIANCE REQUIREMENTS:**
Required Certifications: {required_certifications}
Industry Standards: {industry_standards}
Inspection Level: {inspection_level}
Third-party Inspection: {third_party_inspection}

**NEGOTIATION CONTEXT:**
Rounds: {negotiation_rounds}
Difficulty: {negotiation_difficulty}
Relationship Quality: {relationship_quality}
Key Concessions: {key_concessions}

Generate structured ContractTerms with all details integrated.""")
    ])


def create_enhanced_contract_drafting_prompt():
    """Enhanced prompt for drafting complete contract with all improvements"""
    
    system_prompt = """You are a senior legal counsel specializing in international B2B textile procurement. You will draft a complete, legally sound contract incorporating all provided terms, risk mitigations, and compliance requirements.

**CONTRACT STRUCTURE REQUIREMENTS:**

**1. PREAMBLE & PARTIES**
- Full legal names and addresses of both parties
- Contract purpose and date
- Recitals establishing background and intent

**2. DEFINITIONS**
- All technical and commercial terms clearly defined
- Industry-specific terminology explained
- Measurement units and quality parameters

**3. SCOPE OF SUPPLY**
- Detailed fabric specifications with tolerances
- Quantity with acceptable variance (if any)
- Quality grade and certification requirements

**4. PRICING & PAYMENT TERMS**
- Detailed payment milestone schedule with triggers
- Bank details (placeholder for supplier to provide)
- Late payment provisions
- Currency and exchange rate terms
- Bank guarantee requirements (if applicable)

**5. DELIVERY TERMS**
- Specific milestone dates with buffers
- Incoterm explanation with responsibilities
- Partial shipment policy
- Required shipping documentation
- Delivery acceptance procedure

**6. QUALITY ASSURANCE**
- Pre-production sample approval process
- Inspection procedures (in-line, pre-shipment)
- Third-party inspection requirements
- AQL standards and sampling methods
- Testing requirements and acceptance criteria
- Remedy procedures for rejection

**7. REPRESENTATIONS & WARRANTIES**
- Supplier warrants quality and fitness for purpose
- Certification validity warranties
- Compliance with specifications
- Warranty period and remedy

**8. PENALTIES & REMEDIES**
- Delay penalties (specific percentage/amount per day)
- Quality failure remedies
- Liquidated damages provisions
- Right to terminate for material breach

**9. FORCE MAJEURE**
- Comprehensive list of force majeure events
- Notification requirements
- Suspension vs. termination criteria
- Evidence and documentation requirements

**10. INTELLECTUAL PROPERTY & CONFIDENTIALITY**
- IP ownership clarifications
- Confidentiality obligations
- Non-disclosure requirements

**11. INSURANCE & INDEMNITY**
- Insurance requirements (cargo, liability)
- Indemnification clauses
- Limitation of liability

**12. COMPLIANCE & REGULATORY**
- Export/import compliance
- Sanction compliance
- Environmental and social compliance

**13. DISPUTE RESOLUTION**
- Negotiation (7 days)
- Mediation (14 days)
- Arbitration (venue, rules, language)
- Governing law and jurisdiction

**14. GENERAL PROVISIONS**
- Entire agreement clause
- Amendment procedure
- Assignment and subcontracting
- Notices procedure
- Severability
- Waiver

**15. TERM & TERMINATION**
- Contract effective date and duration
- Termination rights and procedures
- Effects of termination
- Survival of obligations

**16. SIGNATURE BLOCKS**
- Formal signature blocks for both parties
- Date and place of execution
- Witness requirements (if applicable)

**DRAFTING PRINCIPLES:**
- Use clear, precise legal language
- Include specific numbers, dates, and amounts
- Balance protection for both parties
- Ensure all terms are enforceable
- Reference annexures where detailed specifications are attached
- Use professional formatting with section numbering

Generate a complete, professional contract ready for legal review."""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Draft a complete textile procurement contract using these structured terms and context:

**CONTRACT IDENTIFICATION:**
Contract ID: {contract_id}
Contract Type: {contract_type}
Governing Law: {governing_law}
Creation Date: {creation_date}

**PARTIES:**
BUYER: {buyer_company}
SUPPLIER: {supplier_company}

**STRUCTURED CONTRACT TERMS:**
{contract_terms}

**RISK PROFILE:**
Risk Level: {risk_level}
Risk Score: {risk_score}/100
Key Risks: {risk_factors}
Mitigation Measures: {mitigation_requirements}

**COMPLIANCE FRAMEWORK:**
Certifications Required: {required_certifications}
Inspection Level: {inspection_level}
Third-party Inspection: {third_party_inspection}

**NEGOTIATION BACKGROUND:**
- Total Rounds: {negotiation_rounds}
- Negotiation Difficulty: {negotiation_difficulty}
- Relationship Quality: {relationship_quality}
- Agreement Confidence: {agreement_confidence}

**SPECIAL INSTRUCTIONS:**
1. Include all risk-based protective clauses
2. Ensure compliance requirements are contractually binding
3. Reflect the negotiation outcome faithfully
4. Add appropriate penalty clauses based on risk level
5. Include comprehensive force majeure provisions
6. Structure payment terms to match provided milestones

Generate the complete contract document with all sections, ready for execution.""")
    ])


# Initialize enhanced models
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
terms_model = model.with_structured_output(ContractTerms)
contract_model = model.with_structured_output(DraftedContract)

enhanced_terms_prompt = create_enhanced_contract_terms_prompt()
enhanced_contract_prompt = create_enhanced_contract_drafting_prompt()


# ============================================================================
# MAIN IMPROVED CONTRACT INITIATION FUNCTION
# ============================================================================

def initiate_contract(state: AgentState):
    """
    IMPROVED Node: initiate_contract - Comprehensive Contract Drafting Agent
    
    Improvements:
    1. Comprehensive context extraction from proper model parsing
    2. Risk-based contract customization
    3. Detailed financial terms with milestone payments
    4. Calculated delivery dates with buffers
    5. Comprehensive quality assurance framework
    6. Compliance and certification integration
    7. Industry standards incorporation
    8. Geographic and jurisdiction considerations
    9. Negotiation history integration
    10. Dynamic clause selection based on risk
    
    Process Flow:
    1. Extract comprehensive context from state (proper model parsing)
    2. Assess contract risk holistically
    3. Determine compliance and quality requirements
    4. Structure detailed financial terms with milestones
    5. Calculate delivery schedule with realistic dates
    6. Build quality assurance framework
    7. Generate AI-powered contract terms structure
    8. Draft complete professional contract document
    9. Perform multi-dimensional validation
    10. Generate actionable recommendations
    
    Args:
        state: Current agent state with complete negotiation history
    
    Returns:
        dict: State updates with comprehensive drafted contract
    """
    
    try:
        # print("\n" + "="*80)
        # print("🏗️  INITIATING COMPREHENSIVE CONTRACT DRAFTING")
        # print("="*80)

        logger.info("INITIATING COMPREHENSIVE CONTRACT DRAFTING")
        
        # ========================================
        # PHASE 1: COMPREHENSIVE CONTEXT EXTRACTION
        # ========================================


        logger.info("Extracting comprehensive context from agent state...")
        context = extract_comprehensive_context(state)
        
        
        logger.info(f"Comprehensive context extracted for supplier: {context['supplier_information']['name']}, fabric: {context['fabric_specifications']['fabric_type']}, quantity: {context['fabric_specifications']['quantity']:,} {context['fabric_specifications']['unit']}, contract value: {context['pricing_terms']['currency']} {context['pricing_terms']['total_value']:,.2f}, negotiation rounds: {context['negotiation_context']['total_rounds']}.")


        # ========================================
        # PHASE 2: RISK ASSESSMENT
        # ========================================


        logger.info("Performing holistic contract risk assessment...")
        risk_assessment = assess_contract_risk(context)
        

        logger.info(f"Risk assessment complete. Overall Risk Level: {risk_assessment.overall_risk_level.upper()}, Risk Score: {risk_assessment.risk_score:.1f}/100, Supplier Reliability Risk: {risk_assessment.supplier_reliability_risk:.1f}/100, Financial Risk: {risk_assessment.financial_risk:.1f}/100, Risk Factors Identified: {len(risk_assessment.risk_factors)}.")
        
        if risk_assessment.risk_factors:
            
            logger.info("Risk Factors Identified:")
            for rf in risk_assessment.risk_factors[:3]:
                logger.info(f"    - {rf}")
        
        # ========================================
        # PHASE 3: COMPLIANCE & STANDARDS
        # ========================================
    
        logger.info("Determining compliance and quality requirements...")
        compliance = determine_compliance_requirements(context, risk_assessment)
        

        logger.info(f"Compliance requirements determined. Inspection Level: {compliance.inspection_level.upper()}, Third-party Inspection: {'Required' if compliance.third_party_inspection_required else 'Optional'}, Required Certifications: {len(compliance.required_certifications)}, Industry Standards: {len(compliance.industry_standards)}, Testing Requirements: {len(compliance.testing_requirements)}.")
        
        # ========================================
        # PHASE 4: FINANCIAL TERMS STRUCTURING
        # ========================================

        logger.info("Structuring detailed financial terms...")
        financial_terms = structure_financial_terms(context, risk_assessment)
        

        logger.info(f"Financial terms structured with {len(financial_terms.payment_milestones)} payment milestones, bank guarantee: {'required' if financial_terms.bank_guarantee_required else 'not required'}, late payment interest: {financial_terms.late_payment_interest_rate}%, retention: {financial_terms.retention_amount_percentage or 0}%.")
        
        # ========================================
        # PHASE 5: DELIVERY TERMS STRUCTURING
        # ========================================

        logger.info("Structuring detailed delivery terms...")
        delivery_terms = structure_delivery_terms(context, risk_assessment)


        logger.info(f"Delivery terms structured. Calculated delivery date: {delivery_terms.delivery_date}, Incoterm: {delivery_terms.incoterm}, Partial shipments: {'allowed' if delivery_terms.partial_shipment_allowed else 'not allowed'}.")
        
        # ========================================
        # PHASE 6: QUALITY FRAMEWORK
        # ========================================

        logger.info("Building comprehensive quality assurance framework...")
        quality_framework = structure_quality_framework(context, compliance, risk_assessment)
        

        logger.info(f"Quality assurance framework built with AQL Level: {quality_framework.aql_level}, Pre-production Sample: {'Required' if quality_framework.pre_production_sample_required else 'Not required'}, In-line Inspection: {'Required' if quality_framework.in_line_inspection_required else 'Not required'}, Pre-shipment Inspection: {'Required' if quality_framework.pre_shipment_inspection_required else 'Not required'}.")
        
        # ========================================
        # PHASE 7: GENERATE CONTRACT ID & METADATA
        # ========================================
        logger.info("Generating unique contract ID and metadata...")
        contract_id = f"CTXT_{datetime.now().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8].upper()}"
        
        buyer_info = context['buyer_information']
        supplier_info = context['supplier_information']
        
        # Create JSON strings for company data
        buyer_company_json = json.dumps(buyer_info)
        supplier_company_json = json.dumps(supplier_info)
        
        contract_metadata = ContractMetadata(
            contract_id=contract_id,
            contract_type="textile_procurement_agreement",
            contract_version="1.0",
            buyer_company=buyer_company_json,
            supplier_company=supplier_company_json,
            creation_date=datetime.now().isoformat(),
            effective_date=None,
            expiry_date=None,
            governing_law="International Commercial Law / CISG",
            jurisdiction=f"{buyer_info.get('country', 'TBD')} or Neutral Arbitration"
        )
        

        logger.info(f"Contract ID Generated: {contract_id}")
        
        # ========================================
        # PHASE 8: AI-POWERED TERMS STRUCTURING
        # ========================================

        logger.info("AI structuring of comprehensive contract terms...")
        
        terms_formatted_prompt = enhanced_terms_prompt.invoke({
            "fabric_specifications": json.dumps(context['fabric_specifications'], indent=2),
            "financial_terms": json.dumps(financial_terms.model_dump(), indent=2),
            "delivery_terms": json.dumps(delivery_terms.model_dump(), indent=2),
            "quality_framework": json.dumps(quality_framework.model_dump(), indent=2),
            "risk_level": risk_assessment.overall_risk_level,
            "risk_score": risk_assessment.risk_score,
            "risk_factors": ', '.join(risk_assessment.risk_factors),
            "mitigation_requirements": ', '.join(risk_assessment.mitigation_requirements),
            "recommended_clauses": ', '.join(risk_assessment.recommended_clauses),
            "required_certifications": ', '.join(compliance.required_certifications),
            "industry_standards": ', '.join(compliance.industry_standards[:5]),
            "inspection_level": compliance.inspection_level,
            "third_party_inspection": str(compliance.third_party_inspection_required),
            "negotiation_rounds": context['negotiation_context']['total_rounds'],
            "negotiation_difficulty": context['negotiation_context']['negotiation_difficulty'],
            "relationship_quality": context['negotiation_context']['relationship_quality'],
            "key_concessions": ', '.join(context['negotiation_context'].get('concessions_made', ['None']))
        })
        
        structured_terms: ContractTerms = terms_model.invoke(terms_formatted_prompt)
        logger.success("✓ Contract terms structured by AI.")
        
        # ========================================
        # PHASE 9: AI-POWERED CONTRACT DRAFTING
        # ========================================
        logger.success("AI drafting of complete contract document...")
        
        contract_formatted_prompt = enhanced_contract_prompt.invoke({
            "contract_id": contract_id,
            "contract_type": "Textile Procurement Agreement",
            "governing_law": contract_metadata.governing_law,
            "creation_date": datetime.now().strftime("%B %d, %Y"),
            "buyer_company": buyer_info['company_name'],
            "supplier_company": supplier_info['name'],
            "contract_terms": json.dumps(structured_terms.model_dump(), indent=2),
            "risk_level": risk_assessment.overall_risk_level,
            "risk_score": risk_assessment.risk_score,
            "risk_factors": ', '.join(risk_assessment.risk_factors[:3]),
            "mitigation_requirements": ', '.join(risk_assessment.mitigation_requirements[:3]),
            "required_certifications": ', '.join(compliance.required_certifications),
            "inspection_level": compliance.inspection_level,
            "third_party_inspection": str(compliance.third_party_inspection_required),
            "negotiation_rounds": context['negotiation_context']['total_rounds'],
            "negotiation_difficulty": context['negotiation_context']['negotiation_difficulty'],
            "relationship_quality": context['negotiation_context']['relationship_quality'],
            "agreement_confidence": f"{state.get('analysis_confidence', 0.8):.2f}"
        })
        
        drafted_contract: DraftedContract = contract_model.invoke(contract_formatted_prompt)
        
        # Enhance contract with metadata
        drafted_contract.contract_id = contract_id
        drafted_contract.contract_terms_summary = json.dumps(structured_terms.model_dump())
        drafted_contract.contract_metadata_summary = json.dumps(contract_metadata.model_dump())
        drafted_contract.generation_timestamp = datetime.now().isoformat()
        
        logger.success("✓ Complete contract document drafted by AI.")
        
        # ========================================
        # PHASE 10: MULTI-DIMENSIONAL VALIDATION
        # ========================================
        logger.info("Performing multi-dimensional contract validation...")
        validation_results = enhanced_contract_validation(
            drafted_contract,
            structured_terms,
            risk_assessment,
            compliance,
            context
        )
        
        # print(f"✓ Overall Validation Score: {validation_results['overall_score']:.1%}")
        # print(f"  - Legal Completeness: {validation_results['legal_completeness']:.1%}")
        # print(f"  - Financial Soundness: {validation_results['financial_soundness']:.1%}")
        # print(f"  - Risk Coverage: {validation_results['risk_coverage']:.1%}")
        # print(f"  - Compliance Adequacy: {validation_results['compliance_adequacy']:.1%}")
        # print(f"  - Operational Feasibility: {validation_results['operational_feasibility']:.1%}")

        logger.success(f"✓ Overall Validation Score: {validation_results['overall_score']:.1%}")
        logger.success(f"  - Legal Completeness: {validation_results['legal_completeness']:.1%}")
        logger.success(f"  - Financial Soundness: {validation_results['financial_soundness']:.1%}")
        logger.success(f"  - Risk Coverage: {validation_results['risk_coverage']:.1%}")
        logger.success(f"  - Compliance Adequacy: {validation_results['compliance_adequacy']:.1%}")
        logger.success(f"  - Operational Feasibility: {validation_results['operational_feasibility']:.1%}")

        
        # ========================================
        # PHASE 11: RECOMMENDATIONS & NEXT STEPS
        # ========================================
        logger.info("Generating actionable recommendations based on validation...")
        recommendations = generate_comprehensive_recommendations(
            drafted_contract,
            context,
            risk_assessment,
            compliance,
            validation_results
        )
        
        drafted_contract.recommended_actions = recommendations
        

        logger.success(f"✓ Generated {len(recommendations)} action items")
        
        # ========================================
        # PHASE 12: PREPARE STATE UPDATES
        # ========================================
        logger.info("Preparing state updates with drafted contract and details...")
        
        # Create comprehensive assistant message
        assistant_message = generate_contract_summary_message(
            contract_id,
            context,
            risk_assessment,
            financial_terms,
            delivery_terms,
            quality_framework,
            validation_results,
            recommendations
        )
        
        state_updates = {
            "drafted_contract": drafted_contract.model_dump(),
            "contract_terms": structured_terms.model_dump(),
            "contract_metadata": contract_metadata.model_dump(),
            "contract_id": contract_id,
            "contract_ready": True,
            "contract_confidence": drafted_contract.confidence_score,
            "requires_legal_review": drafted_contract.legal_review_required,
            
            # Detailed components
            "risk_assessment": risk_assessment.model_dump(),
            "compliance_requirements": compliance.model_dump(),
            "financial_terms_detail": financial_terms.model_dump(),
            "delivery_terms_detail": delivery_terms.model_dump(),
            "quality_framework": quality_framework.model_dump(),
            "validation_results": validation_results,
            
            # Workflow control
            "next_step": "legal_review_required",
            "messages": [assistant_message],
            "status": "contract_drafted",
            "contract_generation_timestamp": datetime.now().isoformat()
        }
        


        logger.success("CONTRACT DRAFTING COMPLETED SUCCESSFULLY")
        logger.success(f"Contract ID: {contract_id}")
        logger.success(f"Overall Confidence: {drafted_contract.confidence_score:.1%}")
        logger.success(f"Validation Score: {validation_results['overall_score']:.1%}")
        logger.success(f"Next Step: {state_updates['next_step'].upper()}")
        
        
        return state_updates
        
    except Exception as e:
        error_message = f"❌ Error in contract drafting: {str(e)}"
        logger.error(error_message)
        import traceback
        traceback.print_exc()
        
        return {
            "error": str(e),
            "messages": [error_message],
            "next_step": "handle_error",
            "status": "contract_drafting_error"
        }


# ============================================================================
# ENHANCED VALIDATION
# ============================================================================

def enhanced_contract_validation(
    drafted_contract: DraftedContract,
    structured_terms: ContractTerms,
    risk_assessment: RiskAssessment,
    compliance: ComplianceRequirements,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Multi-dimensional validation of drafted contract
    """
    
    validation_scores = {}
    
    # 1. Legal Completeness (mandatory clauses present)
    mandatory_clauses = [
        'parties', 'preamble', 'definitions', 'scope', 'price', 'payment',
        'delivery', 'quality', 'warranty', 'liability', 'indemnity',
        'force majeure', 'dispute resolution', 'governing law', 'termination',
        'entire agreement', 'amendment', 'notice', 'signature'
    ]
    
    contract_text_lower = (
        drafted_contract.preamble + 
        drafted_contract.terms_and_conditions + 
        drafted_contract.signature_block
    ).lower()
    
    present_clauses = sum(1 for clause in mandatory_clauses if clause in contract_text_lower)
    validation_scores['legal_completeness'] = present_clauses / len(mandatory_clauses)
    
    # 2. Financial Soundness
    financial_checks = [
        'payment' in contract_text_lower,
        'currency' in contract_text_lower,
        str(context['pricing_terms']['total_value']) in drafted_contract.terms_and_conditions or
        str(context['pricing_terms']['unit_price']) in drafted_contract.terms_and_conditions,
        'late payment' in contract_text_lower or 'interest' in contract_text_lower,
        'milestone' in contract_text_lower or 'installment' in contract_text_lower
    ]
    validation_scores['financial_soundness'] = sum(financial_checks) / len(financial_checks)
    
    # 3. Risk Coverage
    risk_checks = [
        'inspection' in contract_text_lower,
        'penalty' in contract_text_lower or 'liquidated damages' in contract_text_lower,
        'insurance' in contract_text_lower,
        'indemnity' in contract_text_lower or 'indemnification' in contract_text_lower,
        'warranty' in contract_text_lower,
        len(risk_assessment.recommended_clauses) > 0
    ]
    
    # Check if high-risk clauses present for high-risk contracts
    if risk_assessment.overall_risk_level in ['high', 'critical']:
        risk_checks.extend([
            'bank guarantee' in contract_text_lower or 'performance bond' in contract_text_lower,
            'third party' in contract_text_lower and 'inspection' in contract_text_lower
        ])
    
    validation_scores['risk_coverage'] = sum(risk_checks) / len(risk_checks)
    
    # 4. Compliance Adequacy
    compliance_checks = [
        'certification' in contract_text_lower,
        'standard' in contract_text_lower,
        'test' in contract_text_lower or 'testing' in contract_text_lower,
        'inspection' in contract_text_lower,
        compliance.inspection_level in contract_text_lower or 'aql' in contract_text_lower
    ]
    
    # Check for specific certifications mentioned
    for cert in compliance.required_certifications[:3]:
        if cert.lower() in contract_text_lower:
            compliance_checks.append(True)
    
    validation_scores['compliance_adequacy'] = min(1.0, sum(compliance_checks) / 5)
    
    # 5. Operational Feasibility
    operational_checks = [
        len(drafted_contract.preamble) > 200,
        len(drafted_contract.terms_and_conditions) > 2000,
        len(drafted_contract.signature_block) > 100,
        'date' in contract_text_lower,
        drafted_contract.contract_terms_summary and len(drafted_contract.contract_terms_summary) > 100
    ]
    validation_scores['operational_feasibility'] = sum(operational_checks) / len(operational_checks)
    
    # Calculate weighted overall score
    weights = {
        'legal_completeness': 0.30,
        'financial_soundness': 0.25,
        'risk_coverage': 0.20,
        'compliance_adequacy': 0.15,
        'operational_feasibility': 0.10
    }
    
    overall_score = sum(
        validation_scores[key] * weights[key] 
        for key in weights.keys()
    )
    
    validation_scores['overall_score'] = overall_score
    
    # Identify issues
    issues = []
    if validation_scores['legal_completeness'] < 0.8:
        missing = [c for c in mandatory_clauses if c not in contract_text_lower]
        issues.append(f"Missing mandatory clauses: {', '.join(missing[:3])}")
    
    if validation_scores['financial_soundness'] < 0.8:
        issues.append("Financial terms may need strengthening")
    
    if validation_scores['risk_coverage'] < 0.7:
        issues.append("Risk mitigation clauses may be insufficient for risk level")
    
    if validation_scores['compliance_adequacy'] < 0.7:
        issues.append("Compliance requirements may not be fully addressed")
    
    validation_scores['issues'] = issues
    validation_scores['is_acceptable'] = overall_score >= 0.75

    logger.info(f"Validation completed. Overall Score: {overall_score:.2%}, Issues Found: {len(issues)}")
    
    return validation_scores


# ============================================================================
# RECOMMENDATIONS GENERATION
# ============================================================================

def generate_comprehensive_recommendations(
    drafted_contract: DraftedContract,
    context: Dict[str, Any],
    risk_assessment: RiskAssessment,
    compliance: ComplianceRequirements,
    validation: Dict[str, Any]
) -> List[str]:
    """
    Generate comprehensive recommendations for next steps
    """
    
    recommendations = []
    
    # Priority 1: Critical actions
    recommendations.append("✓ Conduct comprehensive legal review with qualified counsel")
    recommendations.append("✓ Obtain internal approvals from authorized signatories")
    
    # Risk-based recommendations
    if risk_assessment.overall_risk_level in ['high', 'critical']:
        recommendations.append("⚠️ HIGH RISK: Verify bank guarantee/performance bond arrangements before execution")
        recommendations.append("⚠️ HIGH RISK: Confirm third-party inspection agency selection and engage them")
        recommendations.append("⚠️ Consider obtaining trade credit insurance for this contract")
    
    # Compliance recommendations
    if compliance.third_party_inspection_required:
        recommendations.append("✓ Engage third-party inspection agency (SGS, Bureau Veritas, etc.)")
    
    if compliance.required_certifications:
        recommendations.append(f"✓ Verify supplier's certification status: {', '.join(compliance.required_certifications[:2])}")
    
    # Validation-based recommendations
    if validation['overall_score'] < 0.85:
        recommendations.append("⚠️ Address validation issues identified before finalizing")
    
    if validation.get('issues'):
        for issue in validation['issues'][:2]:
            recommendations.append(f"⚠️ {issue}")
    
    # Negotiation-based recommendations
    negotiation_context = context.get('negotiation_context', {})
    if negotiation_context.get('negotiation_difficulty') in ['very_difficult', 'moderate']:
        recommendations.append("✓ Schedule pre-execution clarification meeting with supplier")
    
    # Financial recommendations
    if context['pricing_terms']['total_value'] > 500000:
        recommendations.append("✓ Establish escrow arrangement or structured payment release mechanism")
    
    # Operational recommendations
    recommendations.extend([
        "✓ Set up contract management system for milestone tracking",
        "✓ Assign dedicated contract manager for execution oversight",
        "✓ Schedule kickoff meeting with supplier post-execution",
        "✓ Prepare delivery and quality acceptance checklists",
        "✓ Set up automated reminders for key milestone dates"
    ])
    
    # Final recommendations
    recommendations.append("✓ Prepare contract execution ceremony/process")
    recommendations.append("✓ Plan post-execution contract monitoring and reporting framework")

    logger.info(f"Generated {len(recommendations)} recommendations for next steps.")
    
    return recommendations[:12]  # Return top 12


# ============================================================================
# SUMMARY MESSAGE GENERATION
# ============================================================================

def generate_contract_summary_message(
    contract_id: str,
    context: Dict[str, Any],
    risk_assessment: RiskAssessment,
    financial_terms: FinancialTermsDetail,
    delivery_terms: DeliveryTermsDetail,
    quality_framework: QualityAssuranceFramework,
    validation: Dict[str, Any],
    recommendations: List[str]
) -> str:
    """
    Generate comprehensive summary message for the user
    """
    
    supplier_name = context['supplier_information']['name']
    fabric_type = context['fabric_specifications']['fabric_type']
    quantity = context['fabric_specifications']['quantity']
    unit = context['fabric_specifications']['unit']
    currency = context['pricing_terms']['currency']
    total_value = context['pricing_terms']['total_value']
    
    message = f"""
**COMPREHENSIVE CONTRACT SUCCESSFULLY DRAFTED**

{'-'*70}

**CONTRACT IDENTIFICATION**
• Contract ID: {contract_id}
• Contract Type: Textile Procurement Agreement
• Status: Draft - Ready for Legal Review

{'-'*70}

**PARTIES & SCOPE**
• Buyer: {context['buyer_information']['company_name']}
• Supplier: {supplier_name}
• Product: {fabric_type}
• Quantity: {quantity:,} {unit}
• Contract Value: {currency} {total_value:,.2f}

{'-'*70}

**RISK ASSESSMENT SUMMARY**
• Risk Level: {risk_assessment.overall_risk_level.upper()}
• Risk Score: {risk_assessment.risk_score:.1f}/100
• Key Risk Factors:
{chr(10).join(f'  - {factor}' for factor in risk_assessment.risk_factors[:3])}

**Risk Mitigation Measures Applied:**
{chr(10).join(f'  ✓ {measure}' for measure in risk_assessment.mitigation_requirements[:3])}

{'-'*70}

**FINANCIAL TERMS STRUCTURE**
• Payment Milestones: {len(financial_terms.payment_milestones)} structured payments
• Advance Payment: {financial_terms.payment_milestones[0]['percentage']}% ({currency} {financial_terms.payment_milestones[0]['amount']:,.2f})
• Bank Guarantee: {'Required' if financial_terms.bank_guarantee_required else 'Not Required'}
{f"  - Guarantee Amount: {financial_terms.bank_guarantee_amount_percentage}% of contract value" if financial_terms.bank_guarantee_required else ""}
• Late Payment Interest: {financial_terms.late_payment_interest_rate}% per annum
• Retention: {financial_terms.retention_amount_percentage or 0}% for quality assurance

{'-'*70}

**DELIVERY SCHEDULE**
• Order Date: {delivery_terms.order_date}
• Production Start: {delivery_terms.production_start_date}
• Inspection Date: {delivery_terms.inspection_date}
• Expected Shipment: {delivery_terms.shipment_date}
• Expected Delivery: {delivery_terms.delivery_date}
• Incoterm: {delivery_terms.incoterm}
• Partial Shipments: {'Permitted' if delivery_terms.partial_shipment_allowed else 'Not Permitted'}
• Shipping Method: {delivery_terms.shipping_method}

{'-'*70}

**QUALITY ASSURANCE FRAMEWORK**
• AQL Level: {quality_framework.aql_level}
• Pre-production Sample: {'Required' if quality_framework.pre_production_sample_required else 'Optional'}
• In-line Inspection: {'Required' if quality_framework.in_line_inspection_required else 'Not Required'}
• Pre-shipment Inspection: {'Mandatory' if quality_framework.pre_shipment_inspection_required else 'Optional'}
{f"• Third-party Inspector: {quality_framework.third_party_inspector}" if quality_framework.third_party_inspector else ""}
• Defect Tolerance: 
  - Critical: {quality_framework.defect_tolerance['critical_defects']}%
  - Major: {quality_framework.defect_tolerance['major_defects']}%
  - Minor: {quality_framework.defect_tolerance['minor_defects']}%

{'-'*70}

**CONTRACT QUALITY VALIDATION**
• Overall Validation Score: {validation['overall_score']:.1%}
  - Legal Completeness: {validation['legal_completeness']:.1%}
  - Financial Soundness: {validation['financial_soundness']:.1%}
  - Risk Coverage: {validation['risk_coverage']:.1%}
  - Compliance Adequacy: {validation['compliance_adequacy']:.1%}
  - Operational Feasibility: {validation['operational_feasibility']:.1%}

**Status:** {'ACCEPTABLE - Ready for Review' if validation['is_acceptable'] else '⚠️ NEEDS ATTENTION'}

{f"**Issues Identified:**{chr(10)}{chr(10).join(f'  ⚠️ {issue}' for issue in validation.get('issues', []))}" if validation.get('issues') else ""}

{'-'*70}

**NEGOTIATION SUMMARY**
• Total Rounds: {context['negotiation_context']['total_rounds']}
• Negotiation Difficulty: {context['negotiation_context']['negotiation_difficulty'].title()}
• Relationship Quality: {context['negotiation_context']['relationship_quality'].title()}
• Savings Achieved: {context['pricing_terms'].get('savings_achieved', 0):.1f}% from initial quote

{'-'*70}

**CRITICAL NEXT STEPS**

{chr(10).join(f"{i+1}. {rec}" for i, rec in enumerate(recommendations[:8]))}

{'-'*70}

**LEGAL NOTICE**
This contract is a DRAFT and requires:
• Comprehensive legal review by qualified counsel
• Internal approval from authorized signatories
• Verification of all terms and conditions
• Final negotiation/clarification with supplier (if needed)

**DO NOT EXECUTE** this contract without proper legal review and approval.

{''*70}

**CONTRACT COMPONENTS READY:**
Complete Preamble with Party Details
Comprehensive Terms and Conditions
Detailed Payment Schedule
Quality Assurance Procedures
Delivery Milestones
Risk Mitigation Clauses
Dispute Resolution Framework
Force Majeure Provisions
Signature Blocks

{'-'*70}

**RECOMMENDATION:** Proceed to legal review immediately to maintain momentum.
**Timeline:** Allow 3-5 business days for legal review and revisions.

"""
    
    return message.strip()