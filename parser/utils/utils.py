import json
import re
from email import policy
from email.parser import BytesParser

def format_schema_for_prompt(schema):
    instructions = ["The current input contains the following fields and information:"]
    
    for key, value in schema.items():
        # capitalize the key nicely
        field_name = key.replace("_", " ").capitalize()
        instructions.append(f"- **{field_name}**: {value}")
    
    return "\n".join(instructions)

def convert_keys_to_lowercase(d):
    if isinstance(d, dict):
        return {k.lower(): convert_keys_to_lowercase(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [convert_keys_to_lowercase(item) for item in d]
    else:
        return d

def extract_json_from_response(content):
    # Strip triple backticks and language hint if present
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # fallback if no triple backtick wrapper
        json_str = content.strip()
        
    jsonResult = json.loads(json_str)
    
    # convert all keys of the jsonResult to lowercase including nested keys
    jsonResult = convert_keys_to_lowercase(jsonResult)
    
    return jsonResult

def loadSchema(schema_path):
    
    with open(schema_path, 'r') as schema_file:
        schema = json.load(schema_file)
        
    return schema

def emlToMessage(eml_path):
    """
    Convert an EML file to an email message object.
    """
    with open(eml_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
        
    return msg