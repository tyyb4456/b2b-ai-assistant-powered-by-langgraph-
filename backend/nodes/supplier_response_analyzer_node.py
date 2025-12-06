from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from state import AgentState
from models.analyze_supplier_response_model import SupplierIntent, ExtractedTerms, NegotiationAnalysis
from loguru import logger

load_dotenv()


def create_intent_classification_prompt():
    """Create prompt for supplier intent classification and sentiment analysis"""
    
    system_prompt = """You are an expert B2B negotiation analyst specializing in textile industry communications. Your expertise includes cross-cultural business communication, supplier relationship dynamics, and negotiation psychology.

Your primary task is to analyze supplier responses and classify their intent with high accuracy.

**INTENT CLASSIFICATION:**

1. **accept**: Supplier agrees to proposed terms unconditionally
   - Indicators: "We accept", "Terms are acceptable", "Let's proceed", "Agreed"
   - May include logistics coordination or next steps discussion

2. **counteroffer**: Supplier rejects current terms but proposes alternatives
   - Indicators: New prices, modified timelines, alternative specifications
   - "We can do X if you...", "Our best price is...", "How about..."
   - Keeps negotiation alive with viable alternatives

3. **reject**: Definitive rejection without viable alternatives
   - Indicators: "Cannot accept", "Not possible", "Must decline"
   - No constructive alternatives offered
   - May signal end of negotiation

4. **clarification_request**: Supplier needs more information
   - Indicators: Questions about specifications, quantities, timelines
   - "Could you clarify...", "We need more details about..."
   - Shows engagement but requires information before proceeding

5. **delay**: Supplier requests more time or indicates delays
   - Indicators: "Need more time", "Will get back to you", "Checking with management"
   - Shows continued interest but needs time

**SENTIMENT ANALYSIS:**
- **positive**: Enthusiastic, collaborative tone
- **neutral**: Professional, matter-of-fact
- **negative**: Resistant, pessimistic
- **frustrated**: Showing impatience or annoyance
- **cooperative**: Willing to work together, solution-oriented

**RELATIONSHIP SIGNALS:**
- Positive: Partnership language, long-term references, appreciation
- Negative: Formal language, resistance, ultimatums

**URGENCY INDICATORS:**
- Time pressure phrases: "immediately", "urgent", "deadline", "rush"
- Decision pressure: "final offer", "limited time", "expires"

Be precise and confident in your classification. The downstream workflow depends on accurate intent detection."""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Analyze this supplier response for intent and sentiment:

**NEGOTIATION CONTEXT:**
- Current negotiation round: {negotiation_round}
- Previous offer: {previous_offer}
- Our last message: {our_last_message}

**SUPPLIER'S RESPONSE:**
{supplier_response}

**SUPPLIER PROFILE:**
- Company: {supplier_name}
- Location: {supplier_location}
- Previous relationship: {relationship_history}

Classify the intent, assess sentiment, and identify key signals.""")
    ])


def create_term_extraction_prompt():
    """Create prompt for extracting specific terms from counteroffer"""
    
    system_prompt = """You are an expert contract term extraction system for B2B textile negotiations. Your job is to identify and extract specific numerical values, conditions, and terms from supplier communications.

**EXTRACTION PRIORITIES:**

1. **Pricing Information:**
   - Exact price numbers with currency
   - Price per unit (meter, kg, piece)
   - Volume-based pricing tiers
   - Payment discounts or surcharges

2. **Timeline Information:**
   - Lead times in days/weeks
   - Production schedules
   - Delivery dates
   - Seasonal constraints

3. **Quantity Requirements:**
   - Minimum order quantities (MOQ)
   - Maximum capacity limits
   - Volume commitments

4. **Commercial Terms:**
   - Payment terms (Net 30, 60, etc.)
   - Incoterms (FOB, CIF, etc.)
   - Currency preferences
   - Credit terms

5. **Quality/Specification Changes:**
   - Grade modifications
   - Certification adjustments
   - Technical specification changes

6. **Concessions & Value-Adds:**
   - What supplier is offering beyond basic terms
   - Flexibility on certain conditions
   - Additional services or benefits

**EXTRACTION RULES:**
- Extract ONLY explicitly stated terms
- Convert relative references to absolute values where possible
- If multiple options are presented, extract the primary offer
- Note any conditional terms ("if you order 50k+, price drops to...")
- Be conservative - if unclear, leave field empty

**NUMERICAL PRECISION:**
- Preserve exact numbers as stated
- Note ranges (e.g., "45-50 days" -> 50 for lead time)
- Extract percentage changes if mentioned"""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Extract specific terms from this supplier counteroffer:

**SUPPLIER'S MESSAGE:**
{supplier_response}

**PREVIOUS TERMS FOR REFERENCE:**
- Previous price: {previous_price}
- Previous lead time: {previous_lead_time}
- Previous MOQ: {previous_moq}

**ORIGINAL REQUEST CONTEXT:**
- Requested quantity: {requested_quantity}
- Target delivery: {target_timeline}
- Budget range: {budget_range}

Extract all new terms, concessions, and conditions mentioned in the response.""")
    ])

def create_strategic_analysis_prompt():
    """Create prompt for comprehensive negotiation analysis"""
    
    system_prompt = """You are a senior B2B negotiation strategist with 15+ years of experience in textile industry procurement. Your expertise includes market analysis, supplier psychology, and tactical negotiation planning.

Your task is to provide strategic analysis and actionable recommendations based on the supplier's response.

**ANALYSIS FRAMEWORK:**

1. **Market Comparison Analysis:**
   - Compare new terms to original market benchmarks
   - Assess competitiveness vs. alternative suppliers
   - Evaluate value proposition changes

2. **Movement Analysis:**
   - Quantify supplier's movement from initial position
   - Assess direction and magnitude of changes
   - Identify what drove their concessions/resistance

3. **Strategic Assessment:**
   - Overall attractiveness of current offer
   - Likelihood of further movement
   - Alignment with buyer's priorities

4. **Leverage Analysis:**
   - Current negotiation power balance
   - Factors strengthening/weakening position
   - Time pressure considerations

5. **Tactical Recommendations:**
   - Specific next moves to optimize outcome
   - Areas to push vs. areas to concede
   - Communication strategy for response

**RECOMMENDATION QUALITY:**
- Be specific and actionable
- Consider both short-term gains and relationship preservation
- Account for cultural and regional business practices
- Balance multiple objectives (price, quality, timeline, relationship)

**RISK ASSESSMENT:**
- Identify potential deal-breakers
- Flag concerning patterns or changes
- Highlight what could go wrong

**OPPORTUNITY IDENTIFICATION:**
- Spot openings for additional value
- Identify areas of flexibility
- Note positive relationship signals to build upon

Provide analysis that enables confident, informed decision-making."""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Provide strategic analysis of this negotiation situation:

**SUPPLIER'S RESPONSE ANALYSIS:**
Intent: {supplier_intent}
Sentiment: {supplier_sentiment}
New Terms: {extracted_terms}

**NEGOTIATION CONTEXT:**
- Round: {negotiation_round}
- Original target price: {target_price}
- Market benchmark: {market_benchmark}
- Our priorities: {buyer_priorities}
- Urgency level: {urgency_level}

**SUPPLIER PROFILE:**
- Reliability score: {supplier_reliability}
- Previous relationship: {relationship_history}
- Geographic location: {supplier_location}

**COMPETITIVE LANDSCAPE:**
- Alternative suppliers: {alternative_suppliers}
- Market conditions: {market_conditions}

Provide comprehensive strategic analysis with specific tactical recommendations.""")
    ])

# Initialize models and prompts
model = init_chat_model("google_genai:gemini-2.5-flash")
intent_model = model.with_structured_output(SupplierIntent)
terms_model = model.with_structured_output(ExtractedTerms)
analysis_model = model.with_structured_output(NegotiationAnalysis)

intent_prompt = create_intent_classification_prompt()
terms_prompt = create_term_extraction_prompt()
analysis_prompt = create_strategic_analysis_prompt()

def extract_negotiation_context(state: AgentState):
    """Extract relevant context for analysis from current state"""

    negotiation_history = state.get('negotiation_history', [])
    negotiation_round = state.get('negotiation_round', 1)

    # Extract previous offers and terms
    previous_terms = {}
    drafted_message = state.get('drafted_message_data', {})
    if drafted_message:
        previous_terms = {
            'previous_offer': drafted_message.get('message_body', ''),
            'message_type': drafted_message.get('message_type', '')
        }
    

    # Get original request parameters 
    extracted_params = state.get('extracted_parameters', {})
    original_request = {
        'fabric_details': extracted_params.get('fabric_details', {}),
        'price_constraints': extracted_params.get('price_constraints', {}),
        'logistics_details': extracted_params.get('logistics_details', {}),
        'urgency_level': extracted_params.get('urgency_level', 'medium')
    }

    supplier_data = state.get('top_suppliers', [])

    # Check if user has selected a supplier, otherwise fall back to first supplier
    selected_supplier = state.get('selected_supplier', None)

    
    if selected_supplier:
        # Use the user-selected supplier
        supplier_info = selected_supplier
        logger.info("Using user-selected supplier for profile.")
    elif supplier_data and len(supplier_data) > 0:
        # Fall back to first supplier if no selection made
        supplier_info = supplier_data[0]
        logger.info("No user-selected supplier, using first supplier from search results.")
    else:
        supplier_info = None

    return {
        'negotiation_round': negotiation_round,
        'previous_terms': previous_terms,
        'original_request': original_request,
        'supplier_info': supplier_info,
        'negotiation_history': negotiation_history
    }

def analyze_supplier_response(state: AgentState):
    """
    Node 6b: analyze_supplier_response - Negotiation perception and analysis engine
    
    Purpose:
    - Classify supplier's intent and sentiment from their response
    - Extract specific terms and conditions from counteroffers
    - Provide strategic analysis and tactical recommendations
    - Update negotiation history and determine next steps
    - Transform unstructured supplier communication into actionable intelligence
    
    Args:
        state: Current agent state containing supplier's response and negotiation context
    
    Returns:
        dict: State updates with analysis, extracted terms, and strategic recommendations
    """

    try:
        # Step 1: Extract supplier response and context
        supplier_response = state.get('supplier_response')
        logger.info("Starting analysis of supplier response...")
        logger.info(f"Supplier Response: {supplier_response}")

        
        if not supplier_response:
            return {
                **state,
                "messages": ["No supplier response found to analyze"],
                "status": "no_supplier_response"
            }
        
        context = extract_negotiation_context(state)
        supplier_info = context['supplier_info']

        # Step 2: Classify supplier intent and sentiment
        intent_formatted_prompt = intent_prompt.invoke({
            "supplier_response": supplier_response,
            "negotiation_round": context['negotiation_round'],
            "previous_offer": context['previous_terms'].get('previous_offer', 'Initial outreach'),
            "our_last_message": context['previous_terms'].get('previous_offer', ''),
            "supplier_name": supplier_info.get('name', 'Supplier'),
            "supplier_location": supplier_info.get('location', 'Unknown'),
            "relationship_history": supplier_info.get('notes', 'New supplier')
        })
        
        supplier_intent: SupplierIntent = intent_model.invoke(intent_formatted_prompt)

        # Step 3: Extract terms if it's a counteroffer
        extracted_terms = None
        if supplier_intent.intent == "counteroffer":
            terms_formatted_prompt = terms_prompt.invoke({
                "supplier_response": supplier_response,
                "previous_price": context['previous_terms'].get('price', 'N/A'),
                "previous_lead_time": context['previous_terms'].get('lead_time', 'N/A'),
                "previous_moq": context['previous_terms'].get('moq', 'N/A'),
                "requested_quantity": context['original_request']['fabric_details'].get('quantity', 'N/A'),
                "target_timeline": context['original_request']['logistics_details'].get('timeline', 'N/A'),
                "budget_range": context['original_request']['price_constraints'].get('max_price', 'N/A')
            })
            
            extracted_terms: ExtractedTerms = terms_model.invoke(terms_formatted_prompt)
    
        # Step 4: Perform strategic analysis
        analysis_formatted_prompt = analysis_prompt.invoke({
            "supplier_intent": supplier_intent.intent,
            "supplier_sentiment": supplier_intent.sentiment,
            "extracted_terms": extracted_terms.model_dump() if extracted_terms else "No new terms",
            "negotiation_round": context['negotiation_round'],
            "target_price": context['original_request']['price_constraints'].get('max_price', 'N/A'),
            "market_benchmark": state.get('market_analysis', {}).get('average_price', 'N/A'),
            "buyer_priorities": determine_buyer_priorities(context['original_request']),
            "urgency_level": context['original_request'].get('urgency_level', 'medium'),
            "supplier_reliability": supplier_info.get('reliability_score', 5.0),
            "relationship_history": supplier_info.get('relationship_notes', 'New supplier'),
            "supplier_location": supplier_info.get('country', 'Unknown'),
            "alternative_suppliers": len(state.get('top_suppliers', [])) - 1,
            "market_conditions": state.get('market_analysis', {}).get('market_trend', 'stable')
        })
        
        strategic_analysis: NegotiationAnalysis = analysis_model.invoke(analysis_formatted_prompt)

        # Step 5: Update negotiation history
        negotiation_entry = {
            "timestamp": datetime.now().isoformat(),
            "round": context['negotiation_round'],
            'assistant_message': state.get('drafted_message', ""),
            "supplier_response": supplier_response,
            "intent": supplier_intent.intent,
            "sentiment": supplier_intent.sentiment,
            "terms": extracted_terms.model_dump() if extracted_terms else None,
            "analysis": strategic_analysis.strategic_assessment
        }
        
        updated_history = context['negotiation_history'] + [negotiation_entry]
        
        # Step 6: Determine next step based on intent
        next_step_mapping = {
            "accept": "initiate_contract",
            "counteroffer": "draft_negotiation_message", 
            "reject": "notify_user_of_failure",
            "clarification_request": "provide_clarification",
            "delay": "schedule_follow_up"
        }
        
        next_step = next_step_mapping.get(supplier_intent.intent, "evaluate_negotiation_status")
        
        # Step 7: Create assistant response message
        assistant = generate_analysis_summary(
            supplier_intent, extracted_terms, strategic_analysis, context['negotiation_round']
        )

        logger.info("Supplier response analysis completed successfully.")

        terms_extracted = extracted_terms.model_dump() if extracted_terms else None

        # Step 8: Prepare comprehensive state updates (CREATE state_updates FIRST!)
        state_updates = {
            "supplier_intent": supplier_intent.model_dump(),
            "extracted_terms": terms_extracted,
            "negotiation_analysis": strategic_analysis.model_dump(),
            "negotiation_advice": strategic_analysis.recommended_response,
            "negotiation_history": updated_history,
            "next_step": next_step,
            "negotiation_status": supplier_intent.intent,
            "analysis_confidence": strategic_analysis.confidence_score,
            "supplier_offers": terms_extracted.get('concessions_offered', []) if terms_extracted else [], 
            "messages": [supplier_response, assistant],
            "status": "supplier_response_analyzed",
            "last_analysis_timestamp": datetime.now().isoformat(),
        }

        # ✅ NOW check for active follow-ups (AFTER creating state_updates)
        supplier_id = state.get('top_suppliers', [{}])[0].get('supplier_id')
        active_follow_up = get_active_follow_up_schedule(supplier_id)
        
        if active_follow_up:
            logger.info(f"Active follow-up detected for supplier {supplier_id}: {active_follow_up['schedule_id']}")
            logger.info(f"Original delay reason: {active_follow_up['delay_reason']}")
            logger.info(f"Follow-ups sent: {active_follow_up['follow_ups_sent']}")
            
            # Update follow-up based on new response
            update_follow_up_on_response(
                active_follow_up['schedule_id'],
                supplier_intent.intent
            )
            
            # ✅ Now we can safely add to state_updates
            state_updates['is_follow_up_response'] = True
            state_updates['follow_up_schedule_id'] = active_follow_up['schedule_id']
        
        # Add risk alerts if significant risks identified
        if strategic_analysis.risk_factors:
            state_updates["risk_alerts"] = strategic_analysis.risk_factors
            state_updates["requires_attention"] = True
        
        # Add opportunities for follow-up
        if strategic_analysis.opportunities:
            state_updates["identified_opportunities"] = strategic_analysis.opportunities
        
        return state_updates
    
    except Exception as e:
        error_message = f"Error analyzing supplier response: {str(e)}"
        logger.error(error_message)
        import traceback
        traceback.print_exc()
        
        return {
            "error": str(e),
            "messages": [error_message],
            "next_step": "handle_error",
            "status": "analysis_error"
        }
    
def classify_response_type(intent: str) -> str:
    """Map supplier intent to response type"""
    mapping = {
        'accept': 'positive',
        'counteroffer': 'positive',
        'delay': 'partial',
        'reject': 'negative',
        'clarification_request': 'partial'
    }
    return mapping.get(intent, 'partial')

def determine_buyer_priorities(original_request: Dict[str, Any]) -> str:
    """Determine buyer's priorities from original request"""
    
    urgency = original_request.get('urgency_level', 'medium')
    price_constraints = original_request.get('price_constraints', {})
    logistics = original_request.get('logistics_details', {})
    
    priorities = []
    
    if urgency in ['high', 'urgent']:
        priorities.append('speed')
    
    if price_constraints.get('max_price'):
        priorities.append('cost')
    
    if logistics.get('timeline_days') and logistics['timeline_days'] < 30:
        priorities.append('delivery_speed')
    
    if not priorities:
        priorities = ['balanced_approach']
    
    return ', '.join(priorities)

def generate_analysis_summary(
    intent: SupplierIntent, 
    terms: Optional[ExtractedTerms], 
    analysis: NegotiationAnalysis, 
    round_number: int
) -> str:
    """Generate human-readable summary of the analysis"""
    
    summary_parts = [
        f"🔍 **Supplier Response Analysis (Round {round_number})**\n",
        f"**Intent**: {intent.intent.upper()} (confidence: {intent.confidence:.2f})",
        f"**Sentiment**: {intent.sentiment.capitalize()}\n"
    ]
    
    if terms and intent.intent == "counteroffer":
        summary_parts.append("**New Terms Offered**:")
        if terms.new_price:
            summary_parts.append(f"• Price: {terms.new_price} {terms.price_currency or ''}/{terms.price_unit or 'unit'}")
        if terms.new_lead_time:
            summary_parts.append(f"• Lead time: {terms.new_lead_time} days")
        if terms.new_minimum_quantity:
            summary_parts.append(f"• MOQ: {terms.new_minimum_quantity}")
        if terms.concessions_offered:
            summary_parts.append(f"• Concessions: {', '.join(terms.concessions_offered)}")
        summary_parts.append("")
    
    summary_parts.extend([
        f"**Strategic Assessment**: {analysis.strategic_assessment}\n",
        f"**Market Analysis**: {analysis.market_comparison}\n",
        f"**Recommended Response**: {analysis.recommended_response}"
    ])
    
    if analysis.risk_factors:
        summary_parts.append(f"\n⚠️ **Risks**: {', '.join(analysis.risk_factors[:2])}")
    
    if analysis.opportunities:
        summary_parts.append(f"✅ **Opportunities**: {', '.join(analysis.opportunities[:2])}")
    
    summary_parts.append(f"\n**Analysis Confidence**: {analysis.confidence_score:.2f}")
    
    return "\n".join(summary_parts)




def get_active_follow_up_schedule(supplier_id: str) -> Optional[Dict[str, Any]]:
    """Check if there's an active follow-up schedule for this supplier"""
    
    from database import SessionLocal, FollowUpSchedule as FollowUpScheduleDB
    from sqlalchemy import desc
    
    db = SessionLocal()
    
    try:
        schedule = db.query(FollowUpScheduleDB).filter(
            FollowUpScheduleDB.supplier_id == supplier_id,
            FollowUpScheduleDB.status == 'active'
        ).order_by(desc(FollowUpScheduleDB.created_at)).first()
        
        if schedule:
            return {
                'schedule_id': schedule.schedule_id,
                'delay_reason': schedule.delay_reason,
                'next_follow_up_date': schedule.next_follow_up_date.isoformat(),
                'follow_ups_sent': schedule.follow_ups_sent,
                'commitment_level': schedule.supplier_commitment_level
            }
        
        return None
        
    finally:
        db.close()


def update_follow_up_on_response(schedule_id: str, response_type: str):
    """Update follow-up schedule when supplier responds"""
    
    from database import SessionLocal, FollowUpSchedule as FollowUpScheduleDB, FollowUpMessage as FollowUpMessageDB
    from sqlalchemy import desc
    
    db = SessionLocal()
    
    try:
        schedule = db.query(FollowUpScheduleDB).filter(
            FollowUpScheduleDB.schedule_id == schedule_id
        ).first()
        
        if not schedule:
            return
        
        # Mark response received
        latest_message = db.query(FollowUpMessageDB).filter(
            FollowUpMessageDB.schedule_id == schedule_id,
            FollowUpMessageDB.status == 'sent'
        ).order_by(desc(FollowUpMessageDB.actual_send_date)).first()
        
        if latest_message:
            latest_message.response_received = True
        
        # Update schedule based on response type
        if response_type in ['accept', 'counteroffer']:
            # Positive response - cancel remaining follow-ups
            schedule.status = 'completed'
            
            pending_messages = db.query(FollowUpMessageDB).filter(
                FollowUpMessageDB.schedule_id == schedule_id,
                FollowUpMessageDB.status == 'pending'
            ).all()
            
            for msg in pending_messages:
                msg.status = 'cancelled'
            
            logger.info(f"Follow-up schedule completed - supplier responded positively")
        
        elif response_type == 'delay':
            # Still delaying - extend schedule
            schedule.next_follow_up_date = datetime.now() + timedelta(days=3)
            logger.info(f"Follow-up extended by 3 days")
        
        elif response_type == 'reject':
            # Rejection - cancel schedule
            schedule.status = 'cancelled'
            logger.info(f"Follow-up schedule cancelled - supplier rejected")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Error updating follow-up schedule: {str(e)}")
        db.rollback()
    finally:
        db.close()


def get_all_active_follow_ups() -> List[Dict[str, Any]]:
    """Get all active follow-up schedules (for dashboard/monitoring)"""
    
    from database import SessionLocal, FollowUpSchedule as FollowUpScheduleDB, FollowUpMessage as FollowUpMessageDB
    from sqlalchemy import func
    
    db = SessionLocal()
    
    try:
        schedules = db.query(
            FollowUpScheduleDB,
            func.count(FollowUpMessageDB.id).label('total_messages'),
            func.sum(
                func.case([(FollowUpMessageDB.status == 'sent', 1)], else_=0)
            ).label('sent_messages')
        ).outerjoin(
            FollowUpMessageDB, 
            FollowUpScheduleDB.schedule_id == FollowUpMessageDB.schedule_id
        ).filter(
            FollowUpScheduleDB.status == 'active'
        ).group_by(
            FollowUpScheduleDB.id
        ).all()
        
        results = []
        for schedule, total, sent in schedules:
            results.append({
                'schedule_id': schedule.schedule_id,
                'supplier_id': schedule.supplier_id,
                'delay_reason': schedule.delay_reason,
                'next_follow_up': schedule.next_follow_up_date.isoformat(),
                'commitment_level': schedule.supplier_commitment_level,
                'messages_sent': sent or 0,
                'messages_total': total or 0,
                'created_at': schedule.created_at.isoformat()
            })
        
        return results
        
    finally:
        db.close()
