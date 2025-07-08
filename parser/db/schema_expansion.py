
import json
import os
from llm.extract import extractData

SCHEMA_FILE = "schema_registry.json"

EVENT_FIELDS = ["title", "date", "time", "description"]

def remove_fields(field_sql: str, fields_to_remove: list[str]) -> str:
    for field in fields_to_remove:
        field_sql = "\n".join(
            line for line in field_sql.splitlines() if not line.strip().startswith(f'"{field}"')
        )
    return field_sql

def setup_schema(pg_conn, topic: str, fields: list[str] = None):
    with pg_conn.cursor() as cur:
        if not fields:
            fields = get_schema(topic)

        if topic == "event":
            for required in EVENT_FIELDS:
                if required not in fields:
                    fields.append(required)

        field_sql = ""
        for field in fields:
            sanitized = field.strip().lower().replace(" ", "_")
            field_sql += f'"{sanitized}" TEXT,\n'

        field_sql = remove_fields(field_sql, ["id", "created_at", "approved"])

        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {topic}s (
                id SERIAL PRIMARY KEY,
                {field_sql}
                approved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        setup_core_schema(pg_conn)
        pg_conn.commit()
        print(f"[setup_schema] Table(s) ensured for topic '{topic}'")

def setup_core_schema(pg_conn):
    print("[setup_core_schema] Ensuring all core tables...")
    with pg_conn.cursor() as cur:

        cur.execute("""
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    label TEXT NOT NULL,
    type TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
""")

        cur.execute("""
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    title TEXT,
    description TEXT,
    link TEXT,
    associated_group TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
""")

        cur.execute("""
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    name TEXT,
    level TEXT,
    department TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
""")

        cur.execute("""
CREATE TABLE IF NOT EXISTS entities (
    id SERIAL PRIMARY KEY,
    name TEXT,
    type TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
""")

        cur.execute("""
CREATE TABLE IF NOT EXISTS people_tags (
    person_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY (person_id, tag_id),
    FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);
""")

        cur.execute("""
CREATE TABLE IF NOT EXISTS people_projects (
    person_id INTEGER,
    project_id INTEGER,
    PRIMARY KEY (person_id, project_id),
    FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
""")

        cur.execute("""
CREATE TABLE IF NOT EXISTS people_courses (
    person_id INTEGER,
    course_id INTEGER,
    PRIMARY KEY (person_id, course_id),
    FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);
""")

        cur.execute("""
CREATE TABLE IF NOT EXISTS people_entities (
    person_id INTEGER,
    entity_id INTEGER,
    role TEXT,
    PRIMARY KEY (person_id, entity_id),
    FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE,
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
);
""")

        print("[setup_core_schema] All tables ensured.")

def generate_schema(topic: str, form_content: dict, schema: dict = None) -> list[str]:
    combined_content = f"{form_content.get('title', '')}\n\n{form_content.get('description', '')}".strip()

    instructions = (
        f"You are a data extraction expert.\n"
        f"Given the topic '{topic}', analyze the following content and determine the most relevant structured fields "
        f"that should be extracted from this kind of data.\n"
        f"Return ONLY a Python-style list of field names as strings.\n"
        f"Content:\n---\n{combined_content}\n---\n\n"
        f"Only include fields that would commonly appear for this topic."
    )

    try:
        result = extractData(combined_content, instructions=instructions, temperature=0.3)
        fields = eval(result) if result.startswith("[") else []
        fields = [f.strip().lower() for f in fields if isinstance(f, str)]

        user_fields = [k.lower() for k in schema.keys()] if schema else []
        merged_fields = sorted(set(fields + user_fields))

        if os.path.exists(SCHEMA_FILE):
            with open(SCHEMA_FILE, "r") as f:
                registry = json.load(f)
        else:
            registry = {}

        registry[topic.lower()] = merged_fields
        with open(SCHEMA_FILE, "w") as f:
            json.dump(registry, f, indent=2)

        print(f"[generate_schema] Final schema for topic '{topic}': {merged_fields}")
        return merged_fields

    except Exception as e:
        print(f"[generate_schema] Failed to generate schema for topic '{topic}': {e}")
        return []

def get_schema(topic: str) -> list[str]:
    if not os.path.exists(SCHEMA_FILE):
        print(f"[get_schema] Schema file '{SCHEMA_FILE}' not found.")
        return []

    try:
        with open(SCHEMA_FILE, "r") as f:
            registry = json.load(f)
    except Exception as e:
        print(f"[get_schema] Failed to load schema file: {e}")
        return []

    return registry.get(topic.lower(), [])
