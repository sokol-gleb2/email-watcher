from prompts.emailPrompt import jsonEmailPrompt, jsonReorganise
from llm.extract import extractData
from utils.utils import format_schema_for_prompt, extract_json_from_response
from utils.utils import emlToMessage

def extract_email_data(msg):

    # Extract content
    subject = msg['subject']
    sender = msg['from']
    to = msg['to']
    date = msg['date']

    # Extract the plain text body (first alternative found)
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain' and not part.get_content_disposition():
                body = part.get_content()
                break
    else:
        body = msg.get_content()

    return {
        'subject': subject,
        'from': sender,
        'to': to,
        'date': date,
        'body': body
    }

def getEmailText(email):
    
    email_data = extract_email_data(email)
    email_text = email_data['body']
    
    if not email_text:
        raise ValueError("Email body is empty or not found.")
    
    return email_text

def parse_email(email, schema, topic):
    
    email_text = getEmailText(email)

    prompt_instructions = format_schema_for_prompt(schema)

    promptResult = jsonEmailPrompt(email_text, prompt_instructions)

    jsonContent = extractData(promptResult, "You are a helpful assistant that extracts structured data.")
    
    prompt = jsonReorganise(jsonContent)

    contentFinal = extractData(prompt, "You are a professional organiser of email-event related information.")
    
    contentFinal = extract_json_from_response(contentFinal)

    return contentFinal