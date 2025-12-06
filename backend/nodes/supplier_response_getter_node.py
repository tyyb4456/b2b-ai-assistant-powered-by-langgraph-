from state import AgentState
from loguru import logger

# NEW: Node to receive supplier response
def receive_supplier_response(state: AgentState):
    """
    Node to receive and process supplier's response to negotiation
    This node is called when resuming after human input
    """
    supplier_response = state.get('supplier_response', '')
    
    if not supplier_response:
        return {
            'messages': ['⚠️ No supplier response received yet. Waiting...'],
            'status': 'awaiting_supplier_response',
            'next_step': 'wait_for_supplier'
        }
    
    # Process the supplier response
    negotiation_rounds = state.get('negotiation_rounds', 0) + 1

    logger.info(f"Received supplier response: {supplier_response}")
    
    return {
        'messages': [f'📨 Received supplier response: {supplier_response[:100]}...'],
        'negotiation_rounds': negotiation_rounds,
        'negotiation_messages' : [{'role' : 'supplier' , 'content' : supplier_response}],
        'status': 'supplier_response_received',
        'next_step': 'analyze_supplier_response'
    }