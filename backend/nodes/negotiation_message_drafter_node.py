from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState
from models.negotiation_message_detail import NegotiationStrategy, DraftedMessage
from dotenv import load_dotenv
import uuid
from utils.determining import determine_cultural_region

load_dotenv()
from loguru import logger



def analyze_negotiation_history(state: AgentState):
    """
    Conduct thorough contextual analysis and historical review
    
    This is the core intelligence function that examines:
    1. The Original Goal: Initial user request that started negotiation
    2. The Conversation Thread: Complete record of all messages exchanged
    3. Supplier Profile: Company info, cultural origin, reliability scores
    4. User's Latest Instruction: Specific immediate goal or counter-offer
    """

    supplier_data = state.get('top_suppliers', [])
    extracted_params = state.get('extracted_parameters', {})

    negotiation_rounds = state.get('negotiation_rounds', 0)
    supplier_response = state.get('supplier_response', "<no response yet, the negotiation is just starting>")
    supplier_offers = state.get('supplier_offers', ["<no offers yet>"]) # by ai
    negotiation_topic = state.get('negotiation_topic', "") # by ai
    conversation_tone = state.get('conversation_tone', "collaborative") # by ai

    # can be modified by ai 
    original_goal = {
        "fabric_details": extracted_params.get('fabric_details', {}),
        "quantity": extracted_params.get('fabric_details', {}).get('quantity'),
        "urgency": extracted_params.get('urgency_level', 'medium'),
        "budget_constraints": extracted_params.get('price_constraints', {}),
        "delivery_requirements": extracted_params.get('logistics_details', {})
    }

    # Extract User's Latest Instruction (immediate tactical goal)
    latest_instruction = state.get('user_input', '')
    current_objective = state.get('negotiation_objective', latest_instruction) # by ai

    
    # Build comprehensive Supplier Profile for cultural context
    active_supplier = {}
    
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
    
    if supplier_info:
        active_supplier = {
            "name": supplier_info.get('name', 'Supplier'),
            "location": supplier_info.get('location', 'Unknown'),
            "country": supplier_info.get('country', 'Unknown'),
            "email": supplier_info.get('email' , "igntayyab@gmail.com"),
            "reliability_score": supplier_info.get('reliability_score', 5.0),
            "cultural_region": determine_cultural_region(supplier_info.get('location', '')),
            "past_negotiations": len(supplier_offers),
            "communication_style": state.get('communication_style', "standard")
        }

    logger.info(f"Active Supplier Profile: {active_supplier}")
    
    # Extract urgency and timing context
    urgency_level = 'medium'
    if isinstance(extracted_params, dict):
        urgency_level = extracted_params.get('urgency_level', 'medium')

    return {
        "negotiation_rounds": negotiation_rounds,
        "last_supplier_response": supplier_response,
        "supplier_offers_history": supplier_offers,
        "negotiation_topic": negotiation_topic,
        "conversation_tone": conversation_tone,
        "original_goal": original_goal,  # The foundational request
        "current_objective": current_objective,  # Immediate tactical goal
        "latest_instruction": latest_instruction,  # User's specific instruction
        "active_supplier": active_supplier,  # Complete supplier profile
        "urgency_level": urgency_level
    }
    
def create_strategy_prompt():
    """Create prompt for negotiation strategy analysis"""
    
    system_prompt = """You are an expert B2B textile negotiation strategist with deep knowledge of global supply chain dynamics and cross-cultural business communication.

Your task is to analyze the current negotiation context and develop an optimal strategic approach for the message that will be drafted.

**STRATEGIC FRAMEWORKS:**

1. **Volume-Based Strategy**: Leverage order size and future business potential
   - Use when: Large quantities, repeat business potential, new supplier relationship
   - Arguments: Economies of scale, long-term partnership value, bulk pricing expectations

2. **Market-Rate Strategy**: Appeal to competitive market dynamics  
   - Use when: Price is above market average, multiple supplier options available
   - Arguments: Competitive benchmarking, market research data, industry standards

3. **Partnership Strategy**: Build long-term relationship value
   - Use when: Seeking ongoing supplier relationships, quality is critical
   - Arguments: Mutual growth, reliability premium, strategic partnership benefits

4. **Urgency Strategy**: Leverage time-sensitive requirements
   - Use when: Tight deadlines, seasonal demands, critical delivery dates
   - Arguments: Premium for speed, expedited processing, priority allocation

5. **Reciprocity Strategy**: Offer value exchange for concessions
   - Use when: Have flexibility in other terms (payment, timeline, specs)
   - Arguments: Faster payment, simplified logistics, specification flexibility

**CULTURAL CONSIDERATIONS:**
- **Asian Markets**: Relationship-first, face-saving, indirect communication
- **European Markets**: Process-oriented, quality-focused, formal communication  
- **Middle Eastern Markets**: Personal relationships, hospitality, patience with negotiation
- **Latin American Markets**: Relationship-building, personal touch, flexible terms
- **North American Markets**: Direct communication, efficiency-focused, data-driven

**TONE GUIDELINES:**
- **Collaborative**: "We're looking to find a solution that works for both sides..."
- **Assertive**: "Based on our market analysis, we need to adjust the terms to..."
- **Relationship-focused**: "Given our interest in building a long-term partnership..."
- **Data-driven**: "Market benchmarks indicate that the current price point..."

Analyze the context and recommend the optimal strategy, supporting arguments, and communication approach."""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Analyze this negotiation context and recommend strategy:

**NEGOTIATION HISTORY:**
- Rounds completed: {negotiation_rounds}
- Current tone: {conversation_tone}
- Urgency level: {urgency_level}

**SUPPLIER PROFILE:**
- Company: {supplier_name}
- Location: {supplier_location}
- Reliability score: {supplier_reliability}

**CURRENT OBJECTIVE:**
{current_objective}

**ORIGINAL REQUEST:**
- Fabric: {fabric_type}
- Quantity: {quantity}
- Budget constraints: {budget_info}

**CONTEXT:**
Last supplier response: {last_response} 

Provide strategic recommendation for optimal negotiation approach.""")
    ])

def create_message_drafting_prompt():
    """Create prompt for strategic message composition with cultural tailoring"""
    
    system_prompt = """You are a veteran B2B textile negotiation specialist and strategic communications expert. You function as the "chief of staff" for negotiations, drafting messages that are tactically sound, strategically aligned, and culturally nuanced.

Your expertise encompasses:
- Global supply chain negotiation dynamics
- Cross-cultural business communication protocols  
- Relationship preservation while achieving tactical objectives
- Persuasive argumentation frameworks
- Professional tone calibration

**STRATEGIC MESSAGE COMPOSITION FRAMEWORK:**

**1. PERSUASIVE RATIONALE CONSTRUCTION:**
Build logical, compelling arguments using these frameworks:

- **Volume-Based Appeals**: "This order is part of our larger procurement strategy for the upcoming season, representing significant volume potential..."
- **Market Intelligence**: "Based on current market benchmarks and our industry analysis, the proposed adjustment reflects fair market rates..."
- **Partnership Value**: "We are seeking to establish a long-term strategic partnership and believe this pricing enables sustainable mutual growth..."
- **Reciprocal Benefits**: "In exchange for this price adjustment, we can offer accelerated payment terms and simplified logistics coordination..."
- **Timeline Optimization**: "Given our production schedule requirements, this arrangement allows for optimal planning and resource allocation..."

**2. CULTURAL COMMUNICATION ADAPTATION:**

- **East Asian Markets**: Indirect approach, relationship emphasis, face-saving language, patience with process
  - "We respectfully request your consideration of..." 
  - "We believe this arrangement honors both our business objectives..."

- **European Markets**: Process-oriented, quality-focused, formal but direct
  - "Our analysis indicates..." 
  - "We propose the following adjustment based on quality specifications..."

- **South Asian Markets**: Relationship-building, respectful hierarchy, collaborative tone
  - "We value our partnership and seek a solution that benefits both parties..."
  - "Given our mutual interest in long-term cooperation..."

- **Middle Eastern Markets**: Personal relationship emphasis, hospitality acknowledgment, patience
  - "We appreciate your hospitality and openness to discussion..."
  - "Building on our positive interactions..."

- **North American Markets**: Direct communication, efficiency-focused, data-driven
  - "Our market analysis shows..."
  - "To optimize efficiency for both organizations..."

**3. PROFESSIONAL TONE CALIBRATION:**

- **Collaborative**: "We're confident we can find a solution that works for both sides..."
- **Assertive**: "Based on our analysis and requirements, we need to adjust the terms to..."
- **Relationship-Focused**: "Given our commitment to building a strong partnership, we propose..."
- **Data-Driven**: "Market benchmarks and our procurement standards indicate..."

**4. STRUCTURAL REQUIREMENTS:**

1. **Professional Opening**: Contextual greeting acknowledging previous communication
2. **Strategic Context**: Brief rationale that justifies the request logically  
3. **Specific Request**: Unambiguous statement of desired terms with clear parameters
4. **Value Proposition**: What the supplier gains from accepting these terms
5. **Clear Call to Action**: Specific response requested with reasonable timeframe
6. **Relationship-Preserving Close**: Maintains long-term partnership potential

**5. COMMUNICATION PRINCIPLES:**
- Every sentence serves a strategic purpose
- Maintain dignity and respect for both parties
- Build logical argument progression
- Be concise but complete
- Include specific terms and numbers
- Avoid ultimatums while being clear about requirements
- Preserve business relationship for future opportunities

Generate a message that reads like it was written by an experienced international trade professional who understands both the technical requirements and the interpersonal dynamics of B2B negotiations."""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Draft a strategic negotiation message using this context:

**NEGOTIATION CONTEXT:**
- Current Round: {negotiation_round}
- Negotiation Topic: {negotiation_topic}  
- Conversation Tone: {conversation_tone}
- Last Supplier Response: {last_supplier_response}

**SUPPLIER PROFILE:**
- Company: {supplier_name}
- Location: {supplier_location}
- Cultural Region: {cultural_region}
- Communication Style: {communication_style}
- Reliability Score: {supplier_reliability}

**STRATEGIC FRAMEWORK:**
- Primary Approach: {primary_approach}
- Key Arguments: {supporting_arguments}
- Recommended Tone: {tone_assessment}
- Cultural Considerations: {cultural_considerations}

**ORIGINAL GOAL (Foundation):**
{original_goal}

**CURRENT TACTICAL OBJECTIVE:**
{negotiation_objective}

**USER'S SPECIFIC INSTRUCTION:**
{latest_instruction}

**MESSAGE PARAMETERS:**
- Channel: {channel}
- Priority Level: {priority}  
- Max Length: 200 words
- Required: Clear call to action, specific terms, professional tone

Draft a complete message ready for transmission that implements the strategic approach while maintaining relationship integrity.""")
    ])


# Initialize models and prompts
model = init_chat_model("google_genai:gemini-2.5-flash-lite")
strategy_model = model.with_structured_output(NegotiationStrategy)
message_model = model.with_structured_output(DraftedMessage)

strategy_prompt = create_strategy_prompt()
message_prompt = create_message_drafting_prompt()


def draft_negotiation_message(state: AgentState):
    """
    Node 4b: draft_negotiation_message - Strategic message composition engine
    
    Purpose:
    - Analyze complete negotiation context and history
    - Develop optimal strategic approach for current situation
    - Draft culturally-aware, persuasive negotiation message
    - Prepare message for transmission to supplier
    - Maintain relationship while achieving tactical objectives
    
    Args:
        state: Current agent state with negotiation context and history
    
    Returns:
        dict: State updates with drafted message and strategic analysis
    """
    
    try:
        # Step 1: Analyze negotiation context and history
        negotiation_context = analyze_negotiation_history(state)

        # Extract key context elements
        supplier_data = negotiation_context.get('active_supplier', {})
        supplier_name = supplier_data.get('name', 'Supplier')
        supplier_location = supplier_data.get('location', 'Unknown')
        supplier_reliability = supplier_data.get('reliability_score', 5.0)
        
        current_objective = negotiation_context.get('current_objective', {})
        urgency_level = negotiation_context.get('urgency_level', 'medium')
        conversation_tone = negotiation_context.get('conversation_tone', 'collaborative')
        active_supplier_email = supplier_data['email']

        # Step 2: Develop negotiation strategy
        strategy_formatted_prompt = strategy_prompt.invoke({
            "negotiation_rounds": negotiation_context.get('negotiation_rounds', 0),
            "conversation_tone": conversation_tone,
            "urgency_level": urgency_level,
            "supplier_name": supplier_name,
            "supplier_location": supplier_location,
            "supplier_reliability": supplier_reliability,
            "current_objective": str(current_objective),
            "fabric_type": negotiation_context.get('original_goal', {}).get('fabric_details', {}).get('type', 'textile'),
            "quantity": negotiation_context.get('original_goal', {}).get('quantity', 'N/A'),
            "budget_info": negotiation_context.get('original_goal', {}).get('budget_constraints', {}),
            "last_response": negotiation_context.get('last_supplier_response', 'No previous response')
        })
        
        # Get strategic recommendation from LLM
        strategy: NegotiationStrategy = strategy_model.invoke(strategy_formatted_prompt)

        # Step 3: Draft the negotiation message with enhanced context
        message_formatted_prompt = message_prompt.invoke({
            "primary_approach": strategy.primary_approach,
            "supporting_arguments": ", ".join(strategy.supporting_arguments),
            "tone_assessment": strategy.tone_assessment,
            "cultural_considerations": strategy.cultural_considerations or "Standard business communication",
            "supplier_name": supplier_name,
            "supplier_location": supplier_location,
            "cultural_region": supplier_data.get('cultural_region', 'international'),
            "communication_style": supplier_data.get('communication_style', 'standard'),
            "supplier_reliability": supplier_reliability,
            "channel": state.get('channel', 'email'),
            "message_type": state.get('message_type', ""), # based on negotiation objective
            "priority": determine_priority(urgency_level, negotiation_context.get('negotiation_rounds', 0)),
            "negotiation_objective": str(current_objective),
            "latest_instruction": negotiation_context.get('latest_instruction', ''),
            "original_goal": str(negotiation_context.get('original_goal', {})),
            "conversation_tone": conversation_tone,
            "negotiation_topic": negotiation_context.get('negotiation_topic', 'general'),
            "negotiation_round": negotiation_context.get('negotiation_rounds', 0) + 1,
            "last_supplier_response": negotiation_context.get('last_supplier_response', 'Initial outreach')
        })

        # Get drafted message from LLM
        drafted_message: DraftedMessage = message_model.invoke(message_formatted_prompt)
        
        # Step 4: Generate unique message ID and set metadata
        message_id = f"msg_{str(uuid.uuid4())[:8]}"
        
        # Update the drafted message with generated ID and current timestamp
        drafted_message.message_id = message_id
        drafted_message.recipient = f"{supplier_name} <{supplier_data.get('contact_info', {}).get('email', 'supplier@email.com')}>"
        
        # Step 5: Create assistant response message that reflects strategic depth
        assistant_message = f"""📋 **Negotiation Message Drafted**

**Strategic Approach:** {strategy.primary_approach}
**Key Arguments:** {', '.join(strategy.supporting_arguments[:2])}
**Cultural Adaptation:** {supplier_data.get('cultural_region', 'Standard')} communication style
**Message Tone:** {strategy.tone_assessment}
**Confidence Score:** {drafted_message.confidence_score:.2f}/1.0

**Ready for transmission to:** {supplier_name} ({supplier_location})
**Message Type:** {drafted_message.message_type}
**Priority:** {drafted_message.priority_level}

The message maintains professional relationship standards while clearly presenting our tactical objectives."""

        # Step 6: Prepare state updates
        state_updates = {
            "drafted_message_data": drafted_message.model_dump(),
            "negotiation_strategy": strategy.model_dump(),
            "negotiation_messages" : [{"role" : "assistant" , "content" : drafted_message.message_body}],
            "drafted_message": drafted_message.message_body,
            "message_id": message_id,
            "message_ready": True,
            "next_step": "send_message_to_supplier",
            "messages": [assistant_message],
            "status": "message_drafted",
            "last_message_confidence": drafted_message.confidence_score,
            "active_supplier_email": active_supplier_email
        }
        
        # Add fallback planning if confidence is low
        if drafted_message.confidence_score < 0.7:
            state_updates["requires_review"] = True
            state_updates["fallback_options"] = drafted_message.fallback_options
            state_updates["next_step"] = "review_message_before_send"
        
        return state_updates


    except Exception as e:
        error_message = f"Error in drafting negotiation message: {str(e)}"
        return {
            "error": str(e),
            "messages": [error_message],
            "next_step": "handle_error",
            "status": "error"
        }
    

def determine_priority(urgency_level: str, negotiation_round: int) -> str:
    """Determine message priority based on urgency and negotiation stage"""
    
    if urgency_level == "urgent" or negotiation_round >= 3:
        return "high"
    elif urgency_level == "high" or negotiation_round >= 2:
        return "medium"
    else:
        return "normal"