import argparse
import json
from parsers.parser import parser
from utils.utils import loadSchema
import sys
from db.DBconn import pg_conn, mongo_db
from db.store import store_to_db
from db.schema import generate_schema, get_schema, setup_schema
from db.fields import detect_topic, extract_fields, match_fields

def main():
    form_path = sys.argv[1]
    
    form = loadSchema(form_path)
    
    print(form, "hi")
    
    type = form.get("form_type", "")
    topic = form.get("type", "")
    detail = form.get("detail", {})
    # remove detail from form to avoid duplication
    form.pop("detail", None)
    form.pop("form_type", None)
    
    if( not type or not topic):
        topic = detect_topic(form)
    
    fields = get_schema(type)
    
    if not fields:
        fields = generate_schema(type, form)
        # generate the entity here based on the fields and topic 
        print(f"Generated schema for topic '{type}': {fields}")
        setup_schema(pg_conn, type, fields)  # Ensure table exists for the topic
        
    result = parser(form, type, detail, inputType="form")
    
    extracted_data = result.get(type, result)  # or the topic block
    
    # extracted data will be of the follwoing form:
    
    # {
        # core:{}  exactly the same as the input form
        # extra:{} any extra fields that were not matched to the schema - to be pushed ot mongo
    # }
    
    # matched, extra, people, groups = match_fields(extracted_data, fields)
    
    print(extracted_data)
    result = store_to_db(type, extracted_data, fields, pg_conn, mongo_db)
    
    return result

if __name__ == "__main__":
    try:
        output = main()
        print(json.dumps(output, indent=2))  # ✅ actually print the result
        sys.stdout.flush()
    except Exception as e:
        import sys
        print(f"Python error : {str(e)}", file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)
