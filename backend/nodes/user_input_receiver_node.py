from state import AgentState
import uuid

def receive_user_input(state: AgentState):
    """
    Node 1: receive_input - Entry point of the LangGraph workflow
    
    Purpose:
    - Initialize the conversation state
    - Store raw user input for downstream processing
    - Set the next step in the workflow
    - Establish the foundation for all subsequent nodes
    
    Args:
        state: Current agent state (may be empty for initial call)
    
    Returns:
        dict: State updates to be merged into the current state
    """
    
    # Create the user message tuple for LangGraph message handling
    user_message = state['user_input']
    session_id = state.get("session_id") or str(uuid.uuid4())
    channel = state.get("channel") or "api"
    

    # This is initial input - normal flow
    assistant_message = f"Received your message via {channel}. Processing..."
    update_state = {
        'messages': [user_message, assistant_message],
        'session_id': session_id,
        'next_step': 'intent_classification',
        'status': 'received_user_input',
    }

    return update_state