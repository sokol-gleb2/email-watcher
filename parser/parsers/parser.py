from parsers.email import parse_email
from parsers.form import parse_form

def parser(input_form, topic, detail, inputType='email', email = None):
    
    """
    Parses the input email or form data based on the specified type.
    Args:
        email (str): The input email or form data as a string.
        schema (dict): The schema to validate the parsed data against.
        inputType (str): The type of input ('email' or 'form'). Defaults to 'email'.
        metadata (dict, optional): Additional metadata for parsing. Defaults to None.
    Returns:
        dict: The parsed output based on the input type.
    """
     
    if(inputType != 'email'):
        output = parse_form(input_form, topic, detail)
    else:
        output = parse_email(email, input_form, topic, detail)
        
    
    return output
    