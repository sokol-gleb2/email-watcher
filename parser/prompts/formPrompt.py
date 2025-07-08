def jsonFormPrompt(prompt_instructions, topic, detail):
    
    
    prompt_instructions = prompt_instructions or ""  # safely handle None
    cleaned_instructions = "".join(prompt_instructions.split())

    if cleaned_instructions:
        phrase = f"with keys matching exactly the schema: {prompt_instructions}."
    else:
        phrase = ""
        
    return f"""
        You are an professional content parser.

        Here is the content:
        
        ---
        {detail}
        ---
        
        The topic of this content is: "{topic or 'general'}".
        
        Currently, the follwing informaiton is already provided. 
        
        {phrase}.
        
        Your task is to extract any other very important information from the content that is not explicitly mentioned in the schema based on  {topic}.
        
        Categorize any extra important information under different keys if different from the schema.
        
        Make sure to run a spell check on the content before extracting the information. Don't include any spelling mistakes in the output.

        Return only the JSON object with the extracted data, without any additional text or explanation. The JSON format should be:
        
        {{
            "core": {{}},  # This should contain the main content as provided
            "extra": {{}}  # This should contain any extra important information extracted from the content
        }}
        
        Ensure that the keys in the "core" section match exactly the schema provided.
    """