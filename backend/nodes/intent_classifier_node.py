from pydantic import BaseModel, Field
from typing import Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from state import AgentState
from dotenv import load_dotenv
load_dotenv()

# Pydantic Models for structured data
class IntentClassification(BaseModel):
    """Structured output model for intent classification"""
    intent: Literal["get_quote", "find_supplier", "negotiate", "request_info", "other"] = Field(
        ...,
        description="The classified intent of the user's message"
    )
    confidence: float = Field(
        ...,
        description="Model's confidence score in the classification (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation of why this intent was chosen"
    )


def create_classification_prompt():
    """Create the prompt template for intent classification."""
    system_prompt = """You are an expert intent classification system for a B2B textile procurement platform.

Your job is to analyze user messages and classify them into one of these categories:

**INTENT CATEGORIES:**

1. **get_quote**: User wants pricing information for specific products
   - Examples: "price for 10,000m cotton", "how much for silk fabric?", "quote me on organic linen"
   - Key indicators: quantity mentions, price requests, cost inquiries

2. **find_supplier**: User wants to locate manufacturers or sources
   - Examples: "who makes organic cotton?", "find suppliers for denim", "source for hemp fabric"
   - Key indicators: "who", "where", "find", "supplier", "manufacturer"

3. **negotiate**: User is discussing terms of existing offers or relationships
   - Examples: "can you do better on price?", "lead time too long", "improve the terms"
   - Key indicators: references to existing quotes, improvement requests, term discussions

4. **request_info**: User wants general information about products/services
   - Examples: "what certifications do you have?", "what's your MOQ?", "shipping options?"
   - Key indicators: question words without specific procurement intent

5. **other**: Greetings, unclear messages, or off-topic content
   - Examples: "hello", "thanks", unclear or ambiguous messages

**CLASSIFICATION RULES:**
- Be decisive: choose the MOST LIKELY intent even if multiple could apply
- Default to "other" only if the message is truly unclear or off-topic
- Consider context clues like quantities, product names, and business terminology
- Confidence should reflect how certain you are (0.8+ for clear cases, 0.5-0.7 for ambiguous)

**ENTITY EXTRACTION:**
Also extract key entities that might be useful:
- fabric_type: cotton, silk, linen, etc.
- quantity: numbers with units (meters, yards, pieces)
- certifications: GOTS, OEKO-TEX, organic, etc.
- location: shipping destinations, supplier locations
- urgency: deadlines, timeline mentions

Respond ONLY in the structured JSON format. Be concise but thorough."""

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Classify this message:\n\n{user_input}")
    ])

model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
structured_model = model.with_structured_output(IntentClassification)
prompt_template = create_classification_prompt()

def classify_intent(state: AgentState):
    """
    Node 2: classify_intent - Intelligent intent classification
    
    Purpose:
    - Analyze user's message to determine their primary goal
    - Route workflow to appropriate specialized agents
    - Establish confidence level for downstream decision making
    - Handle ambiguous requests with appropriate confidence scoring
    
    Args:
        state: Current agent state containing user input
    
    Returns:
        dict: State updates with classified intent and routing information
    """
    
    try:
        # Extract user input from state
        user_input = state['user_input']
        
        # Create prompt with user input
        formatted_prompt = prompt_template.invoke({"user_input": user_input})
        
        # Get structured classification from LLM
        classification: IntentClassification = structured_model.invoke(formatted_prompt)

        # Create assistant response message
        assistant_message = f"Intent classified as: {classification.intent} (confidence: {classification.confidence:.2f})"

        logger.info(f"Classified intent: {classification.intent} with confidence {classification.confidence}")

        # Prepare state update
        state_update = {
            "intent": classification.intent,
            "intent_confidence": classification.confidence,
            "intent_reasoning": classification.reasoning,
            "next_step": classification.intent,  # Route based on intent
            "messages": [assistant_message],
            "status": "intent_classified",
        }
        
        return state_update
    
    except Exception as e:
        error_message = f"Error in intent classification: {str(e)}"
        return {
            "intent": "error",
            "next_step": "handle_error",
            "messages": [error_message],
            "status": "error"
        }