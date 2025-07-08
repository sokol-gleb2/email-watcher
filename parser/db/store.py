import json
import psycopg2
from pymongo import MongoClient
from datetime import datetime
import logging
from db.helper import clean_string
from db.schema import setup_schema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# def serialize_value(value):
#     if isinstance(value, (dict, list)):
#         return json.dumps(value)
#     return clean_string(value)

# def store_to_db(topic: str, matched: dict, extra: dict, people, groups, pg_conn, mongo_db):
#     """
#     Stores normalized matched data in PostgreSQL under a topic-based table.
#     Stores unmatched extra fields in MongoDB under 'extra_information'.
    
#     :param topic: The high-level entity type (e.g., 'event', 'vacation', 'recipe')
#     :param matched: Dict of normalized fields
#     :param extra: Dict of extra unmapped/hallucinated fields
#     :param pg_conn: psycopg2 connection object
#     :param mongo_db: MongoDB database object
#     """

#     try:
#         # --- PostgreSQL Insert ---
#         clean_matched = {k: serialize_value(v) for k, v in matched.items()}
#         fields = list(clean_matched.keys())
#         values = list(clean_matched.values())
#         placeholders = ", ".join(["%s"] * len(fields))
#         columns = ", ".join(fields)

#         query = f"""
#             INSERT INTO {topic}s ({columns}, created_at)
#             VALUES ({placeholders}, %s)
#             RETURNING id;
#         """
        
#         with pg_conn.cursor() as cur:
#             cur.execute(query, values + [datetime.utcnow()])
#             entity_id = cur.fetchone()[0]
#             pg_conn.commit()
#             logger.info(f"[store_to_db] Inserted into {topic}s with ID {entity_id}")
        
#         # get the names of all the people in the matched dict
#         if people:
#             with pg_conn.cursor() as cur:
#                 for person_name in people:
#                     name_parts = person_name.strip().split()
                    
#                     # prepare flexible conditions
#                     conditions = []
#                     for part in name_parts:
#                         # try matching either full or partial
#                         conditions.append(f"LOWER(name) LIKE LOWER('%{part}%')")

#                     where_clause = " OR ".join(conditions)

#                     # search in people table with flexible match
#                     cur.execute(f"""
#                         SELECT id, name FROM people
#                         WHERE {where_clause}
#                         LIMIT 1;
#                     """)
#                     person_row = cur.fetchone()
#                     if person_row:
#                         person_id = person_row[0]
#                         try:
#                             print(f"[store_to_db] Linking person {person_name} (ID: {person_id}) to {topic} ID {entity_id}")
#                             cur.execute("""
#                                 INSERT INTO entity_people (person_id, entity_id, entity_type, role, created_at)
#                                 VALUES (%s, %s, %s, NULL, %s);
#                             """, (person_id, entity_id, topic, datetime.utcnow()))
#                             pg_conn.commit()
#                             logger.info(f"[store_to_db] Linked person '{person_name}' to {topic} ID {entity_id}")
#                         except Exception as link_err:
#                             logger.error(
#                                 f"[store_to_db] Failed to link person '{person_name}' (person_id={person_id}) "
#                                 f"to entity {topic} (entity_id={entity_id}): {link_err}"
#                             )


#         # --- MongoDB Insert (for unmatched fields) ---
#         if extra:
#             mongo_db.extra_information.insert_one({
#                 "entity_type": topic,
#                 "entity_id": entity_id,
#                 "extra_fields": {k: clean_string(v) for k, v in extra.items()},
#                 "created_at": datetime.utcnow()
#             })
#             logger.info(f"[store_to_db] Inserted extra info to MongoDB for {topic} ID {entity_id}")

#     except Exception as e:
#         logger.exception(f"[store_to_db] Failed to store {topic} record: {e}")
#         pg_conn.rollback()

def store_to_db(topic: str, data: dict, schema, pg_conn, mongo_db):
    core_data = data.get("core", {})
    extra_data = data.get("extra", {})
    
    cleaned_core_data = {}

    # clean and validate core fields
    for field in schema:
        if field in core_data and field != "detail":
            cleaned_core_data[field] = clean_string(core_data[field])
        else:
            logger.warning(f"Missing expected field '{field}' in core data for topic '{topic}'")

    # --- Store to PostgreSQL ---
    try:
        with pg_conn.cursor() as cur:
            columns = list(cleaned_core_data.keys())
            values = list(cleaned_core_data.values())
            placeholders = ", ".join(["%s"] * len(columns))
            columns_sql = ", ".join(columns)
            
            query = f"""
                INSERT INTO {topic} ({columns_sql}, created_at)
                VALUES ({placeholders}, %s)
                RETURNING id;
            """
            
            
            cur.execute(query, values + [datetime.utcnow()])
            returned_id = cur.fetchone()[0]
            pg_conn.commit()
            logger.info(f"Inserted core data into Postgres table '{topic}s' with id {returned_id}")
    except Exception as e:
        pg_conn.rollback()
        logger.error(f"Postgres insertion failed: {e}")
        raise

    # --- Store to MongoDB ---
    try:
        if extra_data:
            extra_data['pg_id'] = returned_id
            extra_data['created_at'] = datetime.utcnow().isoformat()
            collection = mongo_db[topic]
            result = collection.insert_one(extra_data)
            print(result)
            logger.info(
                f"Inserted extra data into MongoDB collection '{topic}' with linked pg_id {returned_id}, "
            )
    except Exception as e:
        logger.error(f"MongoDB insertion failed: {e}")
        raise

    return returned_id

