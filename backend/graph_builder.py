import os
import uuid
from typing import Optional

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import sqlite3
from langgraph.prebuilt import ToolNode, tools_condition

from nodes.user_input_receiver_node import receive_user_input
from nodes.intent_classifier_node import classify_intent
from nodes.parameter_extractor_node import extract_parameters
from nodes.quote_generator_node import generate_quote
from nodes.supplier_sourcer_node import search_suppliers_direct_sql  
from nodes.quote_sender_node import send_quote_email
from nodes.negotiation_starter_node import start_negotiation
from nodes.negotiation_message_drafter_node import draft_negotiation_message
from nodes.message_validator_node import validate_and_enhance_message
from nodes.negotiation_message_sender import send_negotiation_message
from nodes.supplier_response_getter_node import receive_supplier_response
from nodes.supplier_response_analyzer_node import analyze_supplier_response
from nodes.clarification_provider_node import handle_clarification_request
from nodes.follow_up_schedualer_node import schedule_follow_up
from nodes.notify_user_and_next_steps_suggester_node import notify_user_and_suggest_next_steps
from nodes.contract_intiate_node import initiate_contract
from state import AgentState

# Configuration
class Config:
    """Configuration management for the procurement graph"""
    DEFAULT_THREAD_ID = os.getenv("GRAPH_THREAD_ID", str(uuid.uuid4()))
    ENABLE_DEBUG = os.getenv("GRAPH_DEBUG", "false").lower() == "true"
    DEFAULT_NEGOTIATION_INPUT = os.getenv("DEFAULT_NEGOTIATION_INPUT", '''
        Can you improve the lead time from 60 to 45 days?,
        The quoted price is too high, can we discuss?,
        Need better payment terms than 100% advance,
        Your competitor quoted 10% lower, can you match?
    ''')  
    DEFAULT_GET_QUOTE_INPUT = os.getenv("DEFAULT_GET_QUOTE_INPUT", '''
        I need a quote for 5,000 meters of organic cotton canvas,
        What's your price for 10k yards of denim fabric?,
        Cost for cotton poplin 120gsm, GOTS certified?,
        Price check: polyester blend, 50/50, 150gsm, quantity 20,000m
    ''')

def route_based_on_intent(state: AgentState) -> str:
    """
    Routing function to determine the next node based on intent
    """
    intent = state.get('intent', '').lower()
    
    if intent == 'get_quote':
        return 'extract_parameters'
    elif intent == 'negotiate':
        return 'start_negotiation'
    else:
        return END
    
def route_after_analysis(state: AgentState) -> str:
    """Route based on supplier response analysis"""
    
    intent = state.get('supplier_intent', {}).get('intent', 'unknown')
    
    if intent == 'clarification_request':
        return 'handle_clarification_request'  # NEW: Comprehensive clarification
    elif intent == 'accept':
        return 'initiate_contract'
    elif intent == 'counteroffer':
        return 'draft_negotiation_message'
    elif intent == 'reject':
        return 'notify_user_and_suggest_next_steps'
    elif intent == 'delay':
        return 'schedule_follow_up'



# Initialize graph
graph_builder = StateGraph(AgentState)

# Add nodes to the graph
graph_builder.add_node('receive_user_input', receive_user_input)
graph_builder.add_node('classify_intent', classify_intent)

graph_builder.add_node('extract_parameters', extract_parameters)
graph_builder.add_node('search_suppliers_direct_sql', search_suppliers_direct_sql)
graph_builder.add_node('generate_quote', generate_quote)
graph_builder.add_node("send_quote_email", send_quote_email)

graph_builder.add_node('start_negotiation', start_negotiation)
graph_builder.add_node('draft_negotiation_message', draft_negotiation_message)
graph_builder.add_node('validate_and_enhance_message', validate_and_enhance_message)
graph_builder.add_node('send_negotiation_message', send_negotiation_message)
graph_builder.add_node('receive_supplier_response', receive_supplier_response)
graph_builder.add_node('analyze_supplier_response', analyze_supplier_response)
graph_builder.add_node("handle_clarification_request", handle_clarification_request)
graph_builder.add_node('schedule_follow_up', schedule_follow_up)
graph_builder.add_node('notify_user_and_suggest_next_steps', notify_user_and_suggest_next_steps)
graph_builder.add_node('initiate_contract', initiate_contract)


# Add edges between nodes
graph_builder.add_edge(START, 'receive_user_input')
graph_builder.add_edge('receive_user_input', 'classify_intent')

graph_builder.add_conditional_edges(
    'classify_intent',
    route_based_on_intent
)

graph_builder.add_edge('extract_parameters', 'search_suppliers_direct_sql')
graph_builder.add_edge('search_suppliers_direct_sql', 'generate_quote')
graph_builder.add_edge('generate_quote', END)
# graph_builder.add_edge("send_quote_email", END)

graph_builder.add_edge('start_negotiation', 'draft_negotiation_message')
graph_builder.add_edge('draft_negotiation_message', 'validate_and_enhance_message')
# graph_builder.add_edge('validate_and_enhance_message', 'send_negotiation_message')
graph_builder.add_edge('validate_and_enhance_message', 'receive_supplier_response')
graph_builder.add_edge('receive_supplier_response', 'analyze_supplier_response') 

# Add conditional routing
graph_builder.add_conditional_edges(
    'analyze_supplier_response',
    route_after_analysis,
    {
        'handle_clarification_request': 'handle_clarification_request',
        'initiate_contract': 'initiate_contract',
        'draft_negotiation_message': 'draft_negotiation_message',
        'notify_user_and_suggest_next_steps': 'notify_user_and_suggest_next_steps',
        'schedule_follow_up': 'schedule_follow_up'
    }
)


graph_builder.add_edge('handle_clarification_request', 'send_negotiation_message')

graph_builder.add_edge('initiate_contract', END)

graph_builder.add_edge('notify_user_and_suggest_next_steps', END)

graph_builder.add_edge('schedule_follow_up', END)

# Setup memory saver for state persistence
conn = sqlite3.connect(database='B2B-texttile-assistant.db', check_same_thread=False)
checkpointer = AsyncSqliteSaver(conn=conn)

# IMPORTANT: Specify interrupt_before to pause before receiving supplier response
graph = graph_builder.compile(
    checkpointer=checkpointer,
    interrupt_before = ['receive_supplier_response'],  # Pause here for human input
    debug=Config.ENABLE_DEBUG
)


def get_saved_state(thread_id: str):
    """
    Retrieve the saved state for a specific thread_id
    
    Returns:
        The saved state dictionary or None if no state exists
    """
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = graph.get_state(config)
        
        if state and state.values:
            print(f"✅ Found saved state for thread: {thread_id}")
            print(f"📊 State keys: {list(state.values.keys())}")
            return state.values
        else:
            print(f"⚠️  No saved state found for thread: {thread_id}")
            return None
    except Exception as e:
        print(f"❌ Error retrieving state: {e}")
        return None


def list_all_threads():
    """
    List all thread IDs that have saved states
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
        threads = cursor.fetchall()
        
        print(f"\n📋 Found {len(threads)} saved threads:")
        for i, (thread_id,) in enumerate(threads, 1):
            print(f"  {i}. {thread_id}")
        
        return [t[0] for t in threads]
    except Exception as e:
        print(f"❌ Error listing threads: {e}")
        return []


def process_events(events, phase=""):
    """Process and display graph events in a consistent format"""
    for event in events:
        step_name = list(event.keys())[0] if event.keys() else "unknown"
        
        for value in event.values():
            if "messages" in value and value["messages"]:
                last_message = value["messages"][-1]
                print(f"[{phase}][{step_name}] 📝 Message: {last_message}")

            # Intent
            if "intent" in value and value['intent']:
                print(f"🎯 Intent: {value['intent']}")
                if 'intent_confidence' in value:
                    print(f"   Confidence: {value['intent_confidence']:.2%}")
            
            # Parameters
            if 'extracted_parameters' in value and value['extracted_parameters']:
                params = value['extracted_parameters']
                print(f"📋 Extracted Parameters:")
                fabric = params.get('fabric_details', {})
                print(f"   - Fabric: {fabric.get('type')}")
                print(f"   - Quantity: {fabric.get('quantity')} {fabric.get('unit')}")
                print(f"   - Urgency: {params.get('urgency_level')}")
            
            # Suppliers
            if 'top_suppliers' in value and value['top_suppliers']:
                suppliers = value['top_suppliers']
                print(f"🏢 Suppliers Found: {len(suppliers)}")
                for i, s in enumerate(suppliers[:3], 1):
                    print(f"   {i}. {s.get('name')} - ${s.get('price_per_unit')}")
            
            # Quote
            if 'quote_id' in value and value['quote_id']:
                print(f"📄 Quote Generated: {value['quote_id']}")
                if 'estimated_savings' in value and value['estimated_savings']:
                    print(f"   💰 Potential Savings: {value['estimated_savings']}%")
            
            # Status
            if 'status' in value and value['status']:
                status = value['status']
                emoji = "✅" if status in ['quote_generated', 'suppliers_found', 'email_sent'] else "⏳"
                print(f"{emoji} Status: {status}")
            
            # Errors
            if 'error' in value and value['error']:
                print(f"❌ Error: {value['error']}")
                if 'error_type' in value:
                    print(f"   Type: {value['error_type']}")
            
            # Next step
            if "next_step" in value and value['next_step']:
                print(f"➡️  Next: {value['next_step']}")

            print()


def run_new_workflow(thread_id: Optional[str] = None) :
    """
    Run a NEW workflow (starts fresh)
    """
    # Generate new thread_id for new conversation
    thread_id = thread_id or str(uuid.uuid4())
    quote_input_text = Config.DEFAULT_GET_QUOTE_INPUT
    
    config = {"configurable": {"thread_id": thread_id}}
    
    print(f"🆕 Starting NEW workflow with thread_id: {thread_id}")
    
    initial_state = {
        "user_input": quote_input_text, 
        "status": "starting",
        "recipient_email": "tybhsn001@gmail.com"
    }
    
    events = graph.stream(initial_state, config)
    process_events(events, "NEW")
    
    print(f"\n✅ Workflow completed. Thread saved as: {thread_id}")


    return thread_id


def continue_workflow(thread_id: str, new_input: Optional[str] = None):
    """
    CONTINUE an existing workflow from saved state
    
    Args:
        thread_id: The thread ID to continue
        new_input: Optional new user input to process
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    # Check if state exists
    saved_state = get_saved_state(thread_id)
    if not saved_state:
        print(f"❌ No saved state found for thread: {thread_id}")
        print("💡 Use run_new_workflow() to start a new conversation")
        return
    
    print(f"🔄 Continuing workflow from thread: {thread_id}")
    print(f"📊 Current status: {saved_state.get('status', 'unknown')}")

    new_input = new_input or Config.DEFAULT_NEGOTIATION_INPUT
    
    # If providing new input, update the state
    if new_input:
        update_state = {"user_input": new_input}
        events = graph.stream(update_state, config)
    else:
        # Continue from where it left off
        events = graph.stream(None, config)
    
    process_events(events, "CONTINUE")


def resume_with_supplier_response(thread_id: str, supplier_response: str):
    """
    Resume the workflow after receiving supplier's response
    
    Args:
        thread_id: The thread ID from the paused workflow
        supplier_response: The supplier's response text
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    # Check current state
    state = graph.get_state(config)
    
    if not state.next:
        print("❌ No paused workflow found for this thread")
        return
    
    print(f"🔄 Resuming negotiation workflow")
    print(f"📨 Supplier response: {supplier_response[:100]}...\n")
    
    # Update the state with supplier response at the current checkpoint
    # This updates the interrupted state without replaying
    graph.update_state(
        config,
        {"supplier_response": supplier_response},
        as_node="receive_supplier_response"  # Update as if we're at this node
    )
    
    # Now stream from None to continue execution from the interruption point
    events = graph.stream(None, config)
    process_events(events, "RESUME")
    
    # Check if paused again (for multi-round negotiation)
    state = graph.get_state(config)
    
    if state.next:
        print("\n" + "="*60)
        print("⏸️  WORKFLOW PAUSED AGAIN - WAITING FOR NEXT SUPPLIER RESPONSE")
        print("="*60)
        print(f"Negotiation rounds: {state.values.get('negotiation_rounds', 0)}")
        print(f"\nTo continue, use:")
        print(f"  resume_with_supplier_response('{thread_id}', 'next supplier response')")
        print("="*60 + "\n")
    else:
        print("\n✅ Negotiation completed")


def view_state(thread_id: str):
    """
    View the current saved state for a thread
    """
    saved_state = get_saved_state(thread_id)
    
    if not saved_state:
        return
    
    print("\n" + "="*60)
    print(f"STATE SNAPSHOT FOR THREAD: {thread_id}")
    print("="*60)
    
    # Show important fields
    important_fields = [
        'status', 'intent', 'quote_id', 'email_sent', 
        'pdf_generated', 'recipient_email'
    ]
    
    for field in important_fields:
        if field in saved_state:
            print(f"  {field}: {saved_state[field]}")
    
    # Show if suppliers and quote exist
    if 'top_suppliers' in saved_state:
        print(f"  top_suppliers: {len(saved_state['top_suppliers'])} suppliers")
    
    if 'extracted_parameters' in saved_state:
        params = saved_state['extracted_parameters']
        print(f"  fabric_type: {params.get('fabric_details', {}).get('type', 'N/A')}")
        print(f"  quantity: {params.get('fabric_details', {}).get('quantity', 'N/A')}")
    
    print("="*60 + "\n")


def demo_checkpoint_usage():
    """
    Demo showing how checkpointing works
    """
    print("\n" + "="*60)
    print("CHECKPOINT DEMO")
    print("="*60)
    
    # 1. Run a new workflow
    print("\n1️⃣ Running NEW workflow...")
    thread_id = run_new_workflow()
    
    # 2. View the saved state
    print("\n2️⃣ Viewing saved state...")
    view_state(thread_id)
    
    # 3. List all threads
    print("\n3️⃣ All saved threads:")
    list_all_threads()
    
    # 4. Show how to continue (example - won't actually run)
    print("\n4️⃣ To continue this workflow later, use:")
    print(f"   continue_workflow('{thread_id}')")
    
    return thread_id


# Main execution block
if __name__ == "__main__":
    while True:

        user_input = input("Enter command (new, continue <id>, view <id>, list, demo, exit): ").strip()
        if user_input == "exit":
            print("Exiting...")
            break

        if user_input == "new":
            run_new_workflow()


        
        elif user_input == "continue":

            # Continue existing workflow
            thread_id = input("Enter thread ID to continue: ")
            continue_workflow(thread_id)

            # Step 2: Simulate supplier response
            print("\nSTEP 2: Supplier responds")
            print("-" * 70)


            supplier_response_1 = """

            Dear Customer,

            Thank you for your inquiry regarding 5,000 meters of organic cotton canvas.

            We are pleased to inform you that we accept all your terms:

            ✓ Price: $4.80 per meter FOB Istanbul
            ✓ Quantity: 5,000 meters
            ✓ Lead time: 22 days from order confirmation
            ✓ Payment terms: 30% advance, 70% before shipment
            ✓ GOTS certification: Included

            We are ready to proceed with this order immediately.

            Please send us your purchase order and we will prepare the proforma invoice within 24 hours.

            Looking forward to working with you.

            Best regards,
            Mehmet Yilmaz
            Sales Manager
            EcoCanvas Mills Turkey
            """
            
            resume_with_supplier_response(thread_id, supplier_response_1)
        
        elif user_input == "view":
            # View saved state
            thread_id = input("Enter thread ID to view: ")
            view_state(thread_id)
        
        elif user_input == "list":
            # List all threads
            list_all_threads()
        
        elif user_input == "demo":
            # Run demo
            demo_checkpoint_usage()
        
        else:
            print("Usage:")
            print("  python graph_builder.py new              - Start new workflow")
            print("  python graph_builder.py continue <id>    - Continue saved workflow")
            print("  python graph_builder.py view <id>        - View saved state")
            print("  python graph_builder.py list             - List all saved threads")
            print("  python graph_builder.py demo             - Run checkpoint demo")

# ed2aa9cb-22d0-4bfc-af7b-509536498ff6