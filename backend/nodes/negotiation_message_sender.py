import asyncio
from state import AgentState
from composio import Composio
from composio_langchain import LangchainProvider
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent

from app.services.supplier_request_service import get_supplier_request_service
from database import SessionLocal
from loguru import logger


def _run_email_agent_sync(recipient_email: str, drafted_message: str) -> tuple:
    """
    Run the email agent synchronously.
    This is called via asyncio.to_thread to avoid blocking the async event loop.
    """
    model = init_chat_model("google_genai:gemini-2.5-flash")

    composio = Composio(provider=LangchainProvider())

    tool_list = composio.tools.get(
        user_id="tyb111",
        tools=["GMAIL_SEND_EMAIL"],
    )

    EMAIL_AGENT_PROMPT = (
        "You are an email assistant specialized in sending professional messages. "
        "You have access to Gmail sending tools. "
        "Your task is to:\n"
        "1. Use GMAIL_SEND_EMAIL to send the email with the provided message content\n"
        "2. Compose professional emails with appropriate subject lines based on the message content\n"
        "3. Always confirm what was sent in your final response."
    )

    email_agent = create_agent(
        model,
        tools=tool_list,
        system_prompt=EMAIL_AGENT_PROMPT,
    )

    query = f"""
    Please send the following message to {recipient_email}:
    
    Message Content:
    {drafted_message}
    
    Instructions:
    - Use GMAIL_SEND_EMAIL tool
    - Recipient: {recipient_email}
    - Subject: Create an appropriate professional subject line based on the message content
    - Email Body: Use the message content provided above
    
    Please execute and confirm completion.
    """

    messages_log = []
    final_message_text = ""
    
    for step in email_agent.stream(
        {"messages": [{"role": "user", "content": query}]}
    ):
        for update in step.values():
            for message in update.get("messages", []):
                if hasattr(message, 'content'):
                    if isinstance(message.content, str):
                        text_content = message.content
                    elif isinstance(message.content, list):
                        text_content = ""
                        for block in message.content:
                            if isinstance(block, dict) and block.get('type') == 'text':
                                text_content += block.get('text', '')
                            elif hasattr(block, 'text'):
                                text_content += block.text
                    else:
                        text_content = str(message.content)
                    
                    print(text_content)
                    messages_log.append(text_content)
                    
                    if text_content:
                        final_message_text = text_content
    
    return messages_log, final_message_text


async def send_negotiation_message(state: AgentState):
    """
    Node to send the drafted message to the user's email.
    Uses asyncio.to_thread to run synchronous email agent code without blocking.
    """
    # Validate thread_id is present
    
    thread_id = state.get('thread_id')
    if not thread_id:
        logger.error("thread_id is missing from state!")
        raise ValueError("thread_id must be present in state for negotiation message sender")

    # Extract necessary information from state
    recipient_email = state.get('active_supplier_email', 'igntayyab@gmail.com')
    drafted_message = state.get('drafted_message', '')

    logger.info(f"Sending negotiation message to {recipient_email}")

    # Run the synchronous email agent in a thread pool to avoid blocking async event loop
    messages_log, final_message_text = await asyncio.to_thread(
        _run_email_agent_sync,
        recipient_email,
        drafted_message
    )

    # Create supplier request when workflow will pause
    db = SessionLocal()
    try:
        request_service = get_supplier_request_service(db)
        
        # Get supplier_id from multiple sources for robustness
        supplier_id = state.get("active_supplier_id")
        logger.info(f"Extracted supplier_id from active_supplier_id: {supplier_id}")
        
        # Fallback: try to get from selected_supplier
        if not supplier_id:
            selected_supplier = state.get("selected_supplier", {})
            supplier_id = selected_supplier.get("supplier_id") or selected_supplier.get("id")
            logger.info(f"Extracted supplier_id from selected_supplier: {supplier_id}")
        
        # Final fallback
        if not supplier_id:
            supplier_id = "CANVAS_001"  # Default supplier_id for fallback
            logger.warning(f"No supplier_id found in state, using default: {supplier_id}")
        
        # Create request
        await request_service.create_supplier_request(
            thread_id=thread_id,
            supplier_id=supplier_id,
            request_type="negotiation",
            request_subject=f"Negotiation Round {state.get('negotiation_rounds', 1)}",
            request_message=state.get("validated_message"),
            request_context={
                "negotiation_rounds": state.get("negotiation_rounds"),
                "negotiation_objective": state.get("negotiation_objective"),
                "extracted_parameters": state.get("extracted_parameters")
            },
            priority="high" if state.get("urgency_level") == "urgent" else "medium"
        )
        
        logger.success("✅ Supplier request created successfully")
        
    finally:
        db.close()


    # Update state to reflect email was sent
    state['email_sent'] = True
    state['drafted_message_sender_agent'] = messages_log
    state['messages'] = [final_message_text]
    state['status'] = 'email_sent'
    state['next_step'] = 'end'
    
    return state

