from state import AgentState
from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from loguru import logger

class PreNegotiate(BaseModel):
    """Structured output model for pre-negotiation analysis"""
    negotiation_topic: str = Field(description="The main topic being negotiated")
    conversation_tone: str = Field(description="The desired tone for the conversation")

def start_negotiation(state: AgentState):
    """
    Initialize negotiation by extracting objective, topic, and tone from user input.
    
    Args:
        state: AgentState containing user_input and negotiation_messages
        
    Returns:
        dict: Updated state with negotiation details
    """
    user_input = state.get("user_input", "")
    negotiation_messages = state.get('negotiation_messages', [])

    logger.info("Starting negotiation initialization...")

    if negotiation_messages:
        logger.info(f"Existing negotiation messages found: {len(negotiation_messages)} messages")
        logger.debug(f"Negotiation messages: {negotiation_messages}")
    else:
        logger.info("No existing negotiation messages found.")
    
    # Initialize the model
    model = init_chat_model("google_genai:gemini-2.5-flash-lite")
    
    # --- Step 1: Extract negotiation objective ---
    objective_prompt = PromptTemplate(
        template=(
            "You are an AI negotiation assistant.\n\n"
            "Given the following user input, extract the main negotiation objective.\n\n"
            "User Input: {user_input}\n\n"
            "Respond with only the core objective in a concise phrase."
        ),
        input_variables=["user_input"],
    )
    
    parser = StrOutputParser()
    objective_chain = objective_prompt | model | parser
    negotiation_objective = objective_chain.invoke({"user_input": user_input}).strip()

    logger.info(f"Extracted negotiation objective: {negotiation_objective}")
    
    # --- Step 2: Extract topic and tone from conversation history ---
    structure_model = model.with_structured_output(PreNegotiate)
    
    # Build context from negotiation messages (list of dicts)
    if negotiation_messages:
        messages_context = "\n".join([
            f"{getattr(msg, 'type', 'unknown')}: {msg.content}"
            for msg in negotiation_messages
        ])
    else:
        messages_context = "No previous messages"
    
    structure_prompt = PromptTemplate(
        template=(
            "Based on the following conversation history and user input, extract:\n"
            "1. The negotiation topic (what is being negotiated)\n"
            "2. The conversation tone (formal, casual, assertive, collaborative, etc.)\n\n"
            "User Input: {user_input}\n\n"
            "Conversation History:\n{negotiation_messages}\n\n"
            "Provide structured output with 'negotiation_topic' and 'conversation_tone'."
        ),
        input_variables=['user_input', 'negotiation_messages']
    )
    
    # Create the structured chain
    structure_chain = structure_prompt | structure_model
    
    # Invoke with proper context
    structured_result: PreNegotiate = structure_chain.invoke({
        "user_input": user_input,
        "negotiation_messages": messages_context
    })
    
    # Extract values
    negotiation_topic = structured_result.negotiation_topic
    conversation_tone = structured_result.conversation_tone
    
    logger.info(f"Extracted negotiation topic: {negotiation_topic}")
    logger.info(f"Extracted conversation tone: {conversation_tone}")

    # Create summary message
    message = f"""
        Negotiation initialized:\n"
        - Objective: {negotiation_objective}\n"
        - Topic: {negotiation_topic}\n"
        - Tone: {conversation_tone}"
    """
    
    # Return updated state
    return {
        "negotiation_objective": negotiation_objective,
        "negotiation_topic": negotiation_topic,
        "conversation_tone": conversation_tone,
        "messages": [message]
    }