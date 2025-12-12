from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger
from state import AgentState
from dotenv import load_dotenv
import json

load_dotenv()

# Initialize model (no structured output needed)
model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")


def safe_get(obj, key, default='N/A'):
    """
    Safely get value from dict or Pydantic model
    
    Args:
        obj: Dictionary or Pydantic model object
        key: Key/attribute name
        default: Default value if not found
    
    Returns:
        Value or default
    """
    if obj is None:
        return default
    
    try:
        # Try dict access first
        if isinstance(obj, dict):
            return obj.get(key, default)
        # Try Pydantic model attribute access
        elif hasattr(obj, key):
            return getattr(obj, key, default)
        # Try model_dump if it's a Pydantic model
        elif hasattr(obj, 'model_dump'):
            return obj.model_dump().get(key, default)
        else:
            return default
    except Exception:
        return default


def to_dict(obj):
    """
    Convert Pydantic model to dict safely
    
    Args:
        obj: Any object (dict, Pydantic model, etc.)
    
    Returns:
        Dictionary representation
    """
    if obj is None:
        return {}
    
    try:
        if isinstance(obj, dict):
            return obj
        elif hasattr(obj, 'model_dump'):
            return obj.model_dump()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return {}
    except Exception:
        return {}


def create_state_summary_prompt(state: AgentState) -> str:
    """
    Create a comprehensive prompt with all state information
    """
    
    # Extract key information from state (safely)
    user_input = state.get('user_input', 'N/A')
    intent = state.get('intent', 'N/A')
    status = state.get('status', 'N/A')
    next_step = state.get('next_step', 'N/A')
    
    # Build state overview
    state_overview = f"""
=== CURRENT WORKFLOW STATE ===

**User Request:**
{user_input}

**Classified Intent:** {intent}
**Current Status:** {status}
**Next Step:** {next_step}

---

**STATE DETAILS:**
"""
    
    # Add extracted parameters if available
    extracted_params = state.get('extracted_parameters')
    if extracted_params:
        params_dict = to_dict(extracted_params)
        fabric_details = to_dict(params_dict.get('fabric_details', {}))
        logistics_details = to_dict(params_dict.get('logistics_details', {}))
        price_constraints = to_dict(params_dict.get('price_constraints', {}))
        
        state_overview += f"""
**Extracted Parameters:**
- Request ID: {safe_get(params_dict, 'item_id')}
- Request Type: {safe_get(params_dict, 'request_type')}
- Fabric Type: {safe_get(fabric_details, 'type')}
- Quantity: {safe_get(fabric_details, 'quantity')} {safe_get(fabric_details, 'unit')}
- Quality Specs: {safe_get(fabric_details, 'quality_specs', [])}
- Certifications: {safe_get(fabric_details, 'certifications', [])}
- Destination: {safe_get(logistics_details, 'destination')}
- Timeline: {safe_get(logistics_details, 'timeline')}
- Max Price: {safe_get(price_constraints, 'max_price')} {safe_get(price_constraints, 'currency')}
- Urgency: {safe_get(params_dict, 'urgency_level')}
- Needs Clarification: {safe_get(params_dict, 'needs_clarification', False)}
"""
    
    # Add supplier search results if available
    supplier_search = state.get('supplier_search_result')
    if supplier_search:
        search_dict = to_dict(supplier_search)
        top_recs = search_dict.get('top_recommendations', [])
        
        state_overview += f"""
**Supplier Search Results:**
- Total Found: {safe_get(search_dict, 'total_suppliers_found', 0)}
- Filtered: {safe_get(search_dict, 'filtered_suppliers', 0)}
- Top Recommendations: {len(top_recs) if isinstance(top_recs, list) else 0}
- Confidence: {safe_get(search_dict, 'confidence', 0):.2f}
- Search Strategy: {safe_get(search_dict, 'search_strategy', 'N/A')}
"""
    
    # Add quote generation results if available
    generated_quote = state.get('generated_quote')
    if generated_quote:
        quote_dict = to_dict(generated_quote)
        supplier_options = quote_dict.get('supplier_options', [])
        
        state_overview += f"""
**Generated Quote:**
- Quote ID: {safe_get(quote_dict, 'quote_id')}
- Quote Date: {safe_get(quote_dict, 'quote_date')}
- Supplier Options: {safe_get(quote_dict, 'total_options_count', 0)}
- Estimated Savings: {safe_get(quote_dict, 'estimated_savings', 0)}%
- Validity Days: {safe_get(quote_dict, 'validity_days', 30)}
"""
        
        # Add recommended supplier if available
        if supplier_options and len(supplier_options) > 0:
            best_option = to_dict(supplier_options[0]) if isinstance(supplier_options[0], object) else supplier_options[0]
            state_overview += f"""
- Recommended Supplier: {safe_get(best_option, 'supplier_name')}
- Recommended Cost: ${safe_get(best_option, 'total_landed_cost', 0):,.2f}
"""
    
    # Add negotiation status if available
    negotiation_status = state.get('negotiation_status')
    if negotiation_status:
        state_overview += f"""
**Negotiation Status:** {negotiation_status}
- Rounds: {state.get('negotiation_rounds', 0)}
- Active Supplier: {state.get('active_supplier_id', 'N/A')}
- Current Status: {state.get('current_round_status', 'N/A')}
"""
    
    # Add drafted message info if available
    drafted_message_data = state.get('drafted_message_data')
    if drafted_message_data:
        msg_dict = to_dict(drafted_message_data)
        state_overview += f"""
**Drafted Message:**
- Message ID: {safe_get(msg_dict, 'message_id')}
- Message Type: {safe_get(msg_dict, 'message_type')}
- Recipient: {safe_get(msg_dict, 'recipient')}
- Confidence: {safe_get(msg_dict, 'confidence_score', 0):.2f}
"""
    
    # Add contract status if available
    drafted_contract = state.get('drafted_contract')
    if drafted_contract:
        contract_dict = to_dict(drafted_contract)
        state_overview += f"""
**Contract Status:**
- Contract ID: {safe_get(contract_dict, 'contract_id')}
- Review Status: {safe_get(contract_dict, 'review_status')}
- Confidence: {safe_get(contract_dict, 'confidence_score', 0):.2f}
- Legal Review Required: {safe_get(contract_dict, 'legal_review_required', True)}
"""
    
    # Add clarification status if available
    clarification_classification = state.get('clarification_classification')
    if clarification_classification:
        clarif_dict = to_dict(clarification_classification)
        state_overview += f"""
**Clarification Request:**
- Request Type: {safe_get(clarif_dict, 'request_type')}
- Confusion Level: {safe_get(clarif_dict, 'supplier_confusion_level')}
- Questions Count: {len(safe_get(clarif_dict, 'questions', []))}
- Escalation Needed: {safe_get(clarif_dict, 'escalation_recommended', False)}
"""
    
    # Add follow-up schedule if available
    follow_up_schedule = state.get('follow_up_schedule')
    if follow_up_schedule:
        schedule_dict = to_dict(follow_up_schedule)
        state_overview += f"""
**Follow-up Scheduled:**
- Schedule ID: {safe_get(schedule_dict, 'schedule_id')}
- Primary Follow-up Date: {safe_get(schedule_dict, 'primary_follow_up_date')}
- Method: {safe_get(schedule_dict, 'follow_up_method')}
- Confidence: {safe_get(schedule_dict, 'confidence_in_schedule', 0):.2f}
"""
    
    # Add any errors
    error = state.get('error')
    if error:
        state_overview += f"""
**Error Encountered:** {error}
**Error Type:** {state.get('error_type', 'unknown')}
"""
    
    # Add validation status if available
    validation_passed = state.get('validation_passed')
    if validation_passed is not None:
        state_overview += f"""
**Validation Status:** {'✅ Passed' if validation_passed else '⚠️ Issues Found'}
- Requires Human Review: {state.get('requires_human_review', False)}
- Critical Issues: {state.get('critical_issues_count', 0)}
"""
    
    return state_overview


def summarize_state(state: AgentState) -> dict:
    """
    Node: State Summarizer - Generate clear summary of workflow progress
    
    Purpose:
    - Provide transparency into AI's actions and decisions
    - Show user exactly what has been done so far
    - Highlight key information and progress
    - Build trust through clear communication
    
    Args:
        state: Complete workflow state
    
    Returns:
        dict: State update with summary message
    """
    
    try:
        logger.info("=== Generating State Summary ===")
        
        # Create comprehensive state overview
        state_overview = create_state_summary_prompt(state)
        
        logger.debug(f"State overview prepared:\n{state_overview[:500]}...")
        
        # Create system prompt for summary generation
        system_prompt = """You are an AI assistant summarizing your own workflow progress for the user.

Your task is to create a clear, friendly summary that:
1. Explains what you've done so far in this conversation
2. Shows the key information you've collected or generated
3. Highlights any important decisions or actions taken
4. Indicates what's coming next in the workflow

**Guidelines:**
- Use first person ("I've analyzed...", "I found...", "I'm now preparing...")
- Be conversational and transparent
- Focus on what matters to the user
- Keep it concise but informative (3-5 paragraphs max)
- Use emojis sparingly for visual clarity (📊 ✅ 🎯 💰 ⏱️)
- End with clear next steps

**Tone:** Friendly, transparent, professional, progress-focused"""

        # Prepare messages
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""Based on this workflow state, generate a clear summary for the user:

{state_overview}

Create a summary that explains what has been done and what's next.""")
        ]
        
        # Generate summary (no structured output)
        logger.info("Invoking LLM for summary generation...")
        response = model.invoke(messages)
        summary_text = response.content
        
        logger.info("State summary generated successfully")
        logger.debug(f"Summary: {summary_text[:200]}...")
        
        # Return state update with summary message
        return {
            "messages": [summary_text],
            "status": "state_summarized"
        }
        
    except Exception as e:
        logger.exception(f"Error generating state summary: {str(e)}")
        error_message = f"I encountered an issue while generating a progress summary. The workflow is still running normally, but I couldn't create the summary report. Error: {str(e)}"
        return {
            "messages": [error_message],
            "status": "summary_error",
            "error": str(e),
            "error_type": "summary_generation_error"
        }