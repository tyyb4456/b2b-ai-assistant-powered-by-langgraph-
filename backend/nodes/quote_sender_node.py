from state import AgentState
from composio import Composio
from composio_langchain import LangchainProvider
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent


def send_quote_email(state: AgentState):
    """
    Node to send the generated quote to the user's email.
    Converts quote to PDF, uploads to Drive (optional), and sends via email.
    """

    # Extract necessary information from state
    recipient_email = state.get('recipient_email', 'igntayyab@gmail.com')
    quote_summary = state.get('quote_summary', {})
    quote_document = state.get('quote_document', '')

    model = init_chat_model("google_genai:gemini-2.5-flash")

    composio = Composio(provider=LangchainProvider())

    tool_list = composio.tools.get(
        user_id="0000-0000-0000",  # replace with your composio user_id
        tools=["TEXT_TO_PDF_CONVERT_TEXT_TO_PDF", "GMAIL_SEND_EMAIL"],
    )

    EMAIL_AGENT_PROMPT = (
        "You are an email assistant specialized in sending professional quotes. "
        "You have access to PDF conversion and Gmail sending tools. "
        "ALWAYS follow this workflow:\n"
        "1. FIRST: Use TEXT_TO_PDF_CONVERT_TEXT_TO_PDF to convert the quote text into a PDF file\n"
        "2. SECOND: Use GMAIL_SEND_EMAIL to send the email with the PDF attachment\n"
        "Compose professional emails with appropriate subject lines. "
        "Always confirm what was sent in your final response, including PDF attachment details."
    )

    email_agent = create_agent(
        model,
        tools=tool_list,
        system_prompt=EMAIL_AGENT_PROMPT,
    )

    # Compose the query with the actual quote information
    query = f"""
    Please process and send the following quote to {recipient_email}:

    Quote Summary:
    {quote_summary}

    Complete Quote Document:
    {quote_document}

    IMPORTANT - Follow these steps in order:

    Step 1: Convert the quote document to PDF
    - Use the TEXT_TO_PDF_CONVERT_TEXT_TO_PDF tool
    - Name the PDF file: "Quote_{recipient_email.split('@')[0]}.pdf"
    - Include all the quote information above

    Step 2: Send the email with PDF attachment
    - Use GMAIL_SEND_EMAIL tool
    - Recipient: {recipient_email}
    - Subject: "Your Professional Quote - [Include relevant quote details]"
    - Email Body should include:
    * Professional greeting
    * Brief introduction about the attached quote
    * Key highlights from the quote summary
    * Mention that the full quote is attached as PDF
    * Professional closing and contact information
    - ATTACH the PDF file you created in Step 1

    Please execute all steps and confirm completion.
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
    return {
        'email_sent': True,
        'pdf_generated': True,
        'quote_sender_agent_messages': messages_log,
        'messages': [final_message_text],  # Return as a list with just the text
        'status': 'email_sent',
        'next_step': 'end'
    }