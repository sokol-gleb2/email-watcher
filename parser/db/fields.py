from sentence_transformers import SentenceTransformer, util
from llm.extract import extractData
import json
import os
from db.schema import get_schema

model = SentenceTransformer("all-MiniLM-L6-v2")

SCHEMA_FILE = "schema_registry.json"
# You can expand this list anytime
KNOWN_TOPICS = [
    "event", "recipe", "job", "vacation", "trip", "news", "product", "course", "announcement"
]

def detect_topic(content: dict) -> str:
    """
    Detects the high-level topic of the input content using an LLM via extractData().
    Accepts a dictionary with 'title' and 'description' keys.
    Returns one of the known topic labels.
    """

    combined_text = f"{content.get('title', '')}\n\n{content.get('description', '')}".strip()

    instructions = (
        "You are an expert content classifier. Based on the input text, classify the topic into one of these categories:\n\n"
        + ", ".join(KNOWN_TOPICS) +
        ".\n\nReturn only the topic label as a single word (lowercase)."
    )

    try:
        response = extractData(combined_text, instructions=instructions, temperature=0.0)
        topic = response.lower().strip()

        return topic if topic in KNOWN_TOPICS else "unknown"

    except Exception as e:
        print(f"[detect_topic] Error detecting topic: {e}")
        return "unknown"



# def match_fields(llm_output: dict, schema: list[str]) -> tuple[dict, dict]:
#     """
#     Compares keys from LLM output to the known schema fields.
#     Returns:
#       - matched_fields: dict of normalized field → value
#       - extra_fields: dict of hallucinated/unmapped field → value
#     Uses synonym mapping and sentence-transformer similarity.
#     """

def match_fields(llm_output: dict, schema: list[str], threshold: float = 0.75) -> tuple[dict, dict]:
    """
    Matches top-level and nested keys from LLM output to known schema fields using semantic similarity.
    Does NOT match nested objects themselves—only their leaf keys.

    :param llm_output: Dict of raw LLM output (may contain nested dicts)
    :param schema: List of valid schema field names
    :param threshold: Similarity threshold for a match
    :return: (matched_fields, extra_fields)
    """
    from sentence_transformers.util import cos_sim

    matched = {}
    extra = {}
    people = []
    groups = []
    
    if not schema or not llm_output:
        return matched, llm_output

    clean_schema = [str(s).strip().lower() for s in schema]
    schema_embeddings = model.encode(clean_schema, convert_to_tensor=True)

    def try_match(field_name, value) -> tuple[bool, str]:
        """Try matching a single field name to schema using semantic similarity."""
        key_embedding = model.encode(field_name, convert_to_tensor=True)
        similarities = cos_sim(key_embedding, schema_embeddings)[0]

        best_score = float(similarities.max())
        best_index = int(similarities.argmax())
        best_match = clean_schema[best_index]

        if best_score >= threshold:
            return True, best_match
        return False, field_name
    
    def recurse(obj, parent=None):
        if not isinstance(obj, dict):
            return

        for k, v in obj.items():
            if isinstance(v, dict):
                # Recurse into nested dictionary — do NOT match parent key
                recurse(v, parent=k)
            else:
                success, key = try_match(k.lower(), v)
                if success:
                    matched[key] = v
                else:
                    dotted = f"{parent}.{k}" if parent else k
                    extra[dotted] = v
                    
    # check if the llm_output has people or groups. If yet to be extracted, then extract them
    if isinstance(llm_output, dict):
        if 'people' in llm_output:
            people = llm_output['people']
            del llm_output['people']
        if 'groups' in llm_output:
            groups = llm_output['groups']
            del llm_output['groups']
    
    print(llm_output)
    recurse(llm_output)
    return matched, extra, people, groups



def extract_fields(form_content: dict, topic: str, schema: dict = None) -> dict:
    """
    Uses an LLM to extract structured data from form_content based on:
    - Known topic schema (from registry)
    - Optional user-provided schema (custom fields)

    :param form_content: dict with 'title' and 'description'
    :param topic: The entity category (e.g., 'event', 'job', 'vacation')
    :param schema: Optional dict of extra user-defined fields
    :return: dict of extracted field values
    """

    # Load core schema fields from registry
    schema_fields = get_schema(topic)
    
    # Merge with user-provided schema keys
    if schema:
        schema_fields = list(set(schema_fields + list(schema.keys())))

    if not schema_fields:
        return {}

    schema_fields = sorted(set(f.lower().strip() for f in schema_fields))

    combined_content = f"{form_content.get('title', '')}\n\n{form_content.get('description', '')}".strip()

    instructions = f"""
You are a structured data extractor. Based on the topic and content below, extract only the fields listed.

Topic: "{topic}"
Fields: {schema_fields}

Content:
---
{combined_content}
---

Instructions:
- Return only a JSON object matching the fields listed.
- Use the exact field names.
- Leave out fields you cannot infer or set them to null/empty string.
- Do not include extra text or explanation.
"""

    try:
        result = extractData(combined_content, instructions=instructions, temperature=0.2)

        # Parse and validate JSON
        try:
            parsed = json.loads(result)
            if isinstance(parsed, dict):
                return parsed
            else:
                print("[extract_fields] Output is not a valid dict.")
                return {}
        except json.JSONDecodeError:
            print(f"[extract_fields] Invalid JSON output:\n{result}")
            return {}

    except Exception as e:
        print(f"[extract_fields] Extraction failed: {e}")
        return {}


