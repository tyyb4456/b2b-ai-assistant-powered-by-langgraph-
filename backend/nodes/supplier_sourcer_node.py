from langchain.chat_models import init_chat_model
from typing import Dict, Any, List
from datetime import datetime
import json
from langchain_core.messages import HumanMessage
from sqlalchemy import text
from database import engine
from state import AgentState

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from models.suppliers_detail_model import SupplierSearchResult, Supplier, SupplierAnalysis

def ai_filter_and_analyze_suppliers(
    suppliers: List[Supplier],
    extracted_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Use AI model to intelligently filter suppliers and generate insights
    
    Args:
        suppliers: List of all suppliers from database
        extracted_params: Original request parameters
    
    Returns:
        dict: Filtered suppliers, insights, and alternatives
    """
    try:
        # Prepare supplier data for AI analysis
        suppliers_summary = []
        for s in suppliers:
            suppliers_summary.append({
                "supplier_id": s.supplier_id,
                "name": s.name,
                "location": s.location,
                "price_per_unit": s.price_per_unit,
                "currency": s.currency,
                "lead_time_days": s.lead_time_days,
                "min_order_qty": s.minimum_order_qty,
                "reputation_score": s.reputation_score,
                "specialties": s.specialties,
                "certifications": s.certifications,
                "overall_score": s.overall_score
            })
        
        # Create AI analysis prompt
        analysis_prompt = f"""You are an expert B2B textile sourcing analyst. Analyze these suppliers and provide intelligent filtering.

CUSTOMER REQUIREMENTS:
- Fabric Type: {extracted_params.get('fabric_details', {}).get('type')}
- Quantity: {extracted_params.get('fabric_details', {}).get('quantity')} {extracted_params.get('fabric_details', {}).get('unit', 'units')}
- Quality Specs: {extracted_params.get('fabric_details', {}).get('quality_specs', [])}
- Certifications Required: {extracted_params.get('fabric_details', {}).get('certifications', [])}
- Max Price: {extracted_params.get('price_constraints', {}).get('max_price')} {extracted_params.get('price_constraints', {}).get('currency', 'USD')}
- Urgency Level: {extracted_params.get('urgency_level', 'medium')}
- Timeline: {extracted_params.get('logistics_details', {}).get('timeline', 'Not specified')}

AVAILABLE SUPPLIERS ({len(suppliers)} found):
{json.dumps(suppliers_summary, indent=2)}

ANALYSIS TASKS:

1. FILTER SUPPLIERS: Select the best-fit suppliers (5-15 suppliers) based on:
   - Price competitiveness (within budget, good value)
   - Lead time matching urgency
   - Reputation and reliability scores
   - Certification match
   - Geographic diversity (include options from different regions)
   - MOQ flexibility
   - Overall score

2. RANK TOP SUPPLIERS: From filtered list, rank top 5-10 by best overall fit

3. MARKET INSIGHTS: Provide 2-3 paragraph analysis covering:
   - Price range analysis (average, min, max) and competitiveness
   - Lead time trends across suppliers
   - Geographic sourcing recommendations
   - Quality vs cost trade-offs
   - Risk considerations (single vs multiple suppliers)
   - Specific recommendations for this buyer

4. ALTERNATIVES: Suggest 2-4 alternative options:
   - Similar fabric types that might work
   - Suppliers with slight trade-offs (higher price but faster, etc.)
   - Different sourcing regions to consider
   - MOQ alternatives if applicable

5. FILTERING RATIONALE: Explain why some suppliers were excluded

Return supplier_ids in your lists, not full objects."""

        # Get AI analysis
        model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
        ai_analysis_model = model.with_structured_output(SupplierAnalysis)
        

        ai_result: SupplierAnalysis = ai_analysis_model.invoke([
            HumanMessage(content=analysis_prompt)
        ])
        
        # Map supplier IDs back to Supplier objects
        supplier_map = {s.supplier_id: s for s in suppliers}
        
        filtered_suppliers = [
            supplier_map[sid] for sid in ai_result.filtered_supplier_ids 
            if sid in supplier_map
        ]
        
        top_recommendations = [
            supplier_map[sid] for sid in ai_result.top_supplier_ids 
            if sid in supplier_map
        ]

        print(f"   Filtering Rationale: {ai_result.filtering_rationale[:100]}...")
        logger.info(f"AI filtering succeeded: Total Suppliers: {len(suppliers)}, {len(filtered_suppliers)} suppliers filtered, {len(top_recommendations)} top recommendations, rationale: {ai_result.filtering_rationale[:100]}...")

        return {
            'filtered_suppliers': filtered_suppliers,
            'top_recommendations': top_recommendations,
            'market_insights': ai_result.market_insights,
            'alternative_suggestions': ai_result.alternative_suggestions,
            'search_strategy': ai_result.search_strategy,
            'filtering_rationale': ai_result.filtering_rationale
        }
        
    except Exception as e:
        print(f"⚠️  AI filtering failed, falling back to basic filtering: {str(e)}")
        
        # Fallback: Use simple filtering
        filtered = suppliers[:15]  # Take top 15
        top = suppliers[:5]  # Take top 5
        
        return {
            'filtered_suppliers': filtered,
            'top_recommendations': top,
            'market_insights': generate_market_insights(extracted_params, len(suppliers)),
            'alternative_suggestions': generate_alternatives(extracted_params),
            'search_strategy': 'Basic reputation and price-based filtering (AI unavailable)',
            'filtering_rationale': 'Using default filtering due to AI processing error'
        }


# ==== ENHANCED VERSION: Direct SQL Execution with AI Filtering =====

def search_suppliers_direct_sql(state : AgentState):
    """
    Enhanced version: Directly execute SQL and structure results with AI filtering
    Uses AI model for intelligent filtering, market insights, and alternatives
    """
    try:

        # To this (with safety check):
        extracted_params = state.get('extracted_parameters', {})

        if not extracted_params:
            logger.error("No extracted parameters found in state")
            return {
                'supplier_search_result': None,
                'top_suppliers': [],
                'messages': ['Error: No parameters extracted from user input']
            }
        
        fabric_details = extracted_params.get('fabric_details', {})
        price_constraints = extracted_params.get('price_constraints', {})
        urgency = extracted_params.get('urgency_level', 'medium')
        
        # Build SQL query with named parameters - Get MORE suppliers initially (up to 25)
        query = """
        SELECT 
            s.supplier_id,
            s.name,
            s.location,
            s.email,
            s.phone,
            s.website,
            s.contact_person,
            s.price_per_unit,
            s.currency,
            s.lead_time_days,
            s.min_order_qty,
            s.reputation_score,
            s.active,
            s.specialties,
            s.certifications,
            s.source,
            s.notes,
            AVG(sp.reliability_score) as avg_reliability,
            AVG(sp.on_time_delivery_rate) as avg_delivery_rate
        FROM suppliers s
        LEFT JOIN supplier_performance sp ON s.supplier_id = sp.supplier_id
        WHERE s.active = 1
        """
        
        params = {}
        
        # Add fabric type filter
        fabric_type = fabric_details.get('type')
        if fabric_type:
            query += " AND s.specialties LIKE :fabric_type"
            params['fabric_type'] = f"%{fabric_type}%"
        
        # Add quantity filter
        quantity = fabric_details.get('quantity')
        if quantity:
            query += " AND s.min_order_qty <= :quantity"
            params['quantity'] = quantity
        
        # Add price filter
        max_price = price_constraints.get('max_price')
        if max_price:
            query += " AND s.price_per_unit <= :max_price"
            params['max_price'] = max_price
        
        # Add certification filter
        certifications = fabric_details.get('certifications', [])
        for i, cert in enumerate(certifications):
            param_name = f"cert_{i}"
            query += f" AND s.certifications LIKE :{param_name}"
            params[param_name] = f"%{cert}%"
        
        # Group by supplier
        query += " GROUP BY s.supplier_id"
        
        # Order by urgency or reputation
        if urgency in ['high', 'urgent']:
            query += " ORDER BY s.lead_time_days ASC, s.reputation_score DESC"
        else:
            query += " ORDER BY s.reputation_score DESC, s.lead_time_days ASC"
        
        query += " LIMIT 25"  # Get more suppliers for AI filtering

        logger.info(f"Executing supplier search SQL with params: {params}")
        logger.info(f"SQL Query: {query}")
        logger.debug(f"SQL Query: {query}")
        
        # Execute query using engine directly
        
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            rows = result.fetchall()
        
        # Parse ALL results into Supplier objects
        all_suppliers = []
        for row in rows:
            supplier = Supplier(
                supplier_id=row[0],
                name=row[1],
                location=row[2],
                email=row[3],
                phone=row[4],
                website=row[5],
                contact_person=row[6],
                price_per_unit=row[7],
                currency=row[8],
                lead_time_days=row[9],
                minimum_order_qty=row[10],
                reputation_score=row[11],
                active=bool(row[12]),
                specialties=row[13].split(',') if row[13] else [],
                certifications=row[14].split(',') if row[14] else [],
                source=row[15],
                notes=row[16],
                overall_score=calculate_overall_score(row)
            )
            all_suppliers.append(supplier)
        
        total_found = len(all_suppliers)

        logger.info(f"Total suppliers found from SQL: {total_found}")
        logger.info(f"Supplier IDs found: {[s.supplier_id for s in all_suppliers]}")
        logger.debug(f"Suppliers found: {[s.supplier_id for s in all_suppliers]}")
        
        # If suppliers found, use AI to filter and analyze
        if total_found > 0:
            ai_analysis = ai_filter_and_analyze_suppliers(
                suppliers=all_suppliers,
                extracted_params=extracted_params
            )
            
            filtered_suppliers = ai_analysis['filtered_suppliers']
            top_recommendations = ai_analysis['top_recommendations']
            market_insights = ai_analysis['market_insights']
            alternative_suggestions = ai_analysis['alternative_suggestions']
            search_strategy = ai_analysis['search_strategy']
            filtering_rationale = ai_analysis['filtering_rationale']

            
        else:
            # No suppliers found
            filtered_suppliers = []
            top_recommendations = []
            market_insights = f"No suppliers found matching '{fabric_type}' with specified criteria. Consider broadening search parameters."
            alternative_suggestions = generate_alternatives(extracted_params)
            search_strategy = "No results - standard search"
        
        # Create result
        supplier_search_result = SupplierSearchResult(
            request_id=extracted_params.get('item_id', 'REQ_' + datetime.now().strftime('%Y%m%d%H%M%S')),
            total_suppliers_found=total_found,
            filtered_suppliers=len(filtered_suppliers),
            top_recommendations=top_recommendations[:10],  # Max 10 recommendations
            search_strategy=search_strategy,
            market_insights=market_insights,
            confidence=extracted_params.get('confidence', 0.8),
            alternative_suggestions=alternative_suggestions,
            search_timestamp=datetime.utcnow(),
            search_parameters=extracted_params
        )

        assistant_message = market_insights

        # Optionally append alternative suggestions if results are limited
        if supplier_search_result.filtered_suppliers < 5 and supplier_search_result.alternative_suggestions:
            assistant_message += "\n\n💡 **Alternative Options:**\n"
            assistant_message += "\n".join(f"• {suggestion}" for suggestion in supplier_search_result.alternative_suggestions)

        top_suppliers = [supplier.model_dump() for supplier in supplier_search_result.top_recommendations]  # Pydantic v2

        return {
            'supplier_search_result': supplier_search_result,
            'top_suppliers': top_suppliers,
            'messages': [assistant_message]
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error during supplier search: {str(e)}\n{error_details}")
        
        supplier_search_result =  SupplierSearchResult(
            request_id=extracted_params.get('item_id', 'ERROR'),
            total_suppliers_found=0,
            filtered_suppliers=0,
            top_recommendations=[],
            search_strategy="Error during search",
            market_insights=f"Search failed: {str(e)}",
            confidence=0.0,
            alternative_suggestions=["Please refine search parameters"],
            search_parameters=extracted_params
        )

        return {
            'supplier_search_result': supplier_search_result,
            'top_suppliers': [],
            'messages': [f"Error during supplier search: {str(e)}"]
        }

def generate_market_insights(params: Dict[str, Any], supplier_count: int) -> str:
    """Generate market insights based on search results"""
    fabric_type = params.get('fabric_details', {}).get('type', 'fabric')
    
    if supplier_count == 0:
        return f"Limited supplier availability for {fabric_type}. Consider broadening search criteria."
    elif supplier_count < 3:
        return f"Competitive market for {fabric_type} with few specialized suppliers. Recommend early engagement."
    else:
        return f"Strong supplier availability for {fabric_type} with {supplier_count} qualified options. Good negotiation position."


def generate_alternatives(params: Dict[str, Any]) -> List[str]:
    """Generate alternative suggestions if needed"""
    alternatives = []
    fabric_details = params.get('fabric_details', {})
    
    # Suggest alternatives based on fabric type
    fabric_type = fabric_details.get('type', '').lower()
    if 'cotton' in fabric_type:
        alternatives.append("Consider cotton-polyester blends for cost savings")
    if 'organic' in str(fabric_details.get('quality_specs', [])).lower():
        alternatives.append("BCI cotton as a more affordable certified option")
    
    return alternatives



def calculate_overall_score(row_data) -> float:
    """Calculate weighted overall score for supplier"""
    reputation = row_data[11] or 5.0
    reliability = row_data[17] or 5.0
    delivery_rate = row_data[18] or 80.0
    
    score = (
        reputation * 0.4 +  # 40% reputation
        reliability * 0.3 +  # 30% reliability
        (delivery_rate / 10) * 0.3  # 30% delivery rate
    )
    
    return min(100.0, score * 10)  # Scale to 0-100