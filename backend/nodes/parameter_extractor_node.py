from langchain.chat_models import init_chat_model
from models.paremeter_extractor_model import ExtractedRequest
from langchain_core.messages import SystemMessage, HumanMessage
from state import AgentState
from loguru import logger
from dotenv import load_dotenv
load_dotenv()

# Load model with structured output
model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
structured_model = model.with_structured_output(ExtractedRequest)

# Define the extraction prompt
PARAMETER_EXTRACTION_PROMPT = """You are an expert parameter extraction system for B2B textile trading.

Your task is to extract structured parameters from user messages about fabric/textile requests.

EXTRACTION RULES:
1. Extract ONLY information explicitly stated or clearly implied
2. Convert quantities to numbers (10k = 10000, 5.5k = 5500)
3. Standardize units (prefer meters over yards unless specified)
4. Normalize certifications to standard names (GOTS, OEKO-TEX, BCI, etc.)
5. If deadline is relative (e.g., "in 60 days"), note it but don't calculate exact dates
6. Be conservative - if unsure, mark as missing rather than guess

INTENT CONTEXT: {intent}
- If intent is "get_quote": Focus on quantity, fabric specs, and delivery requirements
- If intent is "find_supplier": Focus on fabric type, certifications, and quality specs  
- If intent is "negotiate": Look for reference to existing quotes or specific terms
- If intent is "request_info": Focus on product specifications being asked about

CONFIDENCE SCORING:
- High (0.8-1.0): All key parameters clearly stated
- Medium (0.6-0.8): Most parameters clear, some ambiguity
- Low (0.3-0.6): Limited information, many assumptions
- Very Low (0.0-0.3): Unclear request, mostly missing info"""

def extract_parameters(state: AgentState) -> dict:
    """
    Node 3: extract_parameters - Extract structured data from user input
    
    Purpose:
    - Parse unstructured text into structured parameters
    - Validate and normalize extracted values
    - Identify missing critical information
    - Prepare data for downstream processing agents
    
    Args:
        state: Current agent state with user input and intent
    
    Returns:
        dict: State updates with extracted parameters and routing info
    """
    
    try:
        # Extract context from state
        user_input = state['user_input']
        current_intent = state['intent'] or "unknown"
        
        # Create messages list
        messages = [
            SystemMessage(content=PARAMETER_EXTRACTION_PROMPT.format(intent=current_intent)),
            HumanMessage(content=f"Extract parameters from this message:\n\n{user_input}")
        ]
        
        # Get structured extraction from LLM
        extraction_result: ExtractedRequest = structured_model.invoke(messages)

        assistant_message = extraction_result.detailed_extraction
        
        if extraction_result.clarification_questions:
            # assistant_message += f" Clarification questions: {', '.join(extraction_result.clarification_questions)}"
            logger.info(f"Clarification questions generated: {extraction_result.clarification_questions}")
            logger.warning("Missing critical information, clarification needed.")

        updates = {
            'extracted_parameters' : extraction_result.model_dump(),
            'messages': [assistant_message],
            'needs_clarification': extraction_result.needs_clarification,
            'clarification_questions': extraction_result.clarification_questions,
            'missing_info': extraction_result.missing_info,
        }
        return updates

    except Exception as e:
        # Handle errors gracefully
        return {
            "error": str(e),
            "messages": ["Sorry, I encountered an error while processing your request."]
        }