from typing import Dict, Any, List, Optional, Tuple
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import re
from datetime import datetime
from loguru import logger

from state import AgentState
from models.message_validation_model import (
    MessageValidationResult,
    EnhancedMessage,
    AmbiguityIssue,
    MissingInformation,
    JargonTerm,
    ProactiveClarification
)

load_dotenv()

from utils.determining import determine_cultural_region

# Common industry jargon patterns
TEXTILE_JARGON = {
    'GSM': 'grams per square meter',
    'MOQ': 'Minimum Order Quantity',
    'FOB': 'Free On Board (shipping term)',
    'CIF': 'Cost, Insurance, and Freight',
    'CNF': 'Cost and Freight',
    'DDP': 'Delivered Duty Paid',
    'GOTS': 'Global Organic Textile Standard',
    'OEKO-TEX': 'textile safety certification',
    'BCI': 'Better Cotton Initiative',
    'L/C': 'Letter of Credit',
    'T/T': 'Telegraphic Transfer (wire payment)',
    'lead time': 'production and delivery time',
    'selvedge': 'self-finished edge of fabric',
    'warp': 'lengthwise yarn in fabric',
    'weft': 'crosswise yarn in fabric'
}


def create_validation_analysis_prompt():
    """Create prompt for comprehensive message validation"""
    
    system_prompt = """You are an expert B2B communication quality analyst specializing in textile industry negotiations. Your expertise includes:
- Technical specification clarity
- Commercial term completeness
- Cross-cultural business communication
- Supplier relationship management
- Risk identification in business communications

Your task is to perform a comprehensive quality analysis of a drafted negotiation message before it's sent to a supplier.

**VALIDATION FRAMEWORK:**

**1. CLARITY ANALYSIS (Ambiguity Detection):**

Check for ambiguous statements in these categories:

- **Specifications**: Vague fabric descriptions
  - Bad: "standard quality cotton"
  - Good: "cotton poplin, 120 GSM (grams per square meter), 80% cotton/20% polyester blend"

- **Pricing**: Missing currency, unit, or conditions
  - Bad: "around $5 per meter"
  - Good: "$5.00 USD per meter for quantities of 5,000+ meters"

- **Timeline**: Unclear dates or flexible phrasing
  - Bad: "as soon as possible" or "within a few weeks"
  - Good: "delivery required by March 15, 2025" or "45-day lead time from order confirmation"

- **Quantities**: Ambiguous units or ranges
  - Bad: "several thousand yards"
  - Good: "5,000 yards (4,572 meters)"

- **Quality Standards**: Undefined quality terms
  - Bad: "premium quality"
  - Good: "GOTS-certified organic, with third-party inspection reports"

**2. COMPLETENESS ANALYSIS (Missing Information):**

Critical fields that MUST be included:

**For Price Discussions:**
- Exact price with currency symbol (not just "USD")
- Price per unit clearly stated
- Quantity breakpoints if applicable
- Validity period

**For Timeline Discussions:**
- Specific dates or day counts
- What triggers the timeline (order date, payment date, etc.)
- Buffer/flexibility if any

**For Quantity Discussions:**
- Exact numbers (avoid "approximately")
- Unit of measurement
- Minimum/maximum if applicable

**For Commercial Terms:**
- Payment terms (Net 30, 50% advance, etc.)
- Incoterms (FOB, CIF, etc.)
- Currency for all financial terms

**3. JARGON ASSESSMENT:**

Industry terms that might need explanation based on:
- Supplier's location/cultural background
- Previous communication style
- Complexity of the term

Rules:
- Asian suppliers: Often need more technical explanations
- European suppliers: Familiar with ISO/technical standards
- First-time suppliers: Explain most acronyms
- Established relationships: Can use standard jargon

**4. CONTRADICTION DETECTION:**

Look for internal inconsistencies:
- Price mentioned twice with different values
- Conflicting timelines
- Quantity mismatches
- Terms that contradict previous messages

**5. PROACTIVE CLARIFICATION OPPORTUNITIES:**

Based on negotiation patterns, anticipate confusion:
- If mentioning price without specifying payment terms
- If discussing timeline without mentioning shipping method
- If changing previous terms without explaining why
- If introducing new requirements without context

**SCORING CRITERIA:**

**Clarity Score (0-1):**
- 1.0: Crystal clear, no ambiguity
- 0.8-0.9: Minor ambiguities that won't cause confusion
- 0.6-0.7: Some vague terms, but context helps
- 0.4-0.5: Multiple ambiguities, likely to cause follow-up questions
- 0.0-0.3: Very unclear, will definitely confuse supplier

**Completeness Score (0-1):**
- 1.0: All critical information included
- 0.8-0.9: Minor details missing but not critical
- 0.6-0.7: Some important info missing
- 0.4-0.5: Multiple critical gaps
- 0.0-0.3: Severely incomplete

**Overall Quality Score:**
Weighted average: (Clarity × 0.4) + (Completeness × 0.4) + (Professionalism × 0.2)

**DECISION RULES:**
- Score ≥ 0.8: send_as_is (minor improvements optional)
- Score 0.6-0.8: auto_enhance (fix automatically)
- Score 0.5-0.6: human_review_required (significant issues)
- Score < 0.5: major_revision_needed (critical problems)

Be thorough and precise in your analysis."""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Analyze this drafted negotiation message for quality and completeness:

**DRAFTED MESSAGE:**
{drafted_message}

**NEGOTIATION CONTEXT:**
- Supplier: {supplier_name} ({supplier_location})
- Cultural Region: {cultural_region}
- Negotiation Round: {negotiation_round}
- Previous Communication Style: {communication_style}

**ORIGINAL REQUEST CONTEXT:**
- Fabric Type: {fabric_type}
- Quantity: {quantity} {unit}
- Target Price: {target_price}
- Timeline: {timeline}
- Certifications Required: {certifications}

**PREVIOUS MESSAGE HISTORY:**
{message_history}

**CRITICAL CHECK:**
Does this message risk confusing the supplier or requiring follow-up clarifications?

Provide comprehensive validation analysis with specific issues and actionable recommendations.""")
    ])


def create_message_enhancement_prompt():
    """Create prompt for enhancing the message based on validation results"""
    
    system_prompt = """You are an expert B2B communication enhancer specializing in textile industry negotiations. Your job is to improve drafted messages by fixing issues identified in validation while maintaining the core message and tone.

**ENHANCEMENT PRINCIPLES:**

**1. CLARITY ENHANCEMENT:**
- Add specific numbers where vague terms exist
- Define ambiguous quality terms with industry standards
- Replace "approximately" with ranges (e.g., "45-50 days")
- Add units to all measurements

**2. COMPLETENESS ENHANCEMENT:**
- Add missing currencies, units, dates
- Include contextual information for new terms
- Add validity periods for offers
- Clarify conditions and dependencies

**3. PROACTIVE CLARIFICATION:**
- Add inline definitions for jargon (first use only)
- Include relevant examples when helpful
- Anticipate supplier questions and address them preemptively
- Add FAQ-style additions if complexity is high

**4. STRUCTURE OPTIMIZATION:**
- Use bullet points for multiple items
- Add headers for different topics (Pricing, Timeline, etc.)
- Highlight critical information with **bold** or CAPS
- Separate concerns into paragraphs

**5. CULTURAL ADAPTATION:**
- Asian suppliers: Add relationship language, be more formal
- European suppliers: Be process-oriented, include references
- Middle Eastern suppliers: Add personal touch, show respect
- American suppliers: Be direct and data-focused

**ENHANCEMENT CONSTRAINTS:**
- NEVER change the core negotiation stance or terms
- NEVER add information not available in context
- PRESERVE the original tone (assertive, collaborative, etc.)
- MAINTAIN the strategic approach
- Keep message length reasonable (under 300 words if possible)

**OUTPUT FORMAT:**
Provide the enhanced message ready to send, with clear formatting and all improvements integrated naturally.

Track all changes made so they can be reviewed."""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Enhance this message based on validation feedback:

**ORIGINAL MESSAGE:**
{original_message}

**VALIDATION ISSUES IDENTIFIED:**

Ambiguities Found:
{ambiguities}

Missing Information:
{missing_info}

Jargon Needing Explanation:
{jargon_terms}

Proactive Clarifications Recommended:
{proactive_clarifications}

**AVAILABLE CONTEXT TO ADD:**
{available_context}

**SUPPLIER PROFILE:**
- Company: {supplier_name}
- Location: {supplier_location}
- Cultural Region: {cultural_region}
- Communication Preference: {communication_style}

**ENHANCEMENT REQUIREMENTS:**
- Fix all critical and high-priority issues
- Add inline definitions for jargon
- Include proactive clarifications naturally
- Maintain professional tone and relationship-building language

Generate an enhanced version that eliminates confusion while keeping the core message intact.""")
    ])


# Initialize models and prompts
model = init_chat_model("google_genai:gemini-2.5-flash")
validation_model = model.with_structured_output(MessageValidationResult)
enhancement_model = model.with_structured_output(EnhancedMessage)

validation_prompt = create_validation_analysis_prompt()
enhancement_prompt = create_message_enhancement_prompt()

def extract_validation_context(state: AgentState) -> Dict[str, Any]:
    """Extract relevant context for message validation"""
    
    supplier_data = state.get('top_suppliers', [])

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
    
    # Get original request parameters
    extracted_params = state.get('extracted_parameters', {})
    fabric_details = extracted_params.get('fabric_details', {})
    logistics_details = extracted_params.get('logistics_details', {})
    price_constraints = extracted_params.get('price_constraints', {})
    
    # Get message history
    negotiation_history = state.get('negotiation_history', [])
    message_history = format_message_history(negotiation_history)

    logger.info("Extracted validation context successfully. in message_validator_node.py")
    
    return {
        'supplier_data': supplier_info,
        'fabric_details': fabric_details,
        'logistics_details': logistics_details,
        'price_constraints': price_constraints,
        'negotiation_history': negotiation_history,
        'message_history': message_history,
        'negotiation_round': state.get('negotiation_rounds', 0)
    }


def format_message_history(history: List[Dict[str, Any]]) -> str:
    """Format negotiation history for context"""
    
    if not history:
        return "No previous messages"
    
    formatted = []
    for i, entry in enumerate(history[-3:], 1):  # Last 3 exchanges
        formatted.append(f"Exchange {i}:")
        formatted.append(f"  Us: {entry.get('our_message', 'N/A')[:100]}...")
        formatted.append(f"  Supplier: {entry.get('supplier_response', 'N/A')[:100]}...")
    
    return "\n".join(formatted)

def detect_simple_jargon(message: str, supplier_location: str) -> List[JargonTerm]:
    """Simple jargon detection (before AI analysis)"""
    
    detected = []
    message_upper = message.upper()
    
    for term, explanation in TEXTILE_JARGON.items():
        if term.upper() in message_upper:
            # Check if already explained in message
            already_explained = f"({explanation})" in message.lower()
            
            detected.append(JargonTerm(
                term=term,
                explanation=explanation,
                should_add_definition=not already_explained,
                context_appropriateness=calculate_jargon_appropriateness(
                    term, supplier_location
                )
            ))
    logger.info(f"Detected {len(detected)} jargon terms in message.")
    
    return detected


def calculate_jargon_appropriateness(term: str, location: str) -> float:
    """Calculate how appropriate jargon is for this supplier"""
    
    location_lower = location.lower()
    
    # European/North American suppliers - more familiar with industry terms
    if any(region in location_lower for region in ['usa', 'uk', 'germany', 'france', 'italy', 'spain']):
        return 0.9  # Very appropriate
    
    # Asian suppliers - may need more explanation
    elif any(region in location_lower for region in ['china', 'india', 'bangladesh', 'vietnam']):
        return 0.6  # Somewhat appropriate, consider explaining
    
    # Others
    else:
        return 0.7
    

def prepare_available_context(state: AgentState) -> Dict[str, Any]:
    """Prepare contextual information that can be added to enhance the message"""
    
    extracted_params = state.get('extracted_parameters', {})
    
    return {
        'fabric_specs': {
            'type': extracted_params.get('fabric_details', {}).get('type'),
            'quality': extracted_params.get('fabric_details', {}).get('quality_specs', []),
            'certifications': extracted_params.get('fabric_details', {}).get('certifications', []),
            'composition': extracted_params.get('fabric_details', {}).get('composition')
        },
        'quantity_details': {
            'amount': extracted_params.get('fabric_details', {}).get('quantity'),
            'unit': extracted_params.get('fabric_details', {}).get('unit'),
            'flexibility': extracted_params.get('moq_flexibility', False)
        },
        'pricing_info': {
            'budget': extracted_params.get('price_constraints', {}).get('max_price'),
            'currency': extracted_params.get('price_constraints', {}).get('currency', 'USD'),
            'unit': extracted_params.get('price_constraints', {}).get('price_unit', 'per meter')
        },
        'timeline_info': {
            'required_date': extracted_params.get('logistics_details', {}).get('timeline'),
            'days': extracted_params.get('logistics_details', {}).get('timeline_days'),
            'urgency': extracted_params.get('urgency_level', 'medium'),
            'destination': extracted_params.get('logistics_details', {}).get('destination')
        },
        'commercial_terms': {
            'payment_terms': extracted_params.get('payment_terms'),
            'incoterms': 'FOB' if not extracted_params.get('incoterms') else extracted_params.get('incoterms')
        }
    }

def format_issues_for_enhancement(validation_result: MessageValidationResult) -> Dict[str, str]:
    """Format validation issues for the enhancement prompt"""

    logger.info("Formatting issues for message enhancement.")
    
    return {
        'ambiguities': "\n".join([
            f"- [{issue.severity.upper()}] {issue.location}: {issue.suggestion}"
            for issue in validation_result.ambiguities
        ]) or "None detected",
        
        'missing_info': "\n".join([
            f"- [{info.importance.upper()}] {info.missing_field}: {info.context}"
            + (f" (Available: {info.suggested_value})" if info.suggested_value else "")
            for info in validation_result.missing_information
        ]) or "None detected",
        
        'jargon_terms': "\n".join([
            f"- {term.term}: {term.explanation} ({'add definition' if term.should_add_definition else 'OK as-is'})"
            for term in validation_result.jargon_terms
        ]) or "None detected",
        
        'proactive_clarifications': "\n".join([
            f"- [Priority {clarif.priority}] {clarif.topic}: {clarif.suggested_addition}"
            for clarif in validation_result.proactive_clarifications
        ]) or "None recommended"
        
    }

def validate_and_enhance_message(state: AgentState):
    """
    Node: validate_and_enhance_message - Quality gate for negotiation messages
    
    Purpose:
    - Detect ambiguities and missing information in drafted messages
    - Identify industry jargon that needs explanation
    - Find contradictions with previous communications
    - Proactively add clarifications to prevent supplier confusion
    - Enhance message quality before sending
    - Flag critical issues for human review
    
    This node acts as a quality assurance checkpoint between message drafting
    and transmission to the supplier.
    
    Args:
        state: Current agent state with drafted message
    
    Returns:
        dict: State updates with validation results and enhanced message
    """
    
    try:

        logger.info("Starting message validation and enhancement process.")
        
        # Step 1: Extract drafted message and context
        drafted_message_data = state.get('drafted_message_data', {})
        
        if not drafted_message_data:
            return {
                "error": "No drafted message found to validate",
                "messages": ["No message to validate"],
                "status": "validation_error"
            }
        
        drafted_message_text = drafted_message_data.get('message_body', '')
        
        if not drafted_message_text:
            return {
                "error": "Drafted message is empty",
                "messages": ["Cannot validate empty message"],
                "status": "validation_error"
            }

        logger.info(f"Drafted message extracted for validation ({len(drafted_message_text)} characters).")
        
        # Step 2: Extract validation context
        context = extract_validation_context(state)
        supplier_data = context['supplier_data']
        
        # Step 3: Perform AI-powered validation analysis

        logger.info("Invoking validation model with drafted message and context.")
        
        validation_formatted_prompt = validation_prompt.invoke({
            "drafted_message": drafted_message_text,
            "supplier_name": supplier_data.get('name', 'Supplier'),
            "supplier_location": supplier_data.get('location', 'Unknown'),
            "cultural_region": determine_cultural_region(supplier_data.get('location', '')),
            "negotiation_round": context['negotiation_round'],
            "communication_style": supplier_data.get('communication_style', 'standard'),
            "fabric_type": context['fabric_details'].get('type', 'textile'),
            "quantity": context['fabric_details'].get('quantity', 'N/A'),
            "unit": context['fabric_details'].get('unit', 'units'),
            "target_price": context['price_constraints'].get('max_price', 'N/A'),
            "timeline": context['logistics_details'].get('timeline', 'standard'),
            "certifications": ", ".join(context['fabric_details'].get('certifications', [])) or "None",
            "message_history": context['message_history']
        })
        
        validation_result: MessageValidationResult = validation_model.invoke(
            validation_formatted_prompt
        )
        # Step 4: Log validation results

        logger.info(f"\n VALIDATION RESULTS: Overall Quality Score: {validation_result.overall_quality_score:.2f}, Recommended Action: {validation_result.recommended_action.upper()}, Critical Issues: {validation_result.critical_issues_count}, Clarity: {validation_result.clarity_score:.2f}, Completeness: {validation_result.completeness_score:.2f}, Professionalism: {validation_result.professionalism_score:.2f}")
        
        if validation_result.ambiguities:
            logger.info(f"Ambiguities detected: {len(validation_result.ambiguities)} and the details are {validation_result.ambiguities}")
        if validation_result.missing_information:
            logger.info(f"Missing information detected: {len(validation_result.missing_information)} and the details are {validation_result.missing_information}")
        if validation_result.contradictions:
            logger.info(f"Contradictions detected: {len(validation_result.contradictions)} and the details are {validation_result.contradictions}")
        
        # Step 5: Decide on action based on validation score
        if validation_result.overall_quality_score >= 0.8:
            logger.info("Message quality is excellent - ready to send as-is")
            
            return {
                "message_validation": validation_result.model_dump(),
                "validated_message": drafted_message_text,
                "validation_passed": True,
                "requires_human_review": False,
                "next_step": "send_negotiation_message",
                "messages": [
                    f"✅ Message validated successfully (Quality: {validation_result.overall_quality_score:.2f})"
                ],
                "status": "message_validated"
            }
        
        elif validation_result.recommended_action == "major_revision_needed":
            logger.warning("CRITICAL: Message needs major revision - flagging for human review")
            
            return {
                "message_validation": validation_result.model_dump(),
                "validated_message": None,
                "validation_passed": False,
                "requires_human_review": True,
                "validation_issues": {
                    "critical_issues": validation_result.critical_issues_count,
                    "ambiguities": len(validation_result.ambiguities),
                    "missing_info": len(validation_result.missing_information),
                    "contradictions": len(validation_result.contradictions)
                },
                "next_step": "request_human_review",
                "messages": [
                    f"🚨 Message validation failed (Score: {validation_result.overall_quality_score:.2f}). "
                    f"Critical issues found: {validation_result.critical_issues_count}. Human review required."
                ],
                "status": "validation_failed"
            }
        
        # Step 6: Auto-enhance the message
        logger.info("Auto-enhancing message to resolve issues...")
        
        # Prepare context for enhancement
        available_context = prepare_available_context(state)
        formatted_issues = format_issues_for_enhancement(validation_result)
        
        enhancement_formatted_prompt = enhancement_prompt.invoke({
            "original_message": drafted_message_text,
            "ambiguities": formatted_issues['ambiguities'],
            "missing_info": formatted_issues['missing_info'],
            "jargon_terms": formatted_issues['jargon_terms'],
            "proactive_clarifications": formatted_issues['proactive_clarifications'],
            "available_context": str(available_context),
            "supplier_name": supplier_data.get('name', 'Supplier'),
            "supplier_location": supplier_data.get('location', 'Unknown'),
            "cultural_region": determine_cultural_region(supplier_data.get('location', '')),
            "communication_style": supplier_data.get('communication_style', 'standard')
        })
        
        enhanced_result: EnhancedMessage = enhancement_model.invoke(
            enhancement_formatted_prompt
        )

        # Step 7: Display enhancement results
        logger.info(f"\n ENHANCEMENT COMPLETE:")
        logger.info(f"   Enhanced Message Length: {len(enhanced_result.enhanced_message)} characters")
        logger.info(f"   Removed Ambiguities: {len(enhanced_result.removed_ambiguities)}")
        logger.info(f"   Added Proactive Clarifications: {len(enhanced_result.added_clarifications)}")
        logger.info(f"   Improvement Summary: {enhanced_result.improvement_summary}")

        if enhanced_result.remaining_issues:
            logger.info(f"Remaining issues after enhancement: {len(enhanced_result.remaining_issues)} and the details are {enhanced_result.remaining_issues}")
        if enhanced_result.added_clarifications:
            logger.info(f"Added clarifications during enhancement: {len(enhanced_result.added_clarifications)} and the details are {enhanced_result.added_clarifications}")

        logger.info(f"   Quality Improvement: +{enhanced_result.quality_improvement:.2f}")
        logger.info(f"   Final Quality Score: {enhanced_result.final_quality_score:.2f}")
        logger.info(f"   Changes Made: {len(enhanced_result.changes_made)}")
        logger.info(f"   Ready to Send: {'Yes' if enhanced_result.ready_to_send else 'No'}")


        
        # Step 8: Create comprehensive assistant message
        assistant_message = f"""🔍 **Message Validation Complete**

**Original Quality Score:** {validation_result.overall_quality_score:.2f}/1.0
**Final Quality Score:** {enhanced_result.final_quality_score:.2f}/1.0
**Improvement:** +{enhanced_result.quality_improvement:.2f}

**Issues Resolved:**
✅ Ambiguities fixed: {len(enhanced_result.removed_ambiguities)}
✅ Clarifications added: {len(enhanced_result.added_clarifications)}
✅ Changes made: {len(enhanced_result.changes_made)}

**Enhancement Summary:**
{enhanced_result.improvement_summary}

**Status:** {'✅ Ready to send' if enhanced_result.ready_to_send else '⚠️ Needs review'}"""

        # Step 9: Determine next action
        if enhanced_result.ready_to_send:
            next_step = "send_negotiation_message"
            requires_review = False
            status = "message_enhanced_ready"
        elif validation_result.requires_human_review or enhanced_result.remaining_issues:
            next_step = "request_human_review"
            requires_review = True
            status = "message_enhanced_needs_review"
        else:
            next_step = "send_negotiation_message"
            requires_review = False
            status = "message_enhanced_ready"
        

        # Step 10: Update the drafted message in state
        updated_drafted_message_data = {
            **state.get('drafted_message_data', {}),
            'message_body': enhanced_result.enhanced_message
        }
        
        # Step 11: Prepare comprehensive state updates
        state_updates = {
            "message_validation": validation_result.model_dump(),
            "message_enhancement": enhanced_result.model_dump(),
            "drafted_message": enhanced_result.enhanced_message,  # Update with enhanced version
            "drafted_message_data": updated_drafted_message_data,
            "validated_message": enhanced_result.enhanced_message,
            "original_message": drafted_message_text,
            "validation_passed": True,
            "validation_score": enhanced_result.final_quality_score,
            "quality_improvement": enhanced_result.quality_improvement,
            "requires_human_review": requires_review,
            "next_step": next_step,
            "messages": [assistant_message],
            "status": status,
            "validation_timestamp": datetime.now().isoformat(),
            "enhancement_changes": enhanced_result.changes_made,
            "proactive_clarifications_added": enhanced_result.added_clarifications
        }
        
        # Add flags for special cases
        if enhanced_result.remaining_issues:
            state_updates["remaining_validation_issues"] = enhanced_result.remaining_issues
            state_updates["review_priority"] = "medium" if len(enhanced_result.remaining_issues) <= 2 else "high"
        
        if validation_result.critical_issues_count > 0:
            state_updates["had_critical_issues"] = True
            state_updates["critical_issues_resolved"] = validation_result.critical_issues_count
        
        return state_updates
        
    except Exception as e:
        error_message = f"Error in message validation: {str(e)}"
        logger.error(error_message)
        
        import traceback
        traceback.print_exc()
        
        return {
            "error": str(e),
            "messages": [error_message],
            "next_step": "handle_error",
            "status": "validation_error",
            "validation_passed": False
        }