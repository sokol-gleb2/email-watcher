def jsonEmailPrompt(email_text, prompt_instructions):
    return f"""
        You are an professional email parser.

        Here is the email content:
        
        ---
        {email_text}
        ---

        Extract the following types of information from the email. Return them as a JSON object with keys matching exactly these: {prompt_instructions}. 
        
        Return any other important information that is not explicitly mentioned in the schema and are beyond the json keys. 
        Any extra information is relevant to the email content. Categorize any extra important information under different keys if different from the schema.

        Return only the JSON object with the extracted data, without any additional text or explanation.
    """
    
def jsonReorganise(jsonContent):
    
    return f"""
        You are a professional organiser of email-event related information.
        
        Here is the json file information:
        
        ---
        {jsonContent}
        ---
        
        Re-structure the json file to re-organise the event-related information.
        
        Ensure that the keys are relevant to the event and that the information is structured in a way that is easy to understand.
        
        Return only the JSON object with the re-structured data, without any additional text or explanation. Only keep the most important information that is relevant to the event.
    """