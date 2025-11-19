from typing import Dict, Any, List, Optional
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import uuid
from datetime import datetime

from state import AgentState
from models.clarification_models import (
    ClarificationClassification,
    HistoricalContextResult,
    InformationValidation,
    ClarificationResponse,
    ClarificationQualityValidation,
    EnhancedClarificationResponse
)

load_dotenv()

# Initialize model
model = init_chat_model("google_genai:gemini-2.5-flash")


# ===== 1. CLASSIFICATION PROMPT - BALANCED =====

def create_classification_prompt():
    """Classify clarification with strategic context"""
    
    system_prompt = """You're analyzing supplier clarification requests in B2B textile negotiations.

**Goal:** Deeply understand supplier confusion to craft the perfect response.

**Key Focus Areas:**
• Root cause analysis (our message unclear? jargon? missing info? cultural gap?)
• Urgency vs deal impact assessment
• Circular confusion detection (asking same thing repeatedly = red flag)
• Engagement signals (frustrated? interested? losing patience?)

**Decision Priority:**
Critical questions that block deal > High-priority terms > General info requests

Output structured using ClarificationClassification schema."""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """**SUPPLIER MESSAGE:**
{supplier_message}

**CONTEXT:**
Round: {negotiation_round} | Supplier: {supplier_name} ({supplier_location})
Previous clarifications: {previous_clarifications}

**OUR LAST MESSAGE:**
{our_last_message}

**COMMUNICATION HISTORY:**
{communication_history}

**DEAL CONTEXT:**
Fabric: {fabric_type} | Quantity: {quantity} | Budget: {budget} | Timeline: {timeline}

Classify comprehensively with strategic insight.""")
    ])

classification_prompt = create_classification_prompt()
classification_model = model.with_structured_output(ClarificationClassification)


def classify_clarification_request(state: AgentState) -> Dict[str, Any]:
    """
    STEP 1: Classify the clarification request
    
    Purpose:
    - Deeply understand what supplier is confused about
    - Identify root causes of confusion
    - Assess urgency and deal impact
    - Detect circular confusion patterns
    - Determine best response strategy
    """
    
    try:
        print("\n" + "="*70)
        print("🔍 STEP 1: CLASSIFYING CLARIFICATION REQUEST")
        print("="*70)
        
        # Extract supplier message
        supplier_message = state.get('supplier_response') or state.get('human_response')
        
        if not supplier_message:
            return {
                "error": "No supplier message to classify",
                "status": "classification_error"
            }
        
        # Extract context
        extracted_params = state.get('extracted_parameters', {})
        supplier_data = state.get('top_suppliers', [{}])[0]
        negotiation_history = state.get('negotiation_history', [])
        
        # Count previous clarifications on similar topics
        previous_clarifications = len([
            h for h in negotiation_history 
            if h.get('type') == 'clarification_request'
        ])
        
        # Format history
        comm_history = format_communication_history(negotiation_history[-3:])
        
        # Invoke classification
        formatted_prompt = classification_prompt.invoke({
            "supplier_message": supplier_message,
            "negotiation_round": state.get('negotiation_rounds', 0),
            "supplier_name": supplier_data.get('name', 'Supplier'),
            "supplier_location": supplier_data.get('location', 'Unknown'),
            "previous_clarifications": previous_clarifications,
            "our_last_message": state.get('drafted_message', 'Initial outreach'),
            "communication_history": comm_history,
            "fabric_type": extracted_params.get('fabric_details', {}).get('type', 'N/A'),
            "quantity": extracted_params.get('fabric_details', {}).get('quantity', 'N/A'),
            "budget": extracted_params.get('price_constraints', {}).get('max_price', 'N/A'),
            "timeline": extracted_params.get('logistics_details', {}).get('timeline', 'N/A')
        })
        
        classification: ClarificationClassification = classification_model.invoke(formatted_prompt)
        
        # Display results
        print(f"\n📊 CLASSIFICATION RESULTS:")
        print(f"   Request Type: {classification.request_type}")
        print(f"   Questions Identified: {len(classification.questions)}")
        print(f"   Supplier Confusion Level: {classification.supplier_confusion_level.upper()}")
        print(f"   Root Cause: {classification.root_cause_analysis[:80]}...")
        print(f"   Urgency: {classification.urgency_level.upper()}")
        print(f"   Deal Impact: {classification.deal_impact}")
        print(f"   Supplier Engagement: {classification.supplier_engagement_signal}")
        
        if classification.is_circular_confusion:
            print(f"   ⚠️  CIRCULAR CONFUSION DETECTED!")
        
        if classification.escalation_recommended:
            print(f"   🚨 ESCALATION RECOMMENDED")
        
        return {
            "clarification_classification": classification.model_dump(),
            "clarification_questions": [q.model_dump() for q in classification.questions],
            "confusion_level": classification.supplier_confusion_level,
            "is_circular_confusion": classification.is_circular_confusion,
            "escalation_needed": classification.escalation_recommended,
            "status": "classified"
        }
        
    except Exception as e:
        print(f"\n❌ Classification Error: {str(e)}")
        return {
            "error": str(e),
            "status": "classification_error"
        }


# ===== 2. HISTORICAL SEARCH PROMPT - BALANCED =====

def create_historical_search_prompt():
    """Search history with pattern recognition"""
    
    system_prompt = """Search negotiation history for relevant context and patterns.

**Your Task:**
• Find semantic matches (not just exact words) to current questions
• Detect if our terms evolved (price changed? timeline shifted?)
• Identify behavioral patterns (supplier asks same topic repeatedly?)
• Recommend strategy based on what you find

**Pattern Recognition:**
If supplier asked this 2+ times → Circular confusion (change communication approach)
If terms evolved significantly → Must explain what changed and why

Output using HistoricalContextResult schema."""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """**CURRENT QUESTIONS:**
{current_questions}

**COMPLETE NEGOTIATION HISTORY:**
{full_history}

**TERMS COMPARISON:**
Original: {original_terms}
Current: {current_terms}

Analyze thoroughly for matches, evolution, and patterns.""")
    ])


historical_search_prompt = create_historical_search_prompt()
historical_search_model = model.with_structured_output(HistoricalContextResult)


def search_historical_context(state: AgentState) -> Dict[str, Any]:
    """
    STEP 2: Search historical context for previous answers
    
    Purpose:
    - Find if we've answered this before
    - Detect if our terms have evolved
    - Identify circular confusion patterns
    - Provide strategic recommendations
    """
    
    try:
        print("\n" + "="*70)
        print("🔍 STEP 2: SEARCHING HISTORICAL CONTEXT")
        print("="*70)
        
        classification = state.get('clarification_classification', {})
        questions = classification.get('questions', [])
        
        if not questions:
            print("   No questions to search for")
            return {"historical_context": None}
        
        # Format questions for search
        current_questions_text = "\n".join([
            f"{i+1}. {q.get('question_text')}" 
            for i, q in enumerate(questions)
        ])
        
        # Get full history
        full_history = format_full_negotiation_history(
            state.get('negotiation_history', [])
        )
        
        # Get original vs current terms
        extracted_params = state.get('extracted_parameters', {})
        original_terms = format_terms(extracted_params)
        current_terms = format_terms(extracted_params)  # In real system, track evolution
        
        # Invoke search
        formatted_prompt = historical_search_prompt.invoke({
            "current_questions": current_questions_text,
            "full_history": full_history,
            "original_terms": original_terms,
            "current_terms": current_terms
        })
        
        history_result: HistoricalContextResult = historical_search_model.invoke(formatted_prompt)
        
        # Display results
        print(f"\n📚 HISTORICAL CONTEXT RESULTS:")
        print(f"   Found Previous Answers: {history_result.found_previous_answers}")
        
        if history_result.found_previous_answers:
            print(f"   Previous Answers Found: {len(history_result.previous_answers)}")
            for i, ans in enumerate(history_result.previous_answers[:3], 1):
                print(f"      {i}. Round {ans.negotiation_round}: {ans.original_question[:50]}...")
                print(f"         Relevance: {ans.relevance_score:.2f}")
        
        if history_result.information_evolved:
            print(f"   ⚠️  INFORMATION EVOLVED: {history_result.evolution_details}")
        
        print(f"   Pattern: {history_result.supplier_behavior_pattern}")
        print(f"   Recommendation: {history_result.recommendation[:80]}...")
        
        return {
            "historical_context": history_result.model_dump(),
            "found_previous_answers": history_result.found_previous_answers,
            "information_evolved": history_result.information_evolved,
            "status": "history_searched"
        }
        
    except Exception as e:
        print(f"\n❌ Historical Search Error: {str(e)}")
        return {
            "error": str(e),
            "historical_context": None
        }


"""
BALANCED PROMPTS - Optimal token efficiency with strategic guidance
- Remove redundant explanations (trust Pydantic)
- Keep strategic framing and quality standards
- Preserve domain expertise
- Include key decision criteria
"""

# ===== 3. INFORMATION VALIDATION PROMPT - BALANCED =====

def create_information_validation_prompt():
    """Validate info with consistency checks"""
    
    system_prompt = """Audit what information we can provide to answer supplier's questions.

**Validation Checklist:**
• Availability: Do we have the data they're asking for?
• Consistency: Does our info contradict itself? (price mismatch? timeline conflict?)
• Confidence: How certain are we? (explicit vs assumed vs missing)
• Criticality: What's blocking the deal vs nice-to-have?

**Key Decision:**
If missing critical info (price, MOQ, timeline) → Flag for user input
If have inconsistencies → Flag as needing resolution before response

Output using InformationValidation schema."""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """**SUPPLIER'S QUESTIONS:**
{questions}

**AVAILABLE INFORMATION:**
Extracted Parameters: {extracted_parameters}
Supplier Profile: {supplier_profile}
Previous Terms: {previous_terms}
Quote Info: {quote_info}

**OUR PREVIOUS MESSAGES:**
{our_previous_messages}

Cross-check for availability, consistency, and gaps.""")
    ])


information_validation_prompt = create_information_validation_prompt()
information_validation_model = model.with_structured_output(InformationValidation)

def get_conversation_history(history: List[Dict[str, Any]]) -> str:
    """Extract previous conversation exchanges between assistant and supplier"""
    messages = []
    
    for entry in history[-5:]:  # Last 5 rounds
        round_num = entry.get('round', '?')
        
        # Get assistant message
        assistant_msg = entry.get('assistant_message', '')
        if assistant_msg:
            messages.append(f"Round {round_num} - Us: {assistant_msg[:200]}...")
        
        # Get supplier response
        supplier_msg = entry.get('supplier_response', '')
        if supplier_msg:
            messages.append(f"Round {round_num} - Supplier: {supplier_msg[:200]}...")
    
    return "\n\n".join(messages) if messages else "No previous conversation"


def validate_available_information(state: AgentState) -> Dict[str, Any]:
    """
    STEP 3: Validate what information we have available
    
    Purpose:
    - Check what information we can provide
    - Identify missing critical information
    - Verify internal consistency
    - Recommend whether we can answer or need user input
    """
    
    try:
        print("\n" + "="*70)
        print("🔍 STEP 3: VALIDATING AVAILABLE INFORMATION")
        print("="*70)
        
        classification = state.get('clarification_classification', {})
        questions = classification.get('questions', [])
        
        # Format questions
        questions_text = "\n".join([
            f"{i+1}. [{q.get('question_type')}] {q.get('question_text')}"
            for i, q in enumerate(questions)
        ])
        
        # Gather all available information
        extracted_params = state.get('extracted_parameters', {})
        supplier_data = state.get('top_suppliers', [{}])[0]
        quote_data = state.get('generated_quote', {})
        previous_terms = state.get('extracted_terms', {})
        
        # Get our previous messages
        our_messages = get_conversation_history(state.get('negotiation_history', []))
        
        # Invoke validation
        formatted_prompt = information_validation_prompt.invoke({
            "questions": questions_text,
            "extracted_parameters": format_dict_for_prompt(extracted_params),
            "supplier_profile": format_dict_for_prompt(supplier_data),
            "previous_terms": format_dict_for_prompt(previous_terms),
            "quote_info": format_dict_for_prompt(quote_data) if quote_data else "No quote generated yet",
            "our_previous_messages": our_messages
        })
        
        validation: InformationValidation = information_validation_model.invoke(formatted_prompt)
        
        # Display results
        print(f"\n📋 INFORMATION VALIDATION RESULTS:")
        print(f"   Can Answer Completely: {'✅ Yes' if validation.can_answer_completely else '⚠️ No'}")
        print(f"   Completeness Score: {validation.completeness_score:.2f}")
        print(f"   Available Information: {len(validation.available_information)} items")
        print(f"   Missing Information: {len(validation.missing_information)} items")
        print(f"   Consistency Check: {'✅ Passed' if validation.consistency_check_passed else '❌ Failed'}")
        
        if validation.consistency_issues:
            print(f"   ⚠️ Consistency Issues:")
            for issue in validation.consistency_issues[:3]:
                print(f"      • {issue}")
        
        print(f"   Recommended Action: {validation.recommended_action.upper()}")
        
        # Show critical missing info
        critical_missing = [m for m in validation.missing_information if m.criticality == 'critical']
        if critical_missing:
            print(f"\n   🚨 CRITICAL MISSING INFO:")
            for item in critical_missing:
                print(f"      • {item.field_name}: {item.why_needed}")
        
        return {
            "information_validation": validation.model_dump(),
            "can_answer_completely": validation.can_answer_completely,
            "completeness_score": validation.completeness_score,
            "missing_critical_info": [m.model_dump() for m in critical_missing],
            "recommended_action": validation.recommended_action,
            "status": "information_validated"
        }
        
    except Exception as e:
        print(f"\n❌ Information Validation Error: {str(e)}")
        return {
            "error": str(e),
            "status": "validation_error"
        }


# ===== 4. RESPONSE GENERATION PROMPT - BALANCED =====

def create_response_generation_prompt():
    """Generate response with relationship focus"""
    
    system_prompt = """Craft comprehensive clarification response that eliminates confusion.

**Response Requirements:**
• Answer every question explicitly (no question left unaddressed)
• Zero ambiguity (all numbers with units, dates specific, terms defined)
• Proactive clarifications (anticipate follow-up questions)
• Concrete examples (especially for complex topics)
• Clear next steps (what happens after this)

**Communication Principles:**
• Asian suppliers: Formal, relationship-focused, indirect
• European suppliers: Process-oriented, detailed, references
• American suppliers: Direct, data-driven, efficient
• If supplier frustrated: Patient, empathetic tone

**Critical Rule:** If supplier asked this before, reference previous answer AND explain differently

Output using ClarificationResponse schema."""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """**CLASSIFIED QUESTIONS:**
{classified_questions}

**HISTORICAL CONTEXT:**
{historical_context}

**AVAILABLE INFORMATION:**
{available_information}

**MISSING INFORMATION:**
{missing_information}

**SUPPLIER PROFILE:**
{supplier_name} | {supplier_location} | Cultural Region: {cultural_region}
Confusion Level: {confusion_level} | Engagement: {engagement_signal}

**DEAL TERMS:**
{fabric_type} | {quantity} {unit} | {budget} {currency} | Timeline: {timeline}

**COMMUNICATION STRATEGY:**
Approach: {recommended_approach} | Tone: {tone}

**SPECIAL INSTRUCTIONS:**
{special_instructions}

Generate comprehensive, clear response.""")
    ])


response_generation_prompt = create_response_generation_prompt()
response_generation_model = model.with_structured_output(ClarificationResponse)


def generate_comprehensive_response(state: AgentState) -> Dict[str, Any]:
    """
    STEP 4: Generate comprehensive clarification response
    
    Purpose:
    - Create detailed, clear response to all questions
    - Add proactive clarifications
    - Include examples and context
    - Maintain relationship and professionalism
    """
    
    try:
        print("\n" + "="*70)
        print("✍️ STEP 4: GENERATING COMPREHENSIVE RESPONSE")
        print("="*70)
        
        # Gather all context
        classification = state.get('clarification_classification', {})
        historical_context = state.get('historical_context', {})
        info_validation = state.get('information_validation', {})
        
        # Check if we have critical missing info
        if state.get('recommended_action') == 'request_user_input':
            print("\n⚠️ CRITICAL INFO MISSING - Need user input before responding")
            return {
                "error": "Missing critical information - user input required",
                "status": "needs_user_input",
                "missing_info": state.get('missing_critical_info', [])
            }
        
        # Extract supplier and deal context
        supplier_data = state.get('top_suppliers', [{}])[0]
        extracted_params = state.get('extracted_parameters', {})
        fabric_details = extracted_params.get('fabric_details', {})
        
        # Format classified questions
        questions_formatted = format_classified_questions(classification.get('questions', []))
        
        # Format available/missing info
        available_info_text = format_available_information(
            info_validation.get('available_information', [])
        )
        missing_info_text = format_missing_information(
            info_validation.get('missing_information', [])
        )
        
        # Determine special instructions
        special_instructions = generate_special_instructions(state)
        
        # Cultural region
        cultural_region = determine_cultural_region(supplier_data.get('location', ''))
        
        # Invoke response generation
        formatted_prompt = response_generation_prompt.invoke({
            "classified_questions": questions_formatted,
            "historical_context": format_dict_for_prompt(historical_context),
            "available_information": available_info_text,
            "missing_information": missing_info_text,
            "supplier_name": supplier_data.get('name', 'Supplier'),
            "supplier_location": supplier_data.get('location', 'Unknown'),
            "cultural_region": cultural_region,
            "confusion_level": classification.get('supplier_confusion_level', 'medium'),
            "engagement_signal": classification.get('supplier_engagement_signal', 'interested'),
            "fabric_type": fabric_details.get('type', 'N/A'),
            "quantity": fabric_details.get('quantity', 'N/A'),
            "unit": fabric_details.get('unit', 'units'),
            "budget": extracted_params.get('price_constraints', {}).get('max_price', 'N/A'),
            "currency": extracted_params.get('price_constraints', {}).get('currency', 'USD'),
            "timeline": extracted_params.get('logistics_details', {}).get('timeline', 'N/A'),
            "recommended_approach": classification.get('recommended_response_approach', 'professional and detailed'),
            "tone": determine_response_tone(classification),
            "special_instructions": special_instructions
        })
        
        response: ClarificationResponse = response_generation_model.invoke(formatted_prompt)
        
        # Display results
        print(f"\n📝 RESPONSE GENERATED:")
        print(f"   Main Sections: {len(response.main_response_sections)}")
        print(f"   Proactive Additions: {len(response.proactive_additions)}")
        print(f"   Examples Provided: {len(response.examples_provided)}")
        print(f"   Clarity Score: {response.clarity_score:.2f}")
        print(f"   Completeness Score: {response.completeness_score:.2f}")
        print(f"   Confidence in Resolution: {response.confidence_in_resolution:.2f}")
        
        # Assemble full response text
        full_response_text = assemble_response_text(response)
        
        print(f"\n   Response Length: {len(full_response_text)} characters")
        print(f"   Estimated Reading Time: {response.estimated_reading_time}")
        
        return {
            "clarification_response": response.model_dump(),
            "drafted_clarification": full_response_text,
            "clarity_score": response.clarity_score,
            "completeness_score": response.completeness_score,
            "confidence_in_resolution": response.confidence_in_resolution,
            "status": "response_generated"
        }
        
    except Exception as e:
        print(f"\n❌ Response Generation Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "status": "generation_error"
        }


# ===== 5. QUALITY VALIDATION PROMPT - BALANCED =====

def create_quality_validation_prompt():
    """Quality gate with specific checks"""
    
    system_prompt = """Quality-check clarification response before sending.

**Validation Gates:**
1. Completeness: Every question answered? No gaps?
2. Clarity: Any vague terms? ("around", "soon", "good") = FAIL
3. Consistency: Matches previous messages? No contradictions?
4. Helpfulness: Includes examples? Clear next steps?

**Specific Checks:**
• All numbers have units (5000 meters ✓, "five thousand" ✗)
• All prices have currency ($4.50 USD ✓, "$4.50" ✗)
• All dates specific (March 15 ✓, "next month" ✗)
• Jargon defined on first use (120 GSM (grams per square meter) ✓)

**Action Thresholds:**
Score ≥ 0.85: Send as-is
Score 0.65-0.85: Auto-enhance
Score < 0.65: Human review

Output using ClarificationQualityValidation schema."""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """**ORIGINAL SUPPLIER QUESTIONS:**
{supplier_questions}

**DRAFTED CLARIFICATION RESPONSE:**
{drafted_response}

**CONSISTENCY CHECK DATA:**
Negotiation History: {negotiation_history}
Previous Terms: {previous_terms}

**VALIDATION REQUIREMENTS:**
• Must answer all {question_count} questions
• Must match history consistency
• Must have clear next steps
• Appropriate detail for {confusion_level} confusion
• Culturally appropriate for {supplier_location}

Validate thoroughly and identify all issues.""")
    ])



quality_validation_prompt = create_quality_validation_prompt()
quality_validation_model = model.with_structured_output(ClarificationQualityValidation)


def validate_clarification_quality(state: AgentState) -> Dict[str, Any]:
    """
    STEP 5: Validate clarification response quality
    
    Purpose:
    - Ensure all questions are answered
    - Check for ambiguities and inconsistencies
    - Verify appropriate detail level
    - Confirm clear next steps
    - Quality gate before sending
    """
    
    try:
        print("\n" + "="*70)
        print("🔍 STEP 5: VALIDATING CLARIFICATION QUALITY")
        print("="*70)
        
        # Get drafted response
        drafted_response = state.get('drafted_clarification', '')
        
        if not drafted_response:
            return {
                "error": "No drafted response to validate",
                "status": "validation_error"
            }
        
        # Get context
        classification = state.get('clarification_classification', {})
        questions = classification.get('questions', [])
        supplier_data = state.get('top_suppliers', [{}])[0]
        
        # Format questions for validation
        questions_text = "\n".join([
            f"{i+1}. {q.get('question_text')}"
            for i, q in enumerate(questions)
        ])
        
        # Get history for consistency check
        history_text = format_full_negotiation_history(
            state.get('negotiation_history', [])
        )
        
        # Previous terms
        previous_terms_text = format_dict_for_prompt(
            state.get('extracted_terms', {})
        )
        
        # Invoke validation
        formatted_prompt = quality_validation_prompt.invoke({
            "supplier_questions": questions_text,
            "drafted_response": drafted_response,
            "negotiation_history": history_text,
            "previous_terms": previous_terms_text,
            "question_count": len(questions),
            "confusion_level": classification.get('supplier_confusion_level', 'medium'),
            "supplier_location": supplier_data.get('location', 'Unknown')
        })
        
        validation: ClarificationQualityValidation = quality_validation_model.invoke(formatted_prompt)
        
        # Display results
        print(f"\n📊 QUALITY VALIDATION RESULTS:")
        print(f"   Overall Quality: {validation.overall_quality_score:.2f}")
        print(f"   - Clarity: {validation.clarity_score:.2f}")
        print(f"   - Completeness: {validation.completeness_score:.2f}")
        print(f"   - Consistency: {validation.consistency_score:.2f}")
        print(f"   - Helpfulness: {validation.helpfulness_score:.2f}")
        
        print(f"\n   All Questions Answered: {'✅ Yes' if validation.all_questions_answered else '❌ No'}")
        
        if validation.unanswered_questions:
            print(f"   ⚠️ Unanswered Questions:")
            for q in validation.unanswered_questions:
                print(f"      • {q}")
        
        print(f"   Consistency Check: {'✅ Passed' if validation.consistency_with_history else '❌ Failed'}")
        
        if validation.inconsistencies_found:
            print(f"   ⚠️ Inconsistencies:")
            for inc in validation.inconsistencies_found:
                print(f"      • {inc}")
        
        print(f"   Critical Issues: {validation.critical_issues_count}")
        print(f"   Ready to Send: {'✅ Yes' if validation.ready_to_send else '⚠️ No'}")
        print(f"   Recommended Action: {validation.recommended_action.upper()}")
        
        return {
            "clarification_quality_validation": validation.model_dump(),
            "quality_score": validation.overall_quality_score,
            "all_questions_answered": validation.all_questions_answered,
            "ready_to_send": validation.ready_to_send,
            "critical_issues": validation.critical_issues_count,
            "recommended_action": validation.recommended_action,
            "status": "quality_validated"
        }
        
    except Exception as e:
        print(f"\n❌ Quality Validation Error: {str(e)}")
        return {
            "error": str(e),
            "status": "quality_validation_error"
        }


# ===== 6. ENHANCEMENT PROMPT - BALANCED =====

def create_enhancement_prompt():
    """Enhance with constraints"""
    
    system_prompt = """Improve clarification response by fixing identified issues.

**Enhancement Focus:**
• Replace vague terms with specifics (add units, dates, values)
• Complete missing answers using available information
• Resolve inconsistencies with previous messages
• Add helpful examples where clarity needed
• Define jargon inline on first use

**Critical Constraints:**
• NEVER change factual data (prices, dates, terms must stay exact)
• NEVER alter core message or strategic approach
• PRESERVE professional tone and relationship language
• Keep response concise (under 500 words if possible)

Output using EnhancedClarificationResponse schema."""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """**ORIGINAL RESPONSE:**
{original_response}

**IDENTIFIED ISSUES:**
{quality_issues}

**UNANSWERED QUESTIONS:**
{unanswered_questions}

**INCONSISTENCIES:**
{inconsistencies}

**AVAILABLE INFORMATION TO ADD:**
{available_information}

Fix all critical/high issues while maintaining message integrity.""")
    ])


enhancement_prompt = create_enhancement_prompt()
enhancement_model = model.with_structured_output(EnhancedClarificationResponse)


def enhance_clarification_response(state: AgentState) -> Dict[str, Any]:
    """
    STEP 6: Enhance clarification response (if quality issues found)
    
    Purpose:
    - Fix ambiguities and gaps
    - Resolve inconsistencies
    - Add missing answers
    - Improve clarity and helpfulness
    """
    
    try:
        print("\n" + "="*70)
        print("🔧 STEP 6: ENHANCING CLARIFICATION RESPONSE")
        print("="*70)
        
        # Check if enhancement needed
        recommended_action = state.get('recommended_action', 'send_as_is')
        
        if recommended_action == 'send_as_is':
            print("   ✅ Quality excellent - no enhancement needed")
            return {
                "clarification_enhanced": False,
                "final_clarification": state.get('drafted_clarification'),
                "status": "ready_to_send"
            }
        
        if recommended_action in ['human_review_required', 'major_revision_needed']:
            print("   🚨 Quality issues too severe for auto-enhancement")
            print("   Escalating to human review")
            return {
                "clarification_enhanced": False,
                "requires_human_review": True,
                "status": "needs_human_review"
            }
        
        # Get original response and quality issues
        original_response = state.get('drafted_clarification', '')
        validation = state.get('clarification_quality_validation', {})
        info_validation = state.get('information_validation', {})
        
        # Format issues
        issues_text = format_quality_issues(validation.get('issues', []))
        unanswered = "\n".join(validation.get('unanswered_questions', []))
        inconsistencies = "\n".join(validation.get('inconsistencies_found', []))
        available_info = format_available_information(
            info_validation.get('available_information', [])
        )
        
        # Invoke enhancement
        formatted_prompt = enhancement_prompt.invoke({
            "original_response": original_response,
            "quality_issues": issues_text,
            "unanswered_questions": unanswered or "None",
            "inconsistencies": inconsistencies or "None",
            "available_information": available_info
        })
        
        enhanced: EnhancedClarificationResponse = enhancement_model.invoke(formatted_prompt)
        
        # Display results
        print(f"\n✨ ENHANCEMENT COMPLETE:")
        print(f"   Quality Improvement: +{enhanced.quality_improvement:.2f}")
        print(f"   Final Quality Score: {enhanced.final_quality_score:.2f}")
        print(f"   Improvements Made: {len(enhanced.improvements_made)}")
        print(f"   Elements Added: {len(enhanced.added_elements)}")
        print(f"   Ready to Send: {'✅ Yes' if enhanced.ready_to_send else '⚠️ No'}")
        
        if enhanced.remaining_concerns:
            print(f"\n   ⚠️ Remaining Concerns:")
            for concern in enhanced.remaining_concerns:
                print(f"      • {concern}")
        
        return {
            "clarification_enhancement": enhanced.model_dump(),
            "final_clarification": enhanced.enhanced_message,
            "quality_improvement": enhanced.quality_improvement,
            "final_quality_score": enhanced.final_quality_score,
            "clarification_enhanced": True,
            "ready_to_send": enhanced.ready_to_send,
            "status": "enhanced"
        }
        
    except Exception as e:
        print(f"\n❌ Enhancement Error: {str(e)}")
        return {
            "error": str(e),
            "status": "enhancement_error"
        }


# ===== MAIN ORCHESTRATOR =====

def handle_clarification_request(state: AgentState):
    """
    Main orchestrator for comprehensive clarification handling
    
    This node coordinates all 6 steps:
    1. Classify clarification request
    2. Search historical context
    3. Validate available information
    4. Generate comprehensive response
    5. Validate quality
    6. Enhance if needed
    
    Returns complete state with final clarification ready to send
    """
    
    try:
        print("\n" + "="*70)
        print("🎯 COMPREHENSIVE CLARIFICATION HANDLER")
        print("="*70)
        
        # Step 1: Classify
        result = classify_clarification_request(state)
        if result.get('error'):
            return result
        state.update(result)
        
        # Step 2: Search History
        result = search_historical_context(state)
        if result.get('error'):
            print("   ⚠️ Historical search failed, continuing without history...")
        state.update(result)
        
        # Step 3: Validate Information
        result = validate_available_information(state)
        if result.get('error'):
            return result
        state.update(result)
        
        # Check if we need user input
        if result.get('recommended_action') == 'request_user_input':
            print("\n🚨 Missing critical information - need user input")
            return {
                **state,
                "next_step": "request_user_input",
                "status": "needs_user_input"
            }
        
        # Step 4: Generate Response
        result = generate_comprehensive_response(state)
        if result.get('error'):
            return result
        state.update(result)
        
        # Step 5: Validate Quality
        result = validate_clarification_quality(state)
        if result.get('error'):
            return result
        state.update(result)
        
        # Step 6: Enhance if Needed
        result = enhance_clarification_response(state)
        if result.get('error'):
            return result
        state.update(result)
        
        # Check final status
        if result.get('requires_human_review'):
            print("\n" + "="*70)
            print("🚨 HUMAN REVIEW REQUIRED")
            print("="*70)
            return {
                **state,
                "next_step": "request_human_review",
                "status": "needs_human_review"
            }
        
        if not result.get('ready_to_send'):
            print("\n" + "="*70)
            print("⚠️ CLARIFICATION NOT READY")
            print("="*70)
            return {
                **state,
                "next_step": "revise_clarification",
                "status": "needs_revision"
            }
        
        # Success!
        print("\n" + "="*70)
        print("✅ CLARIFICATION READY TO SEND")
        print("="*70)
        
        final_response = state.get('final_clarification')
        
        assistant_message = f"""✅ **Comprehensive Clarification Prepared**

**Classification:**
- Type: {state.get('clarification_classification', {}).get('request_type', 'N/A')}
- Questions: {len(state.get('clarification_questions', []))}
- Confusion Level: {state.get('confusion_level', 'N/A').upper()}
- Urgency: {state.get('clarification_classification', {}).get('urgency_level', 'N/A').upper()}

**Quality Metrics:**
- Overall Score: {state.get('final_quality_score', state.get('quality_score', 0.0)):.2f}/1.0
- Clarity: {state.get('clarification_quality_validation', {}).get('clarity_score', 0.0):.2f}
- Completeness: {state.get('clarification_quality_validation', {}).get('completeness_score', 0.0):.2f}
- All Questions Answered: {'✅ Yes' if state.get('all_questions_answered') else '⚠️ No'}

**Processing:**
- Historical Context: {'✅ Found' if state.get('found_previous_answers') else '❌ None'}
- Enhanced: {'✅ Yes' if state.get('clarification_enhanced') else 'Not needed'}
- Quality Improvement: +{state.get('quality_improvement', 0.0):.2f}

**Ready to send to:** {state.get('top_suppliers', [{}])[0].get('name', 'Supplier')}"""

        return {
            **state,
            "messages": [assistant_message],
            "clarification_ready": True,
            'drafted_message': final_response,
            "next_step": "send_clarification_response",
            "status": "clarification_ready",
            "clarification_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"\n❌ Clarification Handler Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            **state,
            "error": str(e),
            "messages": [f"Error handling clarification: {str(e)}"],
            "next_step": "handle_error",
            "status": "clarification_error"
        }


# ===== UTILITY FUNCTIONS =====

def format_communication_history(history: List[Dict[str, Any]]) -> str:
    """Format recent communication history"""
    if not history:
        return "No previous communications"
    
    formatted = []
    for i, entry in enumerate(history, 1):
        formatted.append(f"\nRound {entry.get('round', i)}:")
        if entry.get('our_message'):
            formatted.append(f"  Us: {entry['our_message'][:150]}...")
        if entry.get('supplier_response'):
            formatted.append(f"  Supplier: {entry['supplier_response'][:150]}...")
    
    return "\n".join(formatted)


def format_full_negotiation_history(history: List[Dict[str, Any]]) -> str:
    """Format complete negotiation history"""
    if not history:
        return "No negotiation history"
    
    formatted = []
    for i, entry in enumerate(history, 1):
        formatted.append(f"\n--- Round {i} ---")
        formatted.append(f"Type: {entry.get('type', 'unknown')}")
        if entry.get('our_message'):
            formatted.append(f"Our message: {entry['our_message'][:200]}...")
        if entry.get('supplier_response'):
            formatted.append(f"Supplier response: {entry['supplier_response'][:200]}...")
        if entry.get('analysis'):
            formatted.append(f"Analysis: {entry['analysis'][:150]}...")
    
    return "\n".join(formatted)


def format_terms(params: Dict[str, Any]) -> str:
    """Format deal terms for prompt"""
    fabric = params.get('fabric_details', {})
    price = params.get('price_constraints', {})
    logistics = params.get('logistics_details', {})
    
    terms = [
        f"Fabric: {fabric.get('type', 'N/A')}",
        f"Quantity: {fabric.get('quantity', 'N/A')} {fabric.get('unit', 'units')}",
        f"Max Price: {price.get('max_price', 'N/A')} {price.get('currency', 'USD')}",
        f"Timeline: {logistics.get('timeline', 'N/A')}",
        f"Destination: {logistics.get('destination', 'N/A')}"
    ]
    
    return "\n".join(terms)





def format_dict_for_prompt(data: Dict[str, Any]) -> str:
    """Format dictionary for prompt inclusion"""
    if not data:
        return "No data available"
    
    lines = []
    for key, value in data.items():
        if isinstance(value, (list, dict)):
            lines.append(f"{key}: {str(value)[:100]}...")
        else:
            lines.append(f"{key}: {value}")
    
    return "\n".join(lines)


def format_classified_questions(questions: List[Dict[str, Any]]) -> str:
    """Format classified questions for prompt"""
    formatted = []
    for i, q in enumerate(questions, 1):
        formatted.append(f"\n{i}. [{q.get('question_type', 'unknown').upper()}] {q.get('question_text')}")
        formatted.append(f"   Priority: {q.get('priority', 'medium').upper()}")
        formatted.append(f"   Blocks negotiation: {'Yes' if q.get('blocks_negotiation') else 'No'}")
        formatted.append(f"   Requires consultation: {'Yes' if q.get('requires_internal_consultation') else 'No'}")
    
    return "\n".join(formatted)


def format_available_information(info_list: List[Dict[str, Any]]) -> str:
    """Format available information for prompt"""
    if not info_list:
        return "No information available"
    
    formatted = []
    for info in info_list:
        formatted.append(f"- {info.get('field_name')}: {info.get('value')}")
        formatted.append(f"  (Source: {info.get('source')}, Confidence: {info.get('confidence', 0):.2f})")
    
    return "\n".join(formatted)


def format_missing_information(info_list: List[Dict[str, Any]]) -> str:
    """Format missing information for prompt"""
    if not info_list:
        return "No missing information"
    
    formatted = []
    for info in info_list:
        formatted.append(f"- {info.get('field_name')} [{info.get('criticality', 'unknown').upper()}]")
        formatted.append(f"  Why needed: {info.get('why_needed')}")
        if info.get('possible_workaround'):
            formatted.append(f"  Workaround: {info['possible_workaround']}")
    
    return "\n".join(formatted)


def format_quality_issues(issues: List[Dict[str, Any]]) -> str:
    """Format quality issues for enhancement prompt"""
    if not issues:
        return "No issues identified"
    
    formatted = []
    for issue in issues:
        formatted.append(f"\n[{issue.get('severity', 'unknown').upper()}] {issue.get('issue_type')}")
        formatted.append(f"  Location: {issue.get('location')}")
        formatted.append(f"  Issue: {issue.get('issue_description')}")
        formatted.append(f"  Fix: {issue.get('suggested_fix')}")
    
    return "\n".join(formatted)


def assemble_response_text(response: ClarificationResponse) -> str:
    """Assemble full response text from structured response"""
    parts = []
    
    # Greeting
    parts.append(response.greeting)
    parts.append("\n")
    
    # Main sections
    for i, section in enumerate(response.main_response_sections, 1):
        parts.append(f"\n**{section.section_title}**\n")
        parts.append(section.content)
        parts.append("\n")
    
    # Proactive additions
    if response.proactive_additions:
        parts.append("\n**Additional Information:**\n")
        for addition in response.proactive_additions:
            parts.append(f"\n• **{addition.topic}**: {addition.content}")
    
    # Examples if any
    if response.examples_provided:
        parts.append("\n\n**Examples:**\n")
        for i, example in enumerate(response.examples_provided, 1):
            parts.append(f"{i}. {example}\n")
    
    # Closing
    parts.append("\n" + response.closing)
    
    return "".join(parts)


def generate_special_instructions(state: AgentState) -> str:
    """Generate special instructions based on state"""
    instructions = []
    
    classification = state.get('clarification_classification', {})
    
    if classification.get('is_circular_confusion'):
        instructions.append("⚠️ CIRCULAR CONFUSION: Supplier has asked this before. Change communication approach - use simpler language, more examples, or different format.")
    
    if classification.get('supplier_confusion_level') == 'severe':
        instructions.append("⚠️ SEVERE CONFUSION: Break down into very simple steps, use many examples, avoid jargon completely.")
    
    if classification.get('supplier_engagement_signal') == 'frustrated':
        instructions.append("⚠️ FRUSTRATED SUPPLIER: Use patient, empathetic tone. Acknowledge their concerns explicitly.")
    
    if state.get('information_evolved'):
        instructions.append("⚠️ TERMS EVOLVED: Clearly explain what changed and why.")
    
    if state.get('found_previous_answers'):
        instructions.append("✅ Reference previous answers where relevant, but add new details.")
    
    return "\n".join(instructions) if instructions else "No special instructions"


def determine_response_tone(classification: Dict[str, Any]) -> str:
    """Determine appropriate tone for response"""
    confusion = classification.get('supplier_confusion_level', 'medium')
    engagement = classification.get('supplier_engagement_signal', 'interested')
    
    if engagement == 'frustrated':
        return "patient, empathetic, apologetic for confusion"
    elif engagement == 'losing_interest':
        return "enthusiastic, value-focused, encouraging"
    elif confusion == 'severe':
        return "simple, clear, friendly, educational"
    elif confusion == 'high':
        return "detailed, patient, thorough"
    else:
        return "professional, clear, collaborative"


def determine_cultural_region(location: str) -> str:
    """Determine cultural region from location"""
    location_lower = location.lower()
    
    if any(c in location_lower for c in ['china', 'japan', 'korea', 'taiwan', 'singapore', 'hong kong']):
        return 'east_asian'
    elif any(c in location_lower for c in ['india', 'pakistan', 'bangladesh', 'sri lanka']):
        return 'south_asian'
    elif any(c in location_lower for c in ['germany', 'italy', 'france', 'uk', 'spain', 'netherlands']):
        return 'european'
    elif any(c in location_lower for c in ['uae', 'turkey', 'egypt', 'saudi']):
        return 'middle_eastern'
    elif any(c in location_lower for c in ['mexico', 'brazil', 'argentina', 'colombia']):
        return 'latin_american'
    elif any(c in location_lower for c in ['usa', 'canada']):
        return 'north_american'
    else:
        return 'international'


# ===== TESTING =====

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 ENHANCED CLARIFICATION NODE - READY")
    print("="*70)
    print("\nFeatures:")
    print("  ✅ 6-stage comprehensive processing")
    print("  ✅ LLM-powered classification")
    print("  ✅ Historical context search")
    print("  ✅ Information validation")
    print("  ✅ Comprehensive response generation")
    print("  ✅ Quality validation gate")
    print("  ✅ Auto-enhancement")
    print("\nTo integrate:")
    print("  1. Add to graph_builder.py")
    print("  2. Route from analyze_supplier_response when intent='clarification_request'")
    print("  3. Connect to send_clarification_response")
    print("\n" + "="*70)