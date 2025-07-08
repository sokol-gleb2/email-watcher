import json
from utils.utils import format_schema_for_prompt
from prompts.formPrompt import jsonFormPrompt
from llm.extract import extractData
from utils.utils import extract_json_from_response


def parse_form(input_form, topic, detail):
    
    # This function is a placeholder for parsing form data.
    prompt_instructions = format_schema_for_prompt(input_form)
    
    promptResult = jsonFormPrompt(prompt_instructions, topic, detail)

    jsonContent = extractData(promptResult, "You are a helpful assistant that extracts structured data.")
    
    contentFinal = extract_json_from_response(jsonContent)
    
    return contentFinal
