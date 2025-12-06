from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState
from dotenv import load_dotenv
from models.notify_and_sugest_model import FailureAnalysis, NextStepsRecommendation, NegotiationAdjustment, AlternativeSupplier, MarketStrategy
import uuid
from loguru import logger

load_dotenv()


def create_failure_analysis_prompt():
    """Create prompt for analyzing negotiation failure"""
    
    system_prompt = """You are a senior B2B procurement strategist and negotiation specialist with deep expertise in textile industry supply chains. Your role is to analyze failed negotiations and provide strategic alternatives.

Your expertise includes:
- Root cause analysis of failed B2B negotiations
- Global supplier market dynamics and alternatives  
- Strategic procurement planning and risk mitigation
- Cross-cultural business relationship management
- Market timing and opportunity assessment

**FAILURE ANALYSIS FRAMEWORK:**

**1. Failure Categorization:**
- **price_mismatch**: Irreconcilable price differences, budget constraints
- **timeline_conflict**: Delivery schedule conflicts, lead time misalignment
- **quality_standards**: Quality/specification disagreements, certification issues
- **quantity_constraints**: MOQ conflicts, volume limitations
- **supplier_capacity**: Production capacity limits, resource constraints
- **market_conditions**: Market volatility, seasonal factors, supply shortages
- **relationship_issues**: Communication breakdowns, cultural misalignments
- **unknown**: Unclear reasons or multiple complex factors

**2. Root Cause Investigation:**
- Examine the complete negotiation history and identify inflection points
- Analyze supplier responses for underlying constraints and motivations  
- Consider external market pressures and competitive dynamics
- Identify missed opportunities or strategic missteps in the negotiation

**3. Constraint Analysis:**
- **Supplier Constraints**: Production limits, cost pressures, policy restrictions
- **Market Factors**: Raw material costs, seasonal demand, regulatory changes
- **Relationship Dynamics**: Communication issues, trust factors, cultural barriers

**4. Severity Assessment:**
- **Minor**: Easily resolvable with small adjustments
- **Moderate**: Requires strategic changes or alternative approaches  
- **Severe**: Fundamental incompatibility requiring complete strategy revision

Be thorough and objective in your analysis. Focus on actionable insights rather than blame assignment."""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Analyze this failed negotiation and identify root causes:

**NEGOTIATION CONTEXT:**
- Original Request: {original_request}
- Supplier: {supplier_name} ({supplier_location})
- Negotiation Rounds: {negotiation_rounds}
- Final Supplier Response: {final_response}
- Supplier Intent: {supplier_intent}

**NEGOTIATION HISTORY:**
{negotiation_history}

**MARKET CONTEXT:**
- Available Alternatives: {alternative_count} suppliers
- Market Conditions: {market_conditions}
- Urgency Level: {urgency_level}

**EXTRACTED PARAMETERS:**
- Budget Constraints: {budget_constraints}
- Timeline Requirements: {timeline_requirements}
- Quality Specifications: {quality_specs}

Provide comprehensive failure analysis identifying the primary failure category, root causes, constraints, and severity level.""")
    ])

def create_recommendations_prompt():
    """Create prompt for generating next steps recommendations"""
    
    system_prompt = """You are a strategic procurement consultant developing recovery strategies for failed B2B textile negotiations.

**OUTPUT REQUIREMENTS:**
Return these fields matching the exact structure:
- immediate_actions: 3-5 specific actions for next 24-48 hours
- short_term_strategies: 2-4 strategies for 1-2 weeks  
- long_term_approaches: 2-3 approaches for 1-3 months
- alternative_suppliers: Leave empty (already provided separately)
- negotiation_adjustments: Leave empty (already provided separately)
- market_strategies: 2-4 MarketStrategy objects
- budget_impact: Single sentence impact summary
- confidence_score: Float 0.0-1.0
- priority_ranking: Ordered list of top approaches

**MARKET STRATEGIES FORMAT:**
Each strategy needs:
- strategy_name: Concise title
- description: 2-3 sentence explanation
- timeline: Specific timeframe (e.g., "2-3 weeks", "Q2 2025")
- requirements: List of needed resources/actions
- success_likelihood: Must be "high", "medium", or "low"

**RULES:**
- Be specific and actionable, no vague terms
- Include concrete numbers and timeframes
- Prioritize by business impact and success probability
- DO NOT include failure_analysis field (provided separately)
- DO NOT populate alternative_suppliers or negotiation_adjustments (handled separately)"""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Generate next steps for this failed negotiation:

**FAILURE CONTEXT:**
Category: {failure_category} | Severity: {severity}
Root Causes: {root_causes}
Supplier Constraints: {supplier_constraints}
Market Factors: {market_factors}

**RESOURCES:**
Alternatives: {alternative_suppliers} | Budget: {budget_flexibility} | Timeline: {timeline_flexibility}

**BUSINESS CONTEXT:**
Request: {original_request}
Importance: {strategic_importance} | Impact: {stakeholder_impact}

**MARKET:**
Conditions: {market_conditions} | Seasonality: {seasonal_factors} | Competition: {competitive_landscape}

Provide structured recommendations. Leave alternative_suppliers and negotiation_adjustments empty.""")
    ])

# Initialize models and prompts
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
failure_analysis_model = model.with_structured_output(FailureAnalysis)

# Create a modified model for recommendations without failure_analysis field
class RecommendationsOnly(BaseModel):
    """Recommendations without failure analysis (which is added separately)"""
    immediate_actions: List[str] = Field(..., description="Actions to take immediately (within 24-48 hours)")
    short_term_strategies: List[str] = Field(..., description="Strategies for next 1-2 weeks")
    long_term_approaches: List[str] = Field(..., description="Long-term approaches for next 1-3 months")
    alternative_suppliers: List[AlternativeSupplier] = Field(default_factory=list, description="Recommended alternative suppliers")
    negotiation_adjustments: List[NegotiationAdjustment] = Field(default_factory=list, description="Adjustments to retry with same supplier")
    market_strategies: List[MarketStrategy] = Field(default_factory=list, description="Market-based strategies")  # CHANGED: Use MarketStrategy instead of Dict
    budget_impact: Optional[str] = Field(None, description="Expected impact on budget/timeline")
    confidence_score: float = Field(..., description="Confidence in recommendations 0-1", ge=0, le=1)
    priority_ranking: List[str] = Field(..., description="Priority ranking of recommended approaches")

recommendations_only_model = model.with_structured_output(RecommendationsOnly)

failure_analysis_prompt = create_failure_analysis_prompt()
recommendations_prompt = create_recommendations_prompt()

def extract_negotiation_context(state: AgentState):
    """Extract comprehensive context for failure analysis"""
    
    # Extract basic negotiation data
    supplier_intent_data = state.get('supplier_intent', {})
    negotiation_history = state.get('negotiation_history', [])
    top_suppliers = state.get('top_suppliers', [])
    extracted_params = state.get('extracted_parameters', {})
    
    # Get failed supplier info
    active_supplier = {}
    if top_suppliers:
        active_supplier = top_suppliers[0]
    
    # Extract original request details
    original_request = {
        'fabric_details': extracted_params.get('fabric_details', {}),
        'quantity': extracted_params.get('fabric_details', {}).get('quantity'),
        'budget_constraints': extracted_params.get('price_constraints', {}),
        'timeline_requirements': extracted_params.get('logistics_details', {}),
        'quality_specs': extracted_params.get('fabric_details', {}).get('quality_specs', [])
    }
    
    # Build negotiation summary
    negotiation_summary = []
    for entry in negotiation_history[-3:]:  # Last 3 rounds for context
        round_summary = f"Round {entry.get('round', '?')}: {entry.get('intent', 'unknown')} - {entry.get('supplier_response', '')[:100]}..."
        negotiation_summary.append(round_summary)
    
    return {
        'supplier_name': active_supplier.get('name', 'Unknown Supplier'),
        'supplier_location': active_supplier.get('location', 'Unknown'),
        'supplier_intent': supplier_intent_data.get('intent', 'unknown'),
        'final_response': state.get('supplier_response', '') or state.get('human_response', ''),
        'negotiation_rounds': len(negotiation_history),
        'negotiation_summary': '\n'.join(negotiation_summary),
        'alternative_count': len(top_suppliers) - 1,
        'original_request': original_request,
        'urgency_level': extracted_params.get('urgency_level', 'medium'),
        'market_analysis': state.get('market_analysis', {})
    }

def generate_alternative_suppliers(top_suppliers: List[Dict], failed_supplier_name: str) -> List[AlternativeSupplier]:
    """Generate alternative supplier recommendations from available options"""
    
    alternatives = []
    for supplier in top_suppliers:
        # Skip the failed supplier
        if supplier.get('name') == failed_supplier_name:
            continue
        
        # Create alternative supplier recommendation
        alternative = AlternativeSupplier(
            supplier_name=supplier.get('name', 'Unknown'),
            location=supplier.get('location', 'Unknown'),
            estimated_price=supplier.get('price_per_unit'),
            lead_time_days=supplier.get('lead_time_days'),
            reliability_score=supplier.get('reliability_score', 5.0),
            why_better=generate_supplier_advantage(supplier, failed_supplier_name),
            contact_priority=determine_contact_priority(supplier)
        )
        alternatives.append(alternative)
    
    return alternatives[:5]  # Return top 5 alternatives

def generate_supplier_advantage(supplier: Dict, failed_supplier: str) -> str:
    """Generate explanation of why alternative supplier might be better"""
    
    advantages = []
    
    if supplier.get('reliability_score', 0) > 7.5:
        advantages.append("higher reliability score")
    
    if supplier.get('lead_time_days', 999) < 45:
        advantages.append("faster delivery times")
    
    if supplier.get('price_per_unit', 999) < 10:  # Configurable threshold
        advantages.append("competitive pricing")
    
    location = supplier.get('location', '').lower()
    if any(region in location for region in ['local', 'domestic', 'nearby']):
        advantages.append("closer geographic proximity")
    
    if not advantages:
        advantages = ["alternative market positioning", "different production capabilities"]
    
    return f"Offers {', '.join(advantages)} compared to {failed_supplier}"

def determine_contact_priority(supplier: Dict) -> Literal["high", "medium", "low"]:
    """Determine contact priority for alternative supplier"""
    
    reliability = supplier.get('reliability_score', 5.0)
    price = supplier.get('price_per_unit', 999)
    lead_time = supplier.get('lead_time_days', 999)
    
    # High priority: High reliability + (good price OR fast delivery)
    if reliability >= 8.0 and (price < 15 or lead_time < 30):
        return "high"
    
    # Low priority: Low reliability OR very slow/expensive
    elif reliability < 6.0 or (price > 25 and lead_time > 60):
        return "low"
    
    # Medium priority: Everything else
    else:
        return "medium"

def generate_negotiation_adjustments(failure_analysis: FailureAnalysis, original_request: Dict) -> List[NegotiationAdjustment]:
    """Generate specific adjustment recommendations based on failure type"""
    
    adjustments = []
    
    if failure_analysis.failure_category == "price_mismatch":
        # Price-based adjustments
        current_budget = original_request.get('budget_constraints', {}).get('max_price', 'N/A')
        adjustments.append(NegotiationAdjustment(
            parameter="budget_flexibility",
            current_value=str(current_budget),
            suggested_value="Increase by 10-15% or offer volume commitments",
            rationale="Price mismatch often resolved with budget adjustment or future volume guarantees",
            success_probability=0.7
        ))
        
        adjustments.append(NegotiationAdjustment(
            parameter="payment_terms",
            current_value="Standard payment terms",
            suggested_value="Offer faster payment (Net 15) or partial advance",
            rationale="Improved cash flow can offset supplier's price concerns",
            success_probability=0.6
        ))
    
    elif failure_analysis.failure_category == "timeline_conflict":
        # Timeline-based adjustments
        current_timeline = original_request.get('timeline_requirements', {}).get('timeline', 'N/A')
        adjustments.append(NegotiationAdjustment(
            parameter="delivery_timeline",
            current_value=str(current_timeline),
            suggested_value="Extend timeline by 2-3 weeks",
            rationale="Additional time allows supplier to manage capacity and reduce rush charges",
            success_probability=0.8
        ))
    
    elif failure_analysis.failure_category == "quantity_constraints":
        # Quantity-based adjustments
        current_quantity = original_request.get('fabric_details', {}).get('quantity', 'N/A')
        adjustments.append(NegotiationAdjustment(
            parameter="order_quantity",
            current_value=str(current_quantity),
            suggested_value="Increase to meet supplier MOQ or split into phases",
            rationale="Meeting MOQ requirements or phased approach can unlock better terms",
            success_probability=0.75
        ))
    
    return adjustments

def create_user_notification_message(
    failure_analysis: FailureAnalysis, 
    recommendations: NextStepsRecommendation, 
    context: Dict[str, Any]
) -> str:
    """Create comprehensive user notification message"""
    
    notification_parts = [
        "🔴 **Negotiation Outcome: Unsuccessful**\n",
        f"**Supplier**: {context['supplier_name']} ({context['supplier_location']})",
        f"**Negotiation Rounds**: {context['negotiation_rounds']}",
        f"**Final Response**: {failure_analysis.failure_category.replace('_', ' ').title()}\n"
    ]
    
    # Failure Analysis Summary
    notification_parts.extend([
        "📊 **Failure Analysis**:",
        f"**Primary Issue**: {failure_analysis.failure_category.replace('_', ' ').title()}",
        f"**Root Causes**: {', '.join(failure_analysis.root_causes[:3])}",
        f"**Severity**: {failure_analysis.severity.capitalize()}\n"
    ])
    
    # Immediate Actions
    if recommendations.immediate_actions:
        notification_parts.extend([
            "⚡ **Immediate Actions (Next 24-48 hours)**:",
            *[f"• {action}" for action in recommendations.immediate_actions[:3]],
            ""
        ])
    
    # Alternative Suppliers
    if recommendations.alternative_suppliers:
        notification_parts.extend([
            "🏭 **Alternative Suppliers Available**:",
            f"**{len(recommendations.alternative_suppliers)} suppliers identified** - Top recommendations:"
        ])
        
        for supplier in recommendations.alternative_suppliers[:3]:
            price_info = f" (${supplier.estimated_price}/unit)" if supplier.estimated_price else ""
            notification_parts.append(
                f"• **{supplier.supplier_name}** ({supplier.location}){price_info} - {supplier.why_better}"
            )
        notification_parts.append("")
    
    # Strategic Recommendations
    notification_parts.extend([
        "🎯 **Recommended Strategy**:",
        f"**Top Priority**: {recommendations.priority_ranking[0] if recommendations.priority_ranking else 'Contact alternative suppliers'}",
        f"**Success Confidence**: {recommendations.confidence_score:.1%}",
        f"**Timeline Impact**: {recommendations.budget_impact or 'Minimal delay expected'}\n"
    ])
    
    # Next Steps Summary
    notification_parts.extend([
        "📋 **Your Options**:",
        "1. **Proceed with alternatives** - Contact recommended suppliers immediately",
        "2. **Adjust requirements** - Modify terms and retry with same supplier", 
        "3. **Strategic pivot** - Explore market-based strategies and timing",
        "\n*Detailed recommendations and supplier contacts available in the full analysis.*"
    ])
    
    return "\n".join(notification_parts)

def determine_strategic_importance(extracted_params: Dict, urgency_level: str) -> str:
    """Determine strategic importance based on project parameters"""
    quantity = extracted_params.get('fabric_details', {}).get('quantity', 0)
    certifications = extracted_params.get('fabric_details', {}).get('certifications', [])
    
    if urgency_level == "urgent" or quantity > 50000:
        return "Critical"
    elif certifications or quantity > 10000:
        return "High"
    else:
        return "Medium"

def determine_stakeholder_impact(urgency_level: str, negotiation_rounds: int) -> str:
    """Determine stakeholder impact based on negotiation context"""
    if urgency_level == "urgent":
        return "High - urgent timeline at risk"
    elif negotiation_rounds > 3:
        return "Moderate - extended negotiations causing delays"
    else:
        return "Low - manageable delay"

def notify_user_and_suggest_next_steps(state: AgentState) -> dict:
    """
    Node 8: notify_user_and_suggest_next_steps - Strategic failure recovery and alternatives engine
    
    Purpose:
    - Analyze failed negotiation to identify root causes and constraints
    - Generate comprehensive alternative strategies and supplier recommendations  
    - Provide immediate, short-term, and long-term action plans
    - Transform negotiation failure into strategic opportunity with clear next steps
    - Maintain user confidence with professional failure handling and viable alternatives
    
    Args:
        state: Current agent state containing failed negotiation context and history
    
    Returns:
        dict: State updates with failure analysis, recommendations, and user notification
    """
    
    try:
        print("\n" + "="*70)
        logger.info("NEGOTIATION FAILURE ANALYSIS & NEXT STEPS")
        print("="*70)
        
        # Step 1: Extract comprehensive negotiation context
        context = extract_negotiation_context(state)
        
        if not context.get('supplier_intent') or context['supplier_intent'] == 'unknown':
            return {
                "messages": ["Unable to analyze negotiation failure - insufficient context"],
                "status": "analysis_error",
                "next_step": "handle_error"
            }
        
        logger.info(f"Context extracted:")
        logger.info(f"   Supplier: {context['supplier_name']}")
        logger.info(f"   Rounds: {context['negotiation_rounds']}")
        logger.info(f"   Final intent: {context['supplier_intent']}")
        
        # Step 2: Perform failure analysis
        logger.info("Analyzing failure root causes...")
        
        failure_analysis_formatted_prompt = failure_analysis_prompt.invoke({
            "original_request": str(context['original_request']),
            "supplier_name": context['supplier_name'],
            "supplier_location": context['supplier_location'],
            "negotiation_rounds": context['negotiation_rounds'],
            "final_response": context['final_response'][:500],  # Truncate for prompt
            "supplier_intent": context['supplier_intent'],
            "negotiation_history": context['negotiation_summary'],
            "alternative_count": context['alternative_count'],
            "market_conditions": str(context['market_analysis']),
            "urgency_level": context['urgency_level'],
            "budget_constraints": str(context['original_request'].get('budget_constraints', {})),
            "timeline_requirements": str(context['original_request'].get('timeline_requirements', {})),
            "quality_specs": str(context['original_request'].get('quality_specs', []))
        })
        
        failure_analysis: FailureAnalysis = failure_analysis_model.invoke(failure_analysis_formatted_prompt)
        
        logger.info(f"   Failure category: {failure_analysis.failure_category}")
        logger.info(f"   Severity: {failure_analysis.severity}")
        logger.info(f"   Root causes: {len(failure_analysis.root_causes)}")
        
        # Step 3: Generate alternative suppliers and adjustments
        logger.info("Generating alternative suppliers...")
        
        top_suppliers = state.get('top_suppliers', [])
        alternative_suppliers = generate_alternative_suppliers(top_suppliers, context['supplier_name'])
        negotiation_adjustments = generate_negotiation_adjustments(failure_analysis, context['original_request'])
        
        logger.success(f"   Found {len(alternative_suppliers)} alternative suppliers")
        logger.success(f"   Generated {len(negotiation_adjustments)} adjustment options")
        
        # Step 4: Check if we have alternatives or need to warn user
        if not alternative_suppliers and not negotiation_adjustments:
            logger.warning("\n   WARNING: No alternatives or adjustments available!")
        
        # Step 5: Develop comprehensive recommendations
        logger.info(" Developing strategic recommendations...")
        
        # Extract strategic importance and stakeholder impact
        extracted_params = state.get('extracted_parameters', {})
        strategic_importance = determine_strategic_importance(extracted_params, context['urgency_level'])
        stakeholder_impact = determine_stakeholder_impact(context['urgency_level'], context['negotiation_rounds'])
        
        recommendations_formatted_prompt = recommendations_prompt.invoke({
            "failure_category": failure_analysis.failure_category,
            "root_causes": ", ".join(failure_analysis.root_causes),
            "supplier_constraints": ", ".join(failure_analysis.supplier_constraints),
            "market_factors": ", ".join(failure_analysis.market_factors),
            "severity": failure_analysis.severity,
            "alternative_suppliers": f"{len(alternative_suppliers)} suppliers available" if alternative_suppliers else "No alternatives available",
            "budget_flexibility": determine_budget_flexibility(context['original_request']),
            "timeline_flexibility": determine_timeline_flexibility(context['urgency_level']),
            "decision_authority": state.get('decision_authority', 'Standard procurement authority'),
            "original_request": str(context['original_request']),
            "strategic_importance": strategic_importance,
            "stakeholder_impact": stakeholder_impact,
            "competitive_implications": "Standard market competition",
            "market_conditions": str(context['market_analysis']),
            "seasonal_factors": "Normal seasonal patterns",
            "competitive_landscape": f"{context['alternative_count']} alternative suppliers"
        })
        
        recommendations_only: RecommendationsOnly = recommendations_only_model.invoke(recommendations_formatted_prompt)
        
        # Step 6: Combine failure analysis with recommendations
        recommendations = NextStepsRecommendation(
            failure_analysis=failure_analysis,
            immediate_actions=recommendations_only.immediate_actions,
            short_term_strategies=recommendations_only.short_term_strategies,
            long_term_approaches=recommendations_only.long_term_approaches,
            alternative_suppliers=alternative_suppliers,  # Use our generated list
            negotiation_adjustments=negotiation_adjustments,  # Use our generated list
            market_strategies=recommendations_only.market_strategies,
            budget_impact=recommendations_only.budget_impact,
            confidence_score=recommendations_only.confidence_score,
            priority_ranking=recommendations_only.priority_ranking
        )
        
        logger.success(f"   Recommendations generated (confidence: {recommendations.confidence_score:.2f})")
        
        # Step 7: Create user notification message
        logger.info("Creating user notification...")
        
        notification_message = create_user_notification_message(failure_analysis, recommendations, context)
        
        # Step 8: Generate unique analysis ID for tracking
        analysis_id = f"analysis_{str(uuid.uuid4())[:8]}"
        
        # Step 9: Determine follow-up actions
        follow_up_actions = determine_follow_up_actions(failure_analysis, recommendations)
        
        logger.success(f"Analysis complete!")
        logger.info(f"   Next step: {follow_up_actions['primary_next_step']}")
        
        # Step 10: Prepare comprehensive state updates
        state_updates = {
            "failure_analysis": failure_analysis.model_dump(),
            "next_steps_recommendations": recommendations.model_dump(),
            "analysis_id": analysis_id,
            "alternative_suppliers_list": [supplier.model_dump() for supplier in alternative_suppliers],
            "recommended_adjustments": [adj.model_dump() for adj in negotiation_adjustments],
            "user_notification": notification_message,
            "messages": [notification_message],
            "status": "failure_analyzed_alternatives_provided",
            "next_step": follow_up_actions['primary_next_step'],
            "follow_up_required": follow_up_actions['requires_follow_up'],
            "priority_level": determine_priority_level(failure_analysis.severity, context['urgency_level']),
            "analysis_timestamp": datetime.now().isoformat(),
            "recommendations_confidence": recommendations.confidence_score
        }
        
        # Add escalation flags if needed
        if failure_analysis.severity == "severe" or recommendations.confidence_score < 0.6:
            state_updates["requires_human_review"] = True
            state_updates["escalation_reason"] = f"Severe failure ({failure_analysis.severity}) or low confidence ({recommendations.confidence_score:.2f})"
        
        return state_updates
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error in failure analysis:\n{error_details}")
        
        error_message = f"Error in failure analysis and recommendations: {str(e)}"
        return {
            "error": str(e),
            "messages": [error_message],  # FIXED: was "messages1"
            "next_step": "handle_error",
            "status": "notification_error"
        }

def determine_budget_flexibility(original_request: Dict) -> str:
    """Determine budget flexibility from original constraints"""
    
    budget_constraints = original_request.get('budget_constraints', {})
    max_price = budget_constraints.get('max_price')
    
    if not max_price:
        return "High flexibility - no strict budget constraints"
    elif isinstance(max_price, (int, float)) and max_price > 20:
        return "Moderate flexibility - some room for adjustment"
    else:
        return "Limited flexibility - tight budget constraints"

def determine_timeline_flexibility(urgency_level: str) -> str:
    """Determine timeline flexibility from urgency level"""
    
    flexibility_mapping = {
        "urgent": "Very limited - urgent timeline",
        "high": "Limited - tight schedule", 
        "medium": "Moderate - some flexibility available",
        "low": "High - flexible timeline"
    }
    
    return flexibility_mapping.get(urgency_level, "Moderate - some flexibility available")

def determine_follow_up_actions(failure_analysis: FailureAnalysis, recommendations: NextStepsRecommendation) -> Dict[str, Any]:
    """Determine appropriate follow-up actions based on analysis"""
    
    if failure_analysis.severity == "severe":
        return {
            "primary_next_step": "escalate_to_human",
            "requires_follow_up": True,
            "urgency": "high"
        }
    elif len(recommendations.alternative_suppliers) > 0:
        return {
            "primary_next_step": "contact_alternative_suppliers",
            "requires_follow_up": True,
            "urgency": "medium"
        }
    elif len(recommendations.negotiation_adjustments) > 0:
        return {
            "primary_next_step": "retry_with_adjustments",
            "requires_follow_up": True,
            "urgency": "medium"
        }
    else:
        return {
            "primary_next_step": "strategic_review",
            "requires_follow_up": True,
            "urgency": "low"
        }

def determine_priority_level(severity: str, urgency: str) -> str:
    """Determine overall priority level for follow-up"""
    
    if severity == "severe" or urgency == "urgent":
        return "critical"
    elif severity == "moderate" or urgency == "high":
        return "high"
    else:
        return "medium"

def validate_recommendations_quality(recommendations: NextStepsRecommendation) -> tuple[bool, List[str]]:
    """Validate the quality and completeness of recommendations"""
    
    issues = []
    
    # Check completeness
    if not recommendations.immediate_actions:
        issues.append("No immediate actions provided")
    
    if not recommendations.short_term_strategies:
        issues.append("No short-term strategies provided")
    
    if not recommendations.priority_ranking:
        issues.append("No priority ranking provided")
    
    # Check confidence level
    if recommendations.confidence_score < 0.5:
        issues.append("Low confidence in recommendations")
    
    # Check for specific, actionable content
    vague_terms = ["consider", "maybe", "possibly", "might want to"]
    for action in recommendations.immediate_actions[:3]:
        if any(term in action.lower() for term in vague_terms):
            issues.append("Actions are too vague or non-specific")
            break
    
    is_valid = len(issues) == 0
    return is_valid, issues

# Utility function for debugging and monitoring
def log_failure_analysis_metrics(state: AgentState, failure_analysis: FailureAnalysis, recommendations: NextStepsRecommendation) -> None:
    """Log metrics about failure analysis for monitoring and improvement"""
    
    metrics = {
        "failure_category": failure_analysis.failure_category,
        "severity": failure_analysis.severity,
        "root_causes_count": len(failure_analysis.root_causes),
        "alternative_suppliers_count": len(recommendations.alternative_suppliers),
        "adjustments_count": len(recommendations.negotiation_adjustments),
        "recommendations_confidence": recommendations.confidence_score,
        "negotiation_rounds": len(state.get('negotiation_history', [])),
        "urgency_level": state.get('extracted_parameters', {}).get('urgency_level', 'unknown')
    }
    
    logger.info(f"Failure Analysis Metrics: {metrics}")