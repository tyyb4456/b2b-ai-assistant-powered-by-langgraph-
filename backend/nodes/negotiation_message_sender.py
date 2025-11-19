from state import AgentState
from composio import Composio
from composio_langchain import LangchainProvider
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent


def send_negotiation_message(state: AgentState):
    """
    Node to send the drafted message to the user's email.
    """

    # Extract necessary information from state
    recipient_email = state.get('active_supplier_email', 'igntayyab@gmail.com')
    drafted_message = state.get('drafted_message', '')

    model = init_chat_model("google_genai:gemini-2.5-flash")

    composio = Composio(provider=LangchainProvider())

    tool_list = composio.tools.get(
        user_id="0000-0000",  # replace with your composio user_id
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

    # Compose the query with the actual message information
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

   # Stream the agent's execution
    messages_log = []
    final_message_text = ""
    
    for step in email_agent.stream(
        {"messages": [{"role": "user", "content": query}]}
    ):
        for update in step.values():
            for message in update.get("messages", []):
                # Extract text content from the message
                if hasattr(message, 'content'):
                    if isinstance(message.content, str):
                        # If content is a string, use it directly
                        text_content = message.content
                    elif isinstance(message.content, list):
                        # If content is a list of content blocks, extract text
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
                    
                    # Store the last message text
                    if text_content:
                        final_message_text = text_content
    
    # Update state to reflect email was sent
    state['email_sent'] = True
    state['drafted_message_sender_agent'] = messages_log
    state['messages'] = [final_message_text],
    state['status'] = 'email_sent'
    state['next_step'] = 'end'
    
    return state

