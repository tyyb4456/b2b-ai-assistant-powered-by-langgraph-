from typing import Dict, Any, List, Optional, Tuple
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
import uuid
import logging
from state import AgentState
from models.quote_detail_model import GeneratedQuote, SupplierQuoteOption, LogisticsCost
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")

structured_model = model.with_structured_output(GeneratedQuote)

# Configuration constants
class QuoteConfig:
    """Configuration constants for quote generation"""
    MAX_SUPPLIER_OPTIONS = 6
    DEFAULT_QUOTE_VALIDITY_DAYS = 30
    DEFAULT_CURRENCY = "USD"
    MIN_QUANTITY_FOR_DISCOUNT = 50000
    LARGE_ORDER_THRESHOLD = 50000
    
    # Weight factors for supplier scoring
    SCORING_WEIGHTS = {
        'price': 0.30,
        'reliability': 0.25,
        'lead_time': 0.20,
        'certifications': 0.15,
        'location': 0.10
    }
    
    # Fabric weight ranges (kg per meter) - (min, max)
    FABRIC_WEIGHTS = {
        'cotton': (0.12, 0.18),
        'silk': (0.06, 0.10),
        'denim': (0.40, 0.50),
        'linen': (0.15, 0.21),
        'polyester': (0.10, 0.14),
        'wool': (0.22, 0.28),
        'viscose': (0.11, 0.16),
        'rayon': (0.10, 0.15),
        'canvas': (0.20, 0.30),
        'poplin': (0.08, 0.12),
        'default': (0.15, 0.25)
    }
    
    # Shipping rates per kg (USD) - (origin, destination): rate
    SHIPPING_RATES = {
        ('China', 'Bangladesh'): 0.85,
        ('India', 'Bangladesh'): 0.45,
        ('Pakistan', 'Bangladesh'): 0.35,
        ('Turkey', 'Bangladesh'): 1.20,
        ('Vietnam', 'Bangladesh'): 0.75,
        ('China', 'USA'): 1.50,
        ('India', 'USA'): 1.30,
        ('Pakistan', 'USA'): 1.25,
        ('Turkey', 'USA'): 1.40,
        ('default_regional',): 0.60,
        ('default_international',): 1.00
    }
    
    # Customs duty rates by fabric type
    CUSTOMS_RATES = {
        'organic': 0.08,
        'synthetic': 0.12,
        'natural': 0.10,
        'blended': 0.11,
        'default': 0.12
    }


def validate_input_state(state: AgentState) -> Tuple[bool, Optional[str]]:
    """
    Validate that the state has all required fields for quote generation
    
    Args:
        state: Current agent state
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = {
        'extracted_parameters': 'Missing extracted parameters',
        'top_suppliers': 'No suppliers available'
    }
    
    for field, error_msg in required_fields.items():
        if not state.get(field):
            logger.warning(f"Validation failed: {error_msg}")
            return False, error_msg
    
    # Validate top_suppliers is not empty
    if not state.get('top_suppliers'):
        return False, "Supplier list is empty"
    
    # Validate extracted_parameters has required sub-fields
    params = state.get('extracted_parameters', {})
    if not params.get('fabric_details'):
        return False, "Missing fabric details in parameters"
    
    return True, None


def calculate_logistics_costs(
    supplier: Dict, 
    destination: str, 
    quantity: float, 
    fabric_type: str
) -> LogisticsCost:
    """
    Calculate comprehensive logistics costs for a supplier with improved accuracy
    
    Args:
        supplier: Supplier dictionary with location and other details
        destination: Destination country/region
        quantity: Order quantity
        fabric_type: Type of fabric for customs classification
    
    Returns:
        LogisticsCost: Detailed breakdown of logistics expenses
    
    Raises:
        ValueError: If quantity is invalid
    """
    if quantity <= 0:
        raise ValueError(f"Invalid quantity: {quantity}. Must be positive.")
    
    try:
        supplier_country = supplier.get('location', 'Unknown')
        
        # Get fabric weight range and use average
        fabric_key = next(
            (key for key in QuoteConfig.FABRIC_WEIGHTS.keys() if key in fabric_type.lower()), 
            'default'
        )
        min_weight, max_weight = QuoteConfig.FABRIC_WEIGHTS[fabric_key]
        avg_weight_per_unit = (min_weight + max_weight) / 2
        total_weight_kg = quantity * avg_weight_per_unit
        
        logger.debug(f"Calculated weight: {total_weight_kg:.2f}kg for {quantity} units of {fabric_type}")
        
        # Get shipping rate
        route_key = (supplier_country, destination) if destination else None
        rate_per_kg = get_shipping_rate(route_key, supplier_country, destination)
        
        # Calculate shipping cost with volume discount for large orders
        base_shipping = total_weight_kg * rate_per_kg
        volume_discount = calculate_volume_discount(total_weight_kg)
        shipping_cost = base_shipping * (1 - volume_discount)
        
        # Calculate insurance (5% of material + shipping value)
        material_value = supplier.get('price_per_unit', 5.0) * quantity
        insurance_base = material_value + shipping_cost
        insurance_cost = insurance_base * 0.05
        
        # Calculate customs duties based on fabric type
        customs_rate = get_customs_rate(fabric_type)
        customs_duties = material_value * customs_rate
        
        # Calculate handling fees (tiered based on order size)
        handling_fees = calculate_handling_fees(quantity, total_weight_kg)
        
        # Total logistics cost
        total_logistics = shipping_cost + insurance_cost + customs_duties + handling_fees
        
        logger.info(f"Logistics calculated: Shipping=${shipping_cost:.2f}, "
                   f"Insurance=${insurance_cost:.2f}, Customs=${customs_duties:.2f}, "
                   f"Handling=${handling_fees:.2f}, Total=${total_logistics:.2f}")
        
        return LogisticsCost(
            shipping_cost=round_decimal(shipping_cost),
            insurance_cost=round_decimal(insurance_cost),
            customs_duties=round_decimal(customs_duties),
            handling_fees=round_decimal(handling_fees),
            total_logistics=round_decimal(total_logistics)
        )
        
    except Exception as e:
        logger.error(f"Error calculating logistics costs: {str(e)}")
        # Return default conservative estimate
        return LogisticsCost(
            shipping_cost=1000.0,
            insurance_cost=100.0,
            customs_duties=500.0,
            handling_fees=200.0,
            total_logistics=1800.0
        )


@lru_cache(maxsize=100)
def get_shipping_rate(route_key: Optional[Tuple[str, str]], origin: str, destination: Optional[str]) -> float:
    """
    Get shipping rate with caching for performance
    
    Args:
        route_key: Tuple of (origin, destination) or None
        origin: Origin country
        destination: Destination country or None
    
    Returns:
        float: Shipping rate per kg
    """
    if not destination:
        return QuoteConfig.SHIPPING_RATES[('default_international',)]
    
    if route_key and route_key in QuoteConfig.SHIPPING_RATES:
        return QuoteConfig.SHIPPING_RATES[route_key]
    
    # Check if both are in Asia (regional rate)
    asian_countries = ['China', 'India', 'Pakistan', 'Bangladesh', 'Vietnam', 'Thailand', 'Indonesia']
    if origin in asian_countries and destination in asian_countries:
        return QuoteConfig.SHIPPING_RATES[('default_regional',)]
    
    # International rate
    return QuoteConfig.SHIPPING_RATES[('default_international',)]


def get_customs_rate(fabric_type: str) -> float:
    """
    Determine customs duty rate based on fabric type
    
    Args:
        fabric_type: Type/description of fabric
    
    Returns:
        float: Customs duty rate (as decimal, e.g., 0.12 for 12%)
    """
    fabric_lower = fabric_type.lower()
    
    if 'organic' in fabric_lower or 'eco' in fabric_lower:
        return QuoteConfig.CUSTOMS_RATES['organic']
    elif 'polyester' in fabric_lower or 'nylon' in fabric_lower or 'synthetic' in fabric_lower:
        return QuoteConfig.CUSTOMS_RATES['synthetic']
    elif 'cotton' in fabric_lower or 'silk' in fabric_lower or 'wool' in fabric_lower:
        return QuoteConfig.CUSTOMS_RATES['natural']
    elif 'blend' in fabric_lower or 'mix' in fabric_lower:
        return QuoteConfig.CUSTOMS_RATES['blended']
    
    return QuoteConfig.CUSTOMS_RATES['default']


def calculate_volume_discount(weight_kg: float) -> float:
    """
    Calculate volume discount based on shipment weight
    
    Args:
        weight_kg: Total weight in kilograms
    
    Returns:
        float: Discount rate (e.g., 0.05 for 5% discount)
    """
    if weight_kg > 10000:
        return 0.10  # 10% discount for very large shipments
    elif weight_kg > 5000:
        return 0.07  # 7% discount
    elif weight_kg > 2000:
        return 0.05  # 5% discount
    elif weight_kg > 1000:
        return 0.03  # 3% discount
    
    return 0.0  # No discount for smaller shipments


def calculate_handling_fees(quantity: float, weight_kg: float) -> float:
    """
    Calculate handling fees based on order size and weight
    
    Args:
        quantity: Order quantity
        weight_kg: Total weight
    
    Returns:
        float: Handling fee amount
    """
    # Base fee on quantity tiers
    if quantity > 100000:
        base_fee = 800
    elif quantity > 50000:
        base_fee = 500
    elif quantity > 20000:
        base_fee = 300
    elif quantity > 5000:
        base_fee = 150
    else:
        base_fee = 75
    
    # Add weight-based fee for very heavy shipments
    if weight_kg > 5000:
        base_fee += 200
    elif weight_kg > 2000:
        base_fee += 100
    
    return float(base_fee)


def round_decimal(value: float, places: int = 2) -> float:
    """
    Round a float to specified decimal places
    
    Args:
        value: Value to round
        places: Number of decimal places
    
    Returns:
        float: Rounded value
    """
    decimal_value = Decimal(str(value))
    rounded = decimal_value.quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)
    return float(rounded)


def calculate_supplier_score(
    supplier: Dict, 
    extracted_params: Dict,
    all_suppliers: List[Dict]
) -> float:
    """
    Calculate comprehensive supplier score using multiple weighted factors
    
    Args:
        supplier: Individual supplier data
        extracted_params: Client requirements
        all_suppliers: All available suppliers for market comparison
    
    Returns:
        float: Overall score (0-100)
    """
    try:
        weights = QuoteConfig.SCORING_WEIGHTS
        
        # Use overall_score if available, otherwise calculate
        if 'overall_score' in supplier and supplier['overall_score']:
            return supplier['overall_score']
        
        # 1. Price Score (30%)
        prices = [s.get('price_per_unit', 0) for s in all_suppliers if s.get('price_per_unit', 0) > 0]
        avg_market_price = sum(prices) / len(prices) if prices else supplier.get('price_per_unit', 5.0)
        supplier_price = supplier.get('price_per_unit', avg_market_price)
        
        if avg_market_price > 0:
            price_ratio = supplier_price / avg_market_price
            price_score = max(0, min(100, 100 - ((price_ratio - 1) * 100)))
        else:
            price_score = 50.0
        
        # 2. Reliability Score (25%)
        reliability_score = supplier.get('reputation_score', 5.0) * 10
        
        # 3. Lead Time Score (20%)
        target_lead_time = extracted_params.get('logistics_details', {}).get('timeline_days', 30)
        supplier_lead_time = supplier.get('lead_time_days', 30)
        
        if target_lead_time and target_lead_time > 0:
            lead_time_ratio = supplier_lead_time / target_lead_time
            lead_time_score = max(0, min(100, 100 - ((lead_time_ratio - 1) * 50)))
        else:
            lead_time_score = 50.0
        
        # 4. Certification Score (15%)
        required_certs = set(extracted_params.get('fabric_details', {}).get('certifications', []))
        supplier_certs = set(supplier.get('certifications', []))
        
        if required_certs:
            matched_certs = len(required_certs & supplier_certs)
            cert_score = (matched_certs / len(required_certs)) * 100
        else:
            cert_score = min(100, len(supplier_certs) * 20)
        
        # 5. Location Score (10%)
        location_score = 50.0  # Default neutral score
        
        # Calculate weighted overall score
        overall_score = (
            price_score * weights['price'] +
            reliability_score * weights['reliability'] +
            lead_time_score * weights['lead_time'] +
            cert_score * weights['certifications'] +
            location_score * weights['location']
        )
        
        return round_decimal(overall_score)
        
    except Exception as e:
        logger.error(f"Error calculating supplier score: {str(e)}")
        return 50.0


def analyze_supplier_advantages_risks(
    supplier: Dict,
    all_suppliers: List[Dict],
    extracted_params: Dict
) -> Tuple[List[str], List[str]]:
    """
    Analyze supplier to identify key advantages and potential risks
    
    Args:
        supplier: Supplier data
        all_suppliers: All suppliers for comparison
        extracted_params: Client requirements
    
    Returns:
        Tuple of (advantages, risks)
    """
    advantages = []
    risks = []
    
    # Get comparison metrics
    prices = [s.get('price_per_unit', 0) for s in all_suppliers if s.get('price_per_unit', 0) > 0]
    min_price = min(prices) if prices else 0
    avg_price = sum(prices) / len(prices) if prices else 0
    
    lead_times = [s.get('lead_time_days', 30) for s in all_suppliers]
    min_lead_time = min(lead_times) if lead_times else 30
    avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 30
    
    # Analyze advantages
    if supplier.get('reputation_score', 5) >= 8:
        advantages.append("✓ Excellent reliability track record (8+/10)")
    elif supplier.get('reputation_score', 5) >= 7:
        advantages.append("✓ Good reliability score")
    
    supplier_lead_time = supplier.get('lead_time_days', 30)
    if supplier_lead_time <= min_lead_time * 1.1:
        advantages.append(f"✓ Fast delivery capability ({supplier_lead_time} days)")
    elif supplier_lead_time <= avg_lead_time:
        advantages.append("✓ Competitive lead time")
    
    supplier_price = supplier.get('price_per_unit', avg_price)
    if avg_price > 0 and supplier_price <= min_price * 1.05:
        advantages.append(f"✓ Most competitive pricing (${supplier_price:.2f}/unit)")
    elif avg_price > 0 and supplier_price <= avg_price:
        advantages.append("✓ Below market average pricing")
    
    # Check certifications
    supplier_certs = supplier.get('certifications', [])
    if 'GOTS' in supplier_certs or 'organic' in str(supplier_certs).lower():
        advantages.append("✓ Organic/GOTS certification available")
    if 'OEKO-TEX' in supplier_certs:
        advantages.append("✓ OEKO-TEX certified")
    if len(supplier_certs) >= 3:
        advantages.append(f"✓ Multiple certifications ({len(supplier_certs)})")
    
    # Analyze risks
    if supplier.get('reputation_score', 5) < 7:
        risks.append("⚠ Lower reliability score - recommend closer monitoring")
    
    if supplier_lead_time > avg_lead_time * 1.3:
        risks.append(f"⚠ Extended lead time ({supplier_lead_time} days) may impact timeline")
    
    min_order = supplier.get('minimum_order_qty', 0)
    requested_qty = extracted_params.get('fabric_details', {}).get('quantity', 0)
    if min_order > requested_qty:
        risks.append(f"⚠ MOQ ({min_order:,}) exceeds requested quantity")
    
    if avg_price > 0 and supplier_price > avg_price * 1.2:
        risks.append("⚠ Pricing above market average")
    
    # Default messages if none found
    if not advantages:
        advantages.append("Competitive option for consideration")
    if not risks:
        risks.append("Standard supplier risks apply - due diligence recommended")
    
    return advantages, risks


def create_quote_generation_prompt() -> ChatPromptTemplate:
    """Create the enhanced prompt template for quote generation"""
    
    system_prompt = """You are an expert B2B textile procurement specialist with deep market knowledge.

Your role is to generate professional, strategic quotes that demonstrate value beyond just price comparison.

**Core Objectives:**
1. Present supplier options as strategic business choices
2. Provide actionable market intelligence and insights
3. Give clear, confident recommendations with reasoning
4. Highlight risks honestly and suggest mitigation strategies
5. Position yourself as a trusted advisor

**Tone & Style:**
- Professional but approachable and conversational
- Confident and knowledgeable, not salesy
- Focus on value, quality, and strategic fit
- Acknowledge trade-offs transparently
- Use business language that resonates with procurement professionals

**Critical Elements to Include:**
✓ Clear total landed costs (material + all logistics)
✓ Comparative analysis of lead times and business impact
✓ Reliability assessment with context
✓ Certification compliance status
✓ Payment term recommendations
✓ Risk factors and mitigation strategies
✓ Negotiation leverage points"""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Generate a comprehensive B2B textile procurement quote:

**CLIENT REQUEST:**
- Fabric Type: {fabric_type}
- Quantity: {quantity} {unit}
- Quality Requirements: {quality_specs}
- Certifications Needed: {certifications}
- Destination: {destination}
- Timeline Required: {timeline}
- Urgency Level: {urgency}

**AVAILABLE SUPPLIER OPTIONS:**
{supplier_options}

**MARKET INTELLIGENCE:**
{market_insights}

**TASK:**
Create a strategic quote analyzing the suppliers provided.""")
    ])


# Initialize prompt template
quote_prompt = create_quote_generation_prompt()


def prepare_supplier_options_text(
    suppliers: List[Dict],
    logistics_costs: Dict[str, LogisticsCost]
) -> str:
    """
    Format supplier data for prompt inclusion with enhanced details
    """
    options_text = []
    
    for i, supplier in enumerate(suppliers[:QuoteConfig.MAX_SUPPLIER_OPTIONS], 1):
        supplier_id = supplier.get('supplier_id', f'supplier_{i}')
        logistics = logistics_costs.get(supplier_id, LogisticsCost(
            shipping_cost=0, insurance_cost=0, customs_duties=0, handling_fees=0, total_logistics=0
        ))
        
        unit_price = supplier.get('price_per_unit', 5.0)
        quantity = supplier.get('quantity', 1000)
        material_cost = unit_price * quantity
        total_cost = material_cost + logistics.total_logistics
        
        option_text = f"""
**Option {i}: {supplier.get('name', 'Unknown Supplier')}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Location: {supplier.get('location', 'Unknown')}
Unit Price: ${unit_price:.2f}
Material Cost: ${material_cost:,.2f}

Logistics Breakdown:
  - Shipping: ${logistics.shipping_cost:,.2f}
  - Insurance: ${logistics.insurance_cost:,.2f}
  - Customs: ${logistics.customs_duties:,.2f}
  - Handling: ${logistics.handling_fees:,.2f}
  - Subtotal: ${logistics.total_logistics:,.2f}

**Total Landed Cost: ${total_cost:,.2f}**

Lead Time: {supplier.get('lead_time_days', 'N/A')} days
Reputation Score: {supplier.get('reputation_score', 'N/A')}/10
Overall Score: {supplier.get('overall_score', 'N/A')}/100

Specialties: {', '.join(supplier.get('specialties', ['N/A']))}
Certifications: {', '.join(supplier.get('certifications', ['None']))}
MOQ: {supplier.get('minimum_order_qty', 'N/A')} units
"""
        options_text.append(option_text)
    
    return "\n".join(options_text)


def generate_terms_and_conditions() -> str:
    """Generate standard terms and conditions for the quote"""
    
    return """
**TERMS AND CONDITIONS:**

1. **Quote Validity:** This quotation is valid for 30 days from the date of issue. Prices are subject to change after expiry.

2. **Payment Terms:** Standard terms are 30% advance payment, 70% against copy of shipping documents. Alternative terms negotiable based on order value and relationship.

3. **Delivery Terms:** FOB supplier's port unless otherwise specified. Other Incoterms (CIF, CNF, DDP) available upon request.

4. **Quality Assurance:** 
   - Pre-shipment inspection recommended for orders exceeding $50,000
   - Third-party inspection acceptable at buyer's cost
   - Lab test reports provided for material quality verification

5. **Lead Time:** Lead times are estimated based on current production schedules and subject to confirmation upon order placement.

6. **Force Majeure:** Standard force majeure clauses apply for delays caused by circumstances beyond reasonable control.

7. **Currency:** All prices quoted in USD unless otherwise specified. Currency fluctuation risk to be managed per agreed terms.

8. **Minimum Order Quantity:** Subject to individual supplier's MOQ requirements as specified in each option.

9. **Pricing:** Prices are based on current market conditions and supplier availability. Final pricing subject to confirmation at time of order placement.

10. **Cancellation Policy:** Cancellations must be notified in writing. Advance payments may be subject to cancellation fees as per supplier policies.

11. **Dispute Resolution:** Any disputes arising from this quotation shall be resolved through negotiation or arbitration as per agreed jurisdiction.

**NOTE:** This quote represents our professional analysis of your requirements. We recommend reviewing all terms with your procurement team before proceeding.
"""


def calculate_estimated_savings(supplier_options: List[SupplierQuoteOption]) -> Optional[float]:
    """Calculate potential savings vs highest cost option"""
    if len(supplier_options) < 2:
        return None
    
    costs = [option.total_landed_cost for option in supplier_options]
    max_cost = max(costs)
    min_cost = min(costs)
    
    if max_cost <= 0:
        return None
    
    savings_amount = max_cost - min_cost
    savings_percentage = (savings_amount / max_cost) * 100
    
    return round_decimal(savings_percentage, 1)


def create_error_response(error_message: str, error_type: str = "generation_error") -> dict:
    """Create standardized error response"""
    return {
        "error": error_message,
        "error_type": error_type,
        "messages": [f"I encountered an issue: {error_message}"],
        "next_step": "handle_error",
        "status": "error",
        "timestamp": datetime.now().isoformat()
    }


def generate_quote(state: AgentState) -> dict:
    """
    Node: generate_quote - Professional quote generation with market intelligence
    
    Args:
        state: Current agent state with supplier results and extracted parameters
    
    Returns:
        dict: State updates with generated quote document and routing information
    """
    try:
        logger.info("=== Starting Quote Generation ===")
        
        # Step 1: Validate input state
        is_valid, error_msg = validate_input_state(state)
        if not is_valid:
            logger.error(f"Input validation failed: {error_msg}")
            return create_error_response(error_msg, "validation_error")
        
        # Step 2: Extract data from state
        extracted_params = state.get('extracted_parameters', {})
        top_suppliers = state.get('top_suppliers', [])

        
        # Get market insights from supplier search or generate
        supplier_search_result = state.get('supplier_search_result')
        if supplier_search_result and isinstance(supplier_search_result, dict):
            market_insights_raw = supplier_search_result.get('market_insights', '')
        else:
            market_insights_raw = ''
        
        logger.info(f"Processing {len(top_suppliers)} suppliers for quote generation")
        
        # Extract key parameters
        fabric_details = extracted_params.get('fabric_details', {})
        logistics_details = extracted_params.get('logistics_details', {})
        
        fabric_type = fabric_details.get('type', 'fabric')
        quantity = fabric_details.get('quantity', 1000)
        unit = fabric_details.get('unit', 'meters')
        quality_specs = fabric_details.get('quality_specs', [])
        certifications = fabric_details.get('certifications', [])
        destination = logistics_details.get('destination', 'Unknown')
        timeline = logistics_details.get('timeline', 'Standard')
        urgency = extracted_params.get('urgency_level', 'medium')
        
        # Step 3: Calculate logistics costs for each supplier
        logger.info("Calculating logistics costs for suppliers...")
        logistics_costs = {}
        
        for supplier in top_suppliers[:QuoteConfig.MAX_SUPPLIER_OPTIONS]:
            supplier_id = supplier.get('supplier_id', str(uuid.uuid4()))
            try:
                # Add quantity to supplier dict for logistics calculation
                supplier['quantity'] = quantity
                logistics_costs[supplier_id] = calculate_logistics_costs(
                    supplier, destination, quantity, fabric_type
                )
            except Exception as e:
                logger.warning(f"Error calculating logistics for {supplier.get('name')}: {e}")
                logistics_costs[supplier_id] = LogisticsCost(
                    shipping_cost=1000.0,
                    insurance_cost=100.0,
                    customs_duties=500.0,
                    handling_fees=200.0,
                    total_logistics=1800.0
                )
        
        # Step 4: Score suppliers and create supplier quote options
        logger.info("Scoring suppliers and generating options...")
        supplier_options = []
        
        for supplier in top_suppliers[:QuoteConfig.MAX_SUPPLIER_OPTIONS]:
            supplier_id = supplier.get('supplier_id', str(uuid.uuid4()))
            logistics = logistics_costs.get(supplier_id)
            
            if not logistics:
                logger.warning(f"No logistics data for supplier {supplier_id}, skipping")
                continue
            
            # Calculate costs
            unit_price = supplier.get('price_per_unit', 5.0)
            material_cost = unit_price * quantity
            total_landed_cost = material_cost + logistics.total_logistics
            
            # Calculate comprehensive score
            overall_score = calculate_supplier_score(supplier, extracted_params, top_suppliers)
            
            # Analyze advantages and risks
            advantages, risks = analyze_supplier_advantages_risks(
                supplier, top_suppliers, extracted_params
            )
            
            supplier_option = SupplierQuoteOption(
                supplier_name=supplier.get('name', 'Unknown Supplier'),
                supplier_location=supplier.get('location', 'Unknown'),
                unit_price=round_decimal(unit_price),
                material_cost=round_decimal(material_cost),
                logistics_cost=logistics,
                total_landed_cost=round_decimal(total_landed_cost),
                lead_time_days=supplier.get('lead_time_days', 30),
                reliability_score=supplier.get('reputation_score', 5.0),
                overall_score=overall_score,
                key_advantages=advantages,
                potential_risks=risks
            )
            supplier_options.append(supplier_option)
        
        if not supplier_options:
            logger.error("No valid supplier options generated")
            return create_error_response("No suitable suppliers found", "no_suppliers")
        
        # Sort by overall score (descending)
        supplier_options.sort(key=lambda x: x.overall_score, reverse=True)
        logger.info(f"Generated {len(supplier_options)} supplier options")
        
        # Step 5: Prepare data for LLM prompt
        logger.info("Preparing LLM prompt for quote generation...")
        supplier_options_text = prepare_supplier_options_text(top_suppliers, logistics_costs)
        
        formatted_prompt = quote_prompt.invoke({
            "fabric_type": fabric_type,
            "quantity": f"{quantity:,.0f}",
            "unit": unit,
            "quality_specs": ", ".join(quality_specs) if quality_specs else "Standard specifications",
            "certifications": ", ".join(certifications) if certifications else "No specific certifications required",
            "destination": destination,
            "timeline": timeline,
            "urgency": urgency.upper(),
            "supplier_options": supplier_options_text,
            "market_insights": market_insights_raw or "Market data being analyzed"
        })
        
        # Step 6: Generate structured quote using LLM
        logger.info("Invoking LLM for quote generation...")
        quote_result: GeneratedQuote = structured_model.invoke(formatted_prompt)
        
        # Step 7: Override/enrich LLM output with our calculated data
        quote_result.supplier_options = supplier_options
        quote_result.quote_id = f"QT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        quote_result.total_options_count = len(supplier_options)
        quote_result.estimated_savings = calculate_estimated_savings(supplier_options)
        quote_result.terms_and_conditions = generate_terms_and_conditions()
        
        # Step 8: Validate generated quote
        if not validate_quote_data(quote_result):
            logger.error("Generated quote failed validation")
            return create_error_response("Quote validation failed", "validation_error")
        
        # Step 9: Generate quote document (markdown format)
        logger.info("Generating quote document...")
        quote_document = generate_quote_document(quote_result, extracted_params)
        
        # Step 10: Generate quote summary
        quote_summary = get_quote_summary(quote_result)
        
        # Step 11: Create assistant response message
        best_supplier = supplier_options[0] if supplier_options else None
        
        if best_supplier:
            savings_text = ""
            if quote_result.estimated_savings:
                savings_text = f"\n💰 Potential Savings: Up to {quote_result.estimated_savings}% by choosing optimal supplier"
            
            assistant_message = f"""✅ **Quote Generated Successfully!**

**Quote ID:** `{quote_result.quote_id}`

**Recommended Option:**
- Supplier: **{best_supplier.supplier_name}** ({best_supplier.supplier_location})
- Total Landed Cost: **${best_supplier.total_landed_cost:,.2f}**
- Lead Time: {best_supplier.lead_time_days} days
- Reliability Score: {best_supplier.reliability_score}/10
- Overall Score: {best_supplier.overall_score:.1f}/100{savings_text}

**Key Insight:**
{quote_result.strategic_analysis.recommendation_reasoning[:200]}...

📊 Complete quote with {len(supplier_options)} supplier options is ready for review."""
        else:
            assistant_message = "⚠️ Quote generated but no suppliers fully meet all requirements. Please review options."
        
        logger.info(f"Quote {quote_result.quote_id} generated successfully")
        
        # Step 12: Return comprehensive state updates
        return {
            "generated_quote": quote_result.model_dump(),
            "quote_document": quote_document,
            "quote_id": quote_result.quote_id,
            "quote_summary": quote_summary,
            "supplier_options": [option.model_dump() for option in supplier_options],
            "estimated_savings": quote_result.estimated_savings,
            "messages": [assistant_message],
            "next_step": "send_output_to_user",
            "status": "quote_generated",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.exception(f"Critical error in quote generation: {str(e)}")
        return create_error_response(
            f"An unexpected error occurred during quote generation: {str(e)}",
            "critical_error"
        )


def generate_quote_document(quote: GeneratedQuote, extracted_params: Dict) -> str:
    """Generate comprehensive formatted quote document in markdown"""
    try:
        fabric_details = extracted_params.get('fabric_details', {})
        logistics_details = extracted_params.get('logistics_details', {})
        
        # Calculate validity date
        validity_date = (quote.quote_date + timedelta(days=quote.validity_days)).strftime("%B %d, %Y")
        issue_date = quote.quote_date.strftime("%B %d, %Y")
        
        document = f"""
# 📋 TEXTILE PROCUREMENT QUOTATION

---

**Quote Reference:** `{quote.quote_id}`  
**Issue Date:** {issue_date}  
**Valid Until:** ⏰ {validity_date}  
**Status:** Active

---

## 🎯 CLIENT REQUIREMENTS SUMMARY

{quote.client_summary}

**Detailed Specifications:**

| Parameter | Requirement |
|-----------|-------------|
| **Fabric Type** | {fabric_details.get('type', 'Not specified')} |
| **Order Quantity** | {fabric_details.get('quantity', 0):,.0f} {fabric_details.get('unit', 'units')} |
| **Quality Standards** | {', '.join(fabric_details.get('quality_specs', [])) or 'Standard quality'} |
| **Certifications** | {', '.join(fabric_details.get('certifications', [])) or 'None specified'} |
| **Delivery Destination** | {logistics_details.get('destination', 'Not specified')} |
| **Timeline Requirement** | {logistics_details.get('timeline', 'Standard')} |
| **Urgency Level** | {extracted_params.get('urgency_level', 'Medium').upper()} |

---

## 💰 SUPPLIER OPTIONS & PRICING ANALYSIS

We have evaluated **{quote.total_options_count} supplier options** based on comprehensive criteria including pricing, reliability, lead time, certifications, and logistics efficiency.

"""
        
        # Add quick comparison table
        document += create_comparison_table(quote.supplier_options)
        
        # Add detailed supplier options
        for i, option in enumerate(quote.supplier_options, 1):
            document += create_supplier_card(i, option)
        
        # Add strategic analysis
        document += f"""
---

## 🎯 STRATEGIC ANALYSIS & RECOMMENDATIONS

### 🏆 Our Top Recommendation: {quote.strategic_analysis.recommended_supplier}

{quote.strategic_analysis.recommendation_reasoning}

---

### 📈 Market Assessment

{quote.strategic_analysis.market_assessment}

---

### ⚠️ Risk Factors & Mitigation Strategies

"""
        
        for i, risk in enumerate(quote.strategic_analysis.risk_factors, 1):
            document += f"{i}. {risk}\n"
        
        document += """
---

### 💡 Negotiation Opportunities

Based on our market analysis, here are potential areas for negotiation:

"""
        
        for i, opportunity in enumerate(quote.strategic_analysis.negotiation_opportunities, 1):
            document += f"{i}. {opportunity}\n"
        
        # Add estimated savings section if applicable
        if quote.estimated_savings:
            document += f"""
---

### 💰 Potential Cost Savings

By selecting our recommended option over the highest-cost alternative, you could achieve savings of up to **{quote.estimated_savings}%**.

"""
        
        # Add alternative strategies if available
        if quote.strategic_analysis.alternative_strategies:
            document += """
---

### 🔄 Alternative Procurement Strategies

Consider these alternative approaches based on your specific priorities:

"""
            for i, strategy in enumerate(quote.strategic_analysis.alternative_strategies, 1):
                document += f"{i}. {strategy}\n"
        
        # Add terms and conditions
        document += f"""
---

## 📜 TERMS AND CONDITIONS

{quote.terms_and_conditions}

---

## 📞 Next Steps

**Ready to Proceed?**

1. Review the supplier options and our recommendations
2. Discuss any questions or concerns with our team
3. Confirm your preferred supplier and quantities
4. We'll coordinate with the supplier and manage the procurement process
5. Receive regular updates throughout production and shipping

---

*This quotation is generated using AI-powered market analysis combined with real-time supplier data.*  
*All pricing and terms are subject to final confirmation with suppliers upon order placement.*  
*Quote Reference: {quote.quote_id} | Generated: {issue_date}*
"""
        
        logger.info(f"Quote document generated successfully for {quote.quote_id}")
        return document
        
    except Exception as e:
        logger.error(f"Error generating quote document: {str(e)}")
        return f"# Quote Generation Error\n\nUnable to generate full quote document: {str(e)}"


def create_comparison_table(options: List[SupplierQuoteOption]) -> str:
    """Create a quick comparison table for all supplier options"""
    table = """
### 📊 Quick Comparison Table

| Rank | Supplier | Location | Total Cost | Material | Logistics | Lead Time | Reliability | Score |
|------|----------|----------|------------|----------|-----------|-----------|-------------|-------|
"""
    
    for i, option in enumerate(options, 1):
        rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        
        table += (
            f"| {rank_emoji} | **{option.supplier_name}** | {option.supplier_location} | "
            f"**${option.total_landed_cost:,.2f}** | ${option.material_cost:,.2f} | "
            f"${option.logistics_cost.total_logistics:,.2f} | {option.lead_time_days}d | "
            f"{option.reliability_score}/10 | {option.overall_score:.1f}/100 |\n"
        )
    
    table += "\n"
    return table


def create_supplier_card(rank: int, option: SupplierQuoteOption) -> str:
    """Create detailed supplier card with full information"""
    rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "📊"
    
    card = f"""
---

### {rank_emoji} Option {rank}: {option.supplier_name}

**Location:** {option.supplier_location} | **Overall Score:** {option.overall_score:.1f}/100

#### 💵 Cost Breakdown

| Component | Amount (USD) |
|-----------|--------------|
| **Material Cost** | ${option.material_cost:,.2f} |
| Unit Price: ${option.unit_price}/unit | |
| | |
| **Logistics Costs:** | |
| ├─ Shipping & Freight | ${option.logistics_cost.shipping_cost:,.2f} |
| ├─ Insurance | ${option.logistics_cost.insurance_cost:,.2f} |
| ├─ Customs & Duties | ${option.logistics_cost.customs_duties:,.2f} |
| └─ Handling Fees | ${option.logistics_cost.handling_fees:,.2f} |
| **Logistics Subtotal** | **${option.logistics_cost.total_logistics:,.2f}** |
| | |
| **TOTAL LANDED COST** | **${option.total_landed_cost:,.2f}** |

#### 📅 Timeline & Reliability

- **Lead Time:** {option.lead_time_days} days from order confirmation
- **Reliability Score:** {option.reliability_score}/10 ({"Excellent" if option.reliability_score >= 8 else "Good" if option.reliability_score >= 7 else "Moderate" if option.reliability_score >= 6 else "Fair"})

#### ✅ Key Advantages

"""
    
    for advantage in option.key_advantages:
        card += f"- {advantage}\n"
    
    card += "\n#### ⚠️ Considerations & Risk Factors\n\n"
    
    for risk in option.potential_risks:
        card += f"- {risk}\n"
    
    card += "\n"
    
    return card


def validate_quote_data(quote: GeneratedQuote) -> bool:
    """Validate the generated quote for completeness and data integrity"""
    try:
        # Check if we have supplier options
        if not quote.supplier_options or len(quote.supplier_options) == 0:
            logger.error("Validation failed: No supplier options")
            return False
        
        # Validate each supplier option
        for i, option in enumerate(quote.supplier_options):
            if option.total_landed_cost <= 0:
                logger.error(f"Validation failed: Invalid cost for option {i+1}")
                return False
            
            if option.lead_time_days <= 0:
                logger.error(f"Validation failed: Invalid lead time for option {i+1}")
                return False
            
            if not option.supplier_name or option.supplier_name.strip() == "":
                logger.error(f"Validation failed: Empty supplier name for option {i+1}")
                return False
        
        # Check if strategic analysis is present
        if not quote.strategic_analysis.recommended_supplier:
            logger.error("Validation failed: No recommended supplier")
            return False
        
        if not quote.strategic_analysis.recommendation_reasoning:
            logger.error("Validation failed: No recommendation reasoning")
            return False
        
        logger.info(f"Quote validation passed for {quote.quote_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error during quote validation: {str(e)}")
        return False


def get_quote_summary(quote: GeneratedQuote) -> Dict[str, Any]:
    """Generate a concise summary of the quote for quick reference"""
    if not quote.supplier_options:
        return {"error": "No supplier options available"}
    
    best_option = quote.supplier_options[0]
    
    # Calculate cost range
    costs = [opt.total_landed_cost for opt in quote.supplier_options]
    min_cost = min(costs)
    max_cost = max(costs)
    
    # Calculate lead time range
    lead_times = [opt.lead_time_days for opt in quote.supplier_options]
    min_lead_time = min(lead_times)
    max_lead_time = max(lead_times)
    
    return {
        "quote_id": quote.quote_id,
        "quote_date": quote.quote_date.isoformat(),
        "validity_date": (quote.quote_date + timedelta(days=quote.validity_days)).isoformat(),
        "total_options": len(quote.supplier_options),
        "recommended_supplier": {
            "name": best_option.supplier_name,
            "location": best_option.supplier_location,
            "total_cost": best_option.total_landed_cost,
            "lead_time_days": best_option.lead_time_days,
            "reliability_score": best_option.reliability_score,
            "overall_score": best_option.overall_score
        },
        "cost_range": {
            "min": min_cost,
            "max": max_cost,
            "variance_percentage": round_decimal(((max_cost - min_cost) / max_cost * 100) if max_cost > 0 else 0, 1)
        },
        "lead_time_range": {
            "min_days": min_lead_time,
            "max_days": max_lead_time
        },
        "estimated_savings_percentage": quote.estimated_savings,
        "confidence_level": "high" if len(quote.supplier_options) >= 3 else "medium" if len(quote.supplier_options) >= 2 else "low",
        "status": "active"
    }