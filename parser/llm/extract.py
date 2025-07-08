from dotenv import load_dotenv
import os
from openai import OpenAI
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extractData(prompt, instructions=None, temperature=0.2):
    
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    prompt = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
    )
    
    result = prompt.choices[0].message.content.strip()
    
    return result