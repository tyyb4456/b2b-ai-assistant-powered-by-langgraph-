from typing import Dict, Any, List, Optional, Tuple
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
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
    
    # Default values for missing data
    DEFAULT_UNIT_PRICE = 5.0
    DEFAULT_LEAD_TIME = 30
    DEFAULT_REPUTATION_SCORE = 5.0
    DEFAULT_QUANTITY = 1000
    DEFAULT_DESTINATION = "Unknown"
    
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


def safe_get_value(obj, key, default=None):
    """
    Safely get value from dict or object attribute
    
    Args:
        obj: Dictionary or object
        key: Key or attribute name
        default: Default value if not found
    
    Returns:
        Value or default
    """
    if obj is None:
        return default
    
    try:
        if isinstance(obj, dict):
            return obj.get(key, default)
        elif hasattr(obj, key):
            return getattr(obj, key, default)
        else:
            return default
    except Exception:
        return default


def safe_float(value, default=0.0):
    """
    Safely convert to float
    
    Args:
        value: Value to convert
        default: Default if conversion fails
    
    Returns:
        Float value or default
    """
    if value is None:
        return default
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """
    Safely convert to int
    
    Args:
        value: Value to convert
        default: Default if conversion fails
    
    Returns:
        Int value or default
    """
    if value is None:
        return default
    
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def validate_input_state(state: AgentState) -> Tuple[bool, Optional[str]]:
    """
    Validate that the state has all required fields for quote generation
    
    Args:
        state: Current agent state
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check state is not None
        if state is None:
            return False, "State is None"
        
        # Check extracted_parameters
        extracted_params = state.get('extracted_parameters')
        if not extracted_params:
            logger.warning("Missing extracted parameters")
            return False, "Missing extracted parameters"
        
        # Check top_suppliers
        top_suppliers = state.get('top_suppliers')
        if not top_suppliers:
            logger.warning("No suppliers available")
            return False, "No suppliers available"
        
        if not isinstance(top_suppliers, list) or len(top_suppliers) == 0:
            logger.warning("Supplier list is empty")
            return False, "Supplier list is empty"
        
        # Check fabric_details exists (can be empty dict)
        params_dict = extracted_params if isinstance(extracted_params, dict) else {}
        fabric_details = safe_get_value(params_dict, 'fabric_details')
        
        if fabric_details is None:
            logger.warning("Missing fabric details in parameters")
            return False, "Missing fabric details in parameters"
        
        logger.info("Input state validation passed")
        return True, None
        
    except Exception as e:
        logger.error(f"Error during validation: {str(e)}")
        return False, f"Validation error: {str(e)}"


def calculate_logistics_costs(
    supplier: Dict, 
    destination: str, 
    quantity: float, 
    fabric_type: str
) -> LogisticsCost:
    """
    Calculate comprehensive logistics costs for a supplier with safety checks
    
    Args:
        supplier: Supplier dictionary with location and other details
        destination: Destination country/region
        quantity: Order quantity
        fabric_type: Type of fabric for customs classification
    
    Returns:
        LogisticsCost: Detailed breakdown of logistics expenses
    """
    try:
        # Safety check: validate inputs
        if supplier is None:
            logger.warning("Supplier is None, using default logistics costs")
            return get_default_logistics_cost()
        
        if quantity is None or quantity <= 0:
            logger.warning(f"Invalid quantity: {quantity}, using default")
            quantity = QuoteConfig.DEFAULT_QUANTITY
        
        quantity = safe_float(quantity, QuoteConfig.DEFAULT_QUANTITY)
        
        if fabric_type is None or fabric_type == "":
            fabric_type = "default"
        
        if destination is None or destination == "":
            destination = QuoteConfig.DEFAULT_DESTINATION
        
        # Get supplier location safely
        supplier_country = safe_get_value(supplier, 'location', 'Unknown')
        
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
        
        # Safety check: ensure shipping cost is positive
        if shipping_cost < 0:
            shipping_cost = 0.0
        
        # Calculate insurance (5% of material + shipping value)
        unit_price = safe_float(safe_get_value(supplier, 'price_per_unit'), QuoteConfig.DEFAULT_UNIT_PRICE)
        material_value = unit_price * quantity
        
        # Safety check: ensure material value is positive
        if material_value < 0:
            material_value = 0.0
        
        insurance_base = material_value + shipping_cost
        insurance_cost = insurance_base * 0.05
        
        # Calculate customs duties based on fabric type
        customs_rate = get_customs_rate(fabric_type)
        customs_duties = material_value * customs_rate
        
        # Calculate handling fees (tiered based on order size)
        handling_fees = calculate_handling_fees(quantity, total_weight_kg)
        
        # Total logistics cost
        total_logistics = shipping_cost + insurance_cost + customs_duties + handling_fees
        
        # Final safety check: ensure all values are positive
        shipping_cost = max(0.0, shipping_cost)
        insurance_cost = max(0.0, insurance_cost)
        customs_duties = max(0.0, customs_duties)
        handling_fees = max(0.0, handling_fees)
        total_logistics = max(0.0, total_logistics)
        
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
        return get_default_logistics_cost()


def get_default_logistics_cost() -> LogisticsCost:
    """Return default logistics cost when calculation fails"""
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
    Get shipping rate with caching and safety checks
    
    Args:
        route_key: Tuple of (origin, destination) or None
        origin: Origin country
        destination: Destination country or None
    
    Returns:
        float: Shipping rate per kg
    """
    try:
        # Safety check: validate inputs
        if origin is None or origin == "" or origin == "Unknown":
            return QuoteConfig.SHIPPING_RATES[('default_international',)]
        
        if not destination or destination == "" or destination == "Unknown":
            return QuoteConfig.SHIPPING_RATES[('default_international',)]
        
        if route_key and route_key in QuoteConfig.SHIPPING_RATES:
            return QuoteConfig.SHIPPING_RATES[route_key]
        
        # Check if both are in Asia (regional rate)
        asian_countries = ['China', 'India', 'Pakistan', 'Bangladesh', 'Vietnam', 'Thailand', 'Indonesia']
        if origin in asian_countries and destination in asian_countries:
            logger.debug(f"Using regional shipping rate for {origin} to {destination}.")
            return QuoteConfig.SHIPPING_RATES[('default_regional',)]
        
        logger.debug(f"No specific shipping rate found for {origin} to {destination}, using default international rate.")
        
        # International rate
        return QuoteConfig.SHIPPING_RATES[('default_international',)]
        
    except Exception as e:
        logger.error(f"Error getting shipping rate: {str(e)}")
        return QuoteConfig.SHIPPING_RATES[('default_international',)]


def get_customs_rate(fabric_type: str) -> float:
    """
    Determine customs duty rate based on fabric type with safety checks
    
    Args:
        fabric_type: Type/description of fabric
    
    Returns:
        float: Customs duty rate (as decimal, e.g., 0.12 for 12%)
    """
    try:
        if fabric_type is None or fabric_type == "":
            return QuoteConfig.CUSTOMS_RATES['default']
        
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
        
    except Exception as e:
        logger.error(f"Error getting customs rate: {str(e)}")
        return QuoteConfig.CUSTOMS_RATES['default']


def calculate_volume_discount(weight_kg: float) -> float:
    """
    Calculate volume discount based on shipment weight with safety checks
    
    Args:
        weight_kg: Total weight in kilograms
    
    Returns:
        float: Discount rate (e.g., 0.05 for 5% discount)
    """
    try:
        weight_kg = safe_float(weight_kg, 0.0)
        
        if weight_kg <= 0:
            return 0.0
        
        if weight_kg > 10000:
            return 0.10  # 10% discount for very large shipments
        elif weight_kg > 5000:
            return 0.07  # 7% discount
        elif weight_kg > 2000:
            return 0.05  # 5% discount
        elif weight_kg > 1000:
            return 0.03  # 3% discount
        
        return 0.0  # No discount for smaller shipments
        
    except Exception as e:
        logger.error(f"Error calculating volume discount: {str(e)}")
        return 0.0


def calculate_handling_fees(quantity: float, weight_kg: float) -> float:
    """
    Calculate handling fees based on order size and weight with safety checks
    
    Args:
        quantity: Order quantity
        weight_kg: Total weight
    
    Returns:
        float: Handling fee amount
    """
    try:
        quantity = safe_float(quantity, 0.0)
        weight_kg = safe_float(weight_kg, 0.0)
        
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
        
    except Exception as e:
        logger.error(f"Error calculating handling fees: {str(e)}")
        return 75.0  # Default minimum fee


def round_decimal(value: float, places: int = 2) -> float:
    """
    Round a float to specified decimal places with safety checks
    
    Args:
        value: Value to round
        places: Number of decimal places
    
    Returns:
        float: Rounded value
    """
    try:
        if value is None:
            return 0.0
        
        value = safe_float(value, 0.0)
        
        decimal_value = Decimal(str(value))
        rounded = decimal_value.quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)
        return float(rounded)
        
    except (InvalidOperation, ValueError, TypeError) as e:
        logger.warning(f"Error rounding decimal {value}: {str(e)}, returning original")
        return safe_float(value, 0.0)


def calculate_supplier_score(
    supplier: Dict, 
    extracted_params: Dict,
    all_suppliers: List[Dict]
) -> float:
    """
    Calculate comprehensive supplier score using multiple weighted factors with safety checks
    
    Args:
        supplier: Individual supplier data
        extracted_params: Client requirements
        all_suppliers: All available suppliers for market comparison
    
    Returns:
        float: Overall score (0-100)
    """
    try:
        # Safety check: validate inputs
        if supplier is None:
            logger.warning("Supplier is None, returning default score")
            return 50.0
        
        if not isinstance(all_suppliers, list) or len(all_suppliers) == 0:
            logger.warning("No suppliers for comparison, using default score")
            return 50.0
        
        weights = QuoteConfig.SCORING_WEIGHTS
        
        # Use overall_score if available, otherwise calculate
        existing_score = safe_get_value(supplier, 'overall_score')
        if existing_score is not None and existing_score > 0:
            return safe_float(existing_score, 50.0)
        
        # 1. Price Score (30%)
        prices = []
        for s in all_suppliers:
            price = safe_float(safe_get_value(s, 'price_per_unit'), 0)
            if price > 0:
                prices.append(price)
        
        if prices:
            avg_market_price = sum(prices) / len(prices)
        else:
            avg_market_price = QuoteConfig.DEFAULT_UNIT_PRICE
        
        supplier_price = safe_float(
            safe_get_value(supplier, 'price_per_unit'),
            avg_market_price
        )
        
        if avg_market_price > 0 and supplier_price > 0:
            price_ratio = supplier_price / avg_market_price
            price_score = max(0, min(100, 100 - ((price_ratio - 1) * 100)))
        else:
            price_score = 50.0
        
        # 2. Reliability Score (25%)
        reputation = safe_float(
            safe_get_value(supplier, 'reputation_score'),
            QuoteConfig.DEFAULT_REPUTATION_SCORE
        )
        reliability_score = reputation * 10
        reliability_score = max(0, min(100, reliability_score))
        
        # 3. Lead Time Score (20%)
        params_dict = extracted_params if isinstance(extracted_params, dict) else {}
        logistics_dict = safe_get_value(params_dict, 'logistics_details', {})
        
        target_lead_time = safe_int(
            safe_get_value(logistics_dict, 'timeline_days'),
            QuoteConfig.DEFAULT_LEAD_TIME
        )
        
        supplier_lead_time = safe_int(
            safe_get_value(supplier, 'lead_time_days'),
            QuoteConfig.DEFAULT_LEAD_TIME
        )
        
        if target_lead_time and target_lead_time > 0:
            lead_time_ratio = supplier_lead_time / target_lead_time
            lead_time_score = max(0, min(100, 100 - ((lead_time_ratio - 1) * 50)))
        else:
            lead_time_score = 50.0
        
        # 4. Certification Score (15%)
        fabric_dict = safe_get_value(params_dict, 'fabric_details', {})
        required_certs_list = safe_get_value(fabric_dict, 'certifications', [])
        
        if not isinstance(required_certs_list, list):
            required_certs_list = []
        
        required_certs = set(required_certs_list)
        
        supplier_certs_list = safe_get_value(supplier, 'certifications', [])
        if not isinstance(supplier_certs_list, list):
            supplier_certs_list = []
        
        supplier_certs = set(supplier_certs_list)
        
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
        
        # Ensure score is within bounds
        overall_score = max(0.0, min(100.0, overall_score))
        
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
    Analyze supplier to identify key advantages and potential risks with safety checks
    
    Args:
        supplier: Supplier data
        all_suppliers: All suppliers for comparison
        extracted_params: Client requirements
    
    Returns:
        Tuple of (advantages, risks)
    """
    advantages = []
    risks = []
    
    try:
        # Safety checks
        if supplier is None:
            return (["Unable to analyze - supplier data missing"], 
                   ["Missing supplier information"])
        
        if not isinstance(all_suppliers, list) or len(all_suppliers) == 0:
            all_suppliers = [supplier]
        
        # Get comparison metrics safely
        prices = []
        for s in all_suppliers:
            price = safe_float(safe_get_value(s, 'price_per_unit'), 0)
            if price > 0:
                prices.append(price)
        
        min_price = min(prices) if prices else 0
        avg_price = sum(prices) / len(prices) if prices else QuoteConfig.DEFAULT_UNIT_PRICE
        
        lead_times = []
        for s in all_suppliers:
            lead_time = safe_int(safe_get_value(s, 'lead_time_days'), 0)
            if lead_time > 0:
                lead_times.append(lead_time)
        
        min_lead_time = min(lead_times) if lead_times else QuoteConfig.DEFAULT_LEAD_TIME
        avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else QuoteConfig.DEFAULT_LEAD_TIME
        
        # Analyze advantages
        reputation = safe_float(
            safe_get_value(supplier, 'reputation_score'),
            QuoteConfig.DEFAULT_REPUTATION_SCORE
        )
        
        if reputation >= 8:
            advantages.append("✓ Excellent reliability track record (8+/10)")
        elif reputation >= 7:
            advantages.append("✓ Good reliability score")
        
        supplier_lead_time = safe_int(
            safe_get_value(supplier, 'lead_time_days'),
            QuoteConfig.DEFAULT_LEAD_TIME
        )
        
        if supplier_lead_time > 0 and min_lead_time > 0:
            if supplier_lead_time <= min_lead_time * 1.1:
                advantages.append(f"✓ Fast delivery capability ({supplier_lead_time} days)")
            elif supplier_lead_time <= avg_lead_time:
                advantages.append("✓ Competitive lead time")
        
        supplier_price = safe_float(
            safe_get_value(supplier, 'price_per_unit'),
            avg_price
        )
        
        if avg_price > 0 and supplier_price > 0:
            if supplier_price <= min_price * 1.05:
                advantages.append(f"✓ Most competitive pricing (${supplier_price:.2f}/unit)")
            elif supplier_price <= avg_price:
                advantages.append("✓ Below market average pricing")
        
        # Check certifications safely
        supplier_certs_list = safe_get_value(supplier, 'certifications', [])
        if not isinstance(supplier_certs_list, list):
            supplier_certs_list = []
        
        supplier_certs = set(supplier_certs_list)
        
        if 'GOTS' in supplier_certs or any('organic' in str(c).lower() for c in supplier_certs):
            advantages.append("✓ Organic/GOTS certification available")
        if 'OEKO-TEX' in supplier_certs:
            advantages.append("✓ OEKO-TEX certified")
        if len(supplier_certs) >= 3:
            advantages.append(f"✓ Multiple certifications ({len(supplier_certs)})")
        
        # Analyze risks
        if reputation < 7:
            risks.append("⚠ Lower reliability score - recommend closer monitoring")
        
        if avg_lead_time > 0 and supplier_lead_time > avg_lead_time * 1.3:
            risks.append(f"⚠ Extended lead time ({supplier_lead_time} days) may impact timeline")
        
        min_order = safe_int(safe_get_value(supplier, 'minimum_order_qty'), 0)
        
        params_dict = extracted_params if isinstance(extracted_params, dict) else {}
        fabric_dict = safe_get_value(params_dict, 'fabric_details', {})
        requested_qty = safe_int(safe_get_value(fabric_dict, 'quantity'), 0)
        
        if min_order > 0 and requested_qty > 0 and min_order > requested_qty:
            risks.append(f"⚠ MOQ ({min_order:,}) exceeds requested quantity")
        
        if avg_price > 0 and supplier_price > avg_price * 1.2:
            risks.append("⚠ Pricing above market average")
        
        # Default messages if none found
        if not advantages:
            advantages.append("Competitive option for consideration")
        if not risks:
            risks.append("Standard supplier risks apply - due diligence recommended")
        
        return advantages, risks
        
    except Exception as e:
        logger.error(f"Error analyzing supplier advantages/risks: {str(e)}")
        return (["Unable to fully analyze advantages"], 
                ["Unable to fully analyze risks - manual review recommended"])


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
    Format supplier data for prompt inclusion with enhanced details and safety checks
    """
    try:
        if not suppliers or not isinstance(suppliers, list):
            return "No supplier options available"
        
        options_text = []
        
        for i, supplier in enumerate(suppliers[:QuoteConfig.MAX_SUPPLIER_OPTIONS], 1):
            if supplier is None:
                continue
            
            supplier_id = safe_get_value(supplier, 'supplier_id', f'supplier_{i}')
            logistics = logistics_costs.get(supplier_id, get_default_logistics_cost())
            
            unit_price = safe_float(safe_get_value(supplier, 'price_per_unit'), QuoteConfig.DEFAULT_UNIT_PRICE)
            quantity = safe_float(safe_get_value(supplier, 'quantity'), QuoteConfig.DEFAULT_QUANTITY)
            material_cost = unit_price * quantity
            total_cost = material_cost + logistics.total_logistics
            
            supplier_name = safe_get_value(supplier, 'name', 'Unknown Supplier')
            location = safe_get_value(supplier, 'location', 'Unknown')
            lead_time = safe_int(safe_get_value(supplier, 'lead_time_days'), QuoteConfig.DEFAULT_LEAD_TIME)
            reputation = safe_float(safe_get_value(supplier, 'reputation_score'), QuoteConfig.DEFAULT_REPUTATION_SCORE)
            overall_score = safe_float(safe_get_value(supplier, 'overall_score'), 50.0)
            
            specialties_list = safe_get_value(supplier, 'specialties', [])
            if not isinstance(specialties_list, list):
                specialties_list = ['N/A']
            specialties = ', '.join(specialties_list) if specialties_list else 'N/A'

           #  FIXED CERTIFICATIONS BLOCK
            certs_list = safe_get_value(supplier, 'certifications', [])
            if not isinstance(certs_list, list):
                certs_list = ['None']
            certifications = ', '.join(certs_list) if certs_list else 'None'

            moq = safe_int(safe_get_value(supplier, 'minimum_order_qty'), 0)
            moq_str = f"{moq:,}" if moq > 0 else "N/A"

            option_text = f"""
**Option {i}: {supplier_name}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Location: {location}
Unit Price: ${unit_price:.2f}
Material Cost: ${material_cost:,.2f}

Logistics Breakdown:
  - Shipping: ${logistics.shipping_cost:,.2f}
  - Insurance: ${logistics.insurance_cost:,.2f}
  - Customs: ${logistics.customs_duties:,.2f}
  - Handling: ${logistics.handling_fees:,.2f}
  - Subtotal: ${logistics.total_logistics:,.2f}

**Total Landed Cost: ${total_cost:,.2f}**

Lead Time: {lead_time} days
Reputation Score: {reputation:.1f}/10
Overall Score: {overall_score:.1f}/100

Specialties: {specialties}
Certifications: {certifications}
MOQ: {moq_str} units
"""
            options_text.append(option_text)

        return "\n".join(options_text) if options_text else "No supplier options available"

    except Exception as e:
        logger.error(f"Error preparing supplier options text: {str(e)}")
        return "Unable to format supplier options"



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
            if unit_price is None:
                unit_price = 5.0
            if quantity is None:
                quantity = 1
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
                savings_text = f"\n\n💰 **Potential Savings:** Up to {quote_result.estimated_savings}% by choosing optimal supplier"
            
            # Create comprehensive assistant message
            assistant_message = f"""✅ **Quote Generated Successfully!**

**Quote ID:** `{quote_result.quote_id}`

{quote_result.strategic_analysis.market_assessment}

🎯 **My Recommendation:**

**{best_supplier.supplier_name}** from {best_supplier.supplier_location}

💰 Total Landed Cost: **${best_supplier.total_landed_cost:,.2f}** (${best_supplier.unit_price:.2f}/unit)
⏱️ Lead Time: {best_supplier.lead_time_days} days
⭐ Reliability: {best_supplier.reliability_score}/10
🏆 Overall Score: {best_supplier.overall_score:.1f}/100

**Why this supplier?**
{quote_result.strategic_analysis.recommendation_reasoning}

💡 **Negotiation Opportunities:**
{chr(10).join(f"• {opp}" for opp in quote_result.strategic_analysis.negotiation_opportunities[:3])}{savings_text}

📊 Complete quote with {len(supplier_options)} detailed supplier options is ready for review.
        """
        else:
            assistant_message = "⚠️ Quote generated but no suppliers fully meet all requirements. Please review options and alternative strategies."
        
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