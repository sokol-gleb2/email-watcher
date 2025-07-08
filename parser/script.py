import sys
import json
from parsers.email import extract_email_data, parse_email
from parsers.parser import parser
from utils.utils import loadSchema, emlToMessage

if __name__ == '__main__':
    try:
        email_path = sys.argv[1]
        schema_path = sys.argv[2]
        inputType = sys.argv[3] if len(sys.argv) > 3 else 'email'
        
        schema = loadSchema(schema_path)
        email = emlToMessage(email_path)
        
        output = parser(email, schema, inputType)

        print(json.dumps(output))
        sys.stdout.flush()

    except Exception as e:
        print(f"Python error: {str(e)}", file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)


# √ one parser function (different parser function based on input type)
# √ the main parse should call each otehr parser baased on the input (parameter for example is "source" "form")
# the body which will be fed to the function will have parameters (format, email)
# √ capture informaiton that arre beyond on the json (description of the event, time, location, people presenting, travel costs, event recorded? Where it's recorded) - these won't be hardcoded in the json schama
# √ We need a text descrioption of the event (Entepreneurship innovations are doing an open mic event).
# √ form source: a form page that asks for description of the event (if beneficial - add radio buttons, person, event group)

# How to make it "smarter" in terms of important information.

# I need to find out
# - detect the source of the input
# - Check if you can include the json file in gpt-4o-mini - YOU CANT





# wouldn't be just a json schema for everything - triplets of multiple items (name, text definition, json schema)
# submit infromation from the form by users
# where does the text come from?
# mailing list, how does it get the emails? - 
# website will have an inbox 
# THE FORM IS ONLY FOR TESTING!!!!!! ************
# the website should automatically get the emails?







# ***FRONTEND***
# home page - feed - recent stuff - search function 
# page showing the informatino of an added item
# form for the user to copy and paste informaiton
# about page - static content
# - no login

# ***BACKEND***
# SQL 
# - items
# - people, groups, events (extended information)
# MongoDB
# - user sessions?

# recommendation system
# session management (possibly redis?)
# - user sessions
# - user preferences
# - gdpr compliance
# - cookies? 

# IN THE FUTURE - to have a vector database to store some information