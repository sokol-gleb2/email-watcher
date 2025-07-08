import openai
import json
import os
from llm.extract import extractData

SCHEMA_FILE = "schema_registry.json"

def remove_fields(field_sql: str, fields_to_remove: list[str]) -> str:
    """
    Removes specified fields from the field SQL string.
    Ensures that fields like 'id', 'created_at', and 'approved' are not included.
    """
    for field in fields_to_remove:
        # remove the line containing the field
        field_sql = "\n".join(
            line for line in field_sql.splitlines() if not line.strip().startswith(f'"{field}"')
        )
    return field_sql


def setup_schema(pg_conn, topic: str, fields: list[str] = None):
    """
    Ensures a topic-specific table exists in PostgreSQL.
    Adds standard 'id', 'created_at', and dynamic fields from schema.
    If topic is 'event', ensures required fields and creates related tables.
    """
    with pg_conn.cursor() as cur:
        # # Load schema if fields not provided
        # if not fields:
        #     fields = get_schema(topic)

        # # Add mandatory event fields if topic is event
        # if topic == "event":
        #     for required in EVENT_FIELDS:
        #         if required not in fields:
        #             fields.append(required)

        # Build CREATE TABLE query for main entity
        field_sql = ""
        for field in fields:
            sanitized = field.strip().lower().replace(" ", "_")
            field_sql += f'"{sanitized}" TEXT,\n'
            
        # check if there is a field called 'id' or 'created_at' or 'approved' in the fields. If so, remove it
        field_sql = remove_fields(field_sql, ["id", "created_at", "approved"])

        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {topic} (
                id SERIAL PRIMARY KEY,
                {field_sql}
                approved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # build the entity for people
        # setup_people_and_relationship_schema(pg_conn)

        # For 'event' topic, create supporting tables
        # if topic == "event":
        #     cur.execute("""
        #         CREATE TABLE IF NOT EXISTS groups (
        #             id SERIAL PRIMARY KEY,
        #             name TEXT UNIQUE NOT NULL,
        #             created_at TIMESTAMP DEFAULT NOW()
        #         );
        #     """)
        #     cur.execute("""
        #         CREATE TABLE IF NOT EXISTS event_groups (
        #             event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
        #             group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
        #             PRIMARY KEY (event_id, group_id)
        #         );
        #     """)

        # setup_core_schema(pg_conn)
        pg_conn.commit()
        print(f"[setup_schema] Table(s) ensured for topic '{topic}'")

def setup_people_and_relationship_schema(pg_conn):
    print("[setup_people_and_relationship_schema] Ensuring 'people' and 'entity_people' tables...")
    with pg_conn.cursor() as cur:
        # Updated people table with extended columns
        cur.execute("""
            CREATE TABLE IF NOT EXISTS people (
                id SERIAL PRIMARY KEY,
                slug TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                industry TEXT,
                institution TEXT,
                industry TEXT,
                interests TEXT,
                bio TEXT,
                website TEXT,
                headshot TEXT,
                is_approved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # Polymorphic many-to-many relation table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS entity_people (
                person_id INTEGER NOT NULL,
                entity_id INTEGER NOT NULL,
                entity_type TEXT NOT NULL,
                role TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (person_id, entity_id, entity_type),
                FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE
            );
        """)

        pg_conn.commit()
        print("[setup_people_and_relationship_schema] Tables 'people' and 'entity_people' ensured.")

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

def generate_schema(topic: str, form_content: dict) -> list[str]:
    """
    Uses an LLM to generate a list of likely structured field names for a given topic and content.
    Merges with user-provided schema (if any), deduplicates, and stores in schema_registry.json.
    
    :param topic: The high-level entity type (e.g., "vacation")
    :param form_content: Dict with keys 'title' and 'description'
    :param schema: Optional dict of user-defined fields
    :return: List of final field names
    """
    
    # combine content from every key in form_content

    combined_content = "\n".join(
        f"{key}: {value}" for key, value in form_content.items() if isinstance(value, str)
    )

    instructions = (
        f"You are a data extraction expert.\n"
        f"Given the topic '{topic}', analyze the following content and determine the most relevant structured fields "
        f"that should be extracted from this kind of data.\n"
        f"Return ONLY a Python-style list of field names as strings, such as:\n"
        f"['title', 'date', 'location']\n\n"
        f"Content:\n---\n{combined_content}\n---\n\n"
        f"Only include fields that would commonly appear for this topic. Do not invent or duplicate fields."
    )

    try:
    #    The following could be used in some way in the future
        # result = extractData(combined_content, instructions=instructions, temperature=0.3)

        # # Parse LLM output as a Python list
        # fields = eval(result) if result.startswith("[") else []
        # fields = [f.strip().lower() for f in fields if isinstance(f, str)]

        # # Merge with user-provided schema (if any)
        # user_fields = [k.lower() for k in schema.keys()] if schema else []
        # merged_fields = sorted(set(fields + user_fields))

        # Load or initialize schema registry
        if os.path.exists(SCHEMA_FILE):
            with open(SCHEMA_FILE, "r") as f:
                registry = json.load(f)
        else:
            registry = {}

        # Save merged schema with an array of field names
        form_content = [field.strip().lower() for field in form_content if isinstance(field, str)]
        registry[topic.lower()] = form_content
        with open(SCHEMA_FILE, "w") as f:
            json.dump(registry, f, indent=2)

        print(f"[generate_schema] Final schema for topic '{topic}': {form_content}")
        return form_content

    except Exception as e:
        print(f"[generate_schema] Failed to generate schema for topic '{topic}': {e}")
        return []

def get_schema(topic: str) -> list[str]:
    """
    Retrieves the schema (list of fields) for a given topic.
    Looks up the topic in a local JSON schema registry file.
    Returns an empty list if the topic is not found.
    """

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