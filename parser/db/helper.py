import bleach

# --- Constants ---
MAX_FIELD_LENGTH = 1000  # Limit for string values stored in MongoDB

def clean_string(value):
    """Sanitize string input for XSS and truncate if needed."""
    if isinstance(value, str):
        value = bleach.clean(value)
        if len(value) > MAX_FIELD_LENGTH:
            value = value[:MAX_FIELD_LENGTH] + "..."
    return value

def normalize_group_entry(group_entry):
    """
    Normalize any group entry into a clean string name.
    Handles strings, dicts, and malformed single-item dict-likes.
    """
    if isinstance(group_entry, str):
        return clean_string(group_entry)

    elif isinstance(group_entry, dict):
        # Try common key names
        for key in ["name", "title", "group"]:
            if key in group_entry:
                return clean_string(group_entry[key])
        # Fallback: stringify the first value
        values = list(group_entry.values())
        if values:
            return clean_string(values[0])

    elif isinstance(group_entry, list):
        # This handles edge cases like: ["name": "Edinburgh Innovations"]
        try:
            return clean_string(group_entry[0])
        except Exception:
            return None

    return None
