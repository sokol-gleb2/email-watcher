import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import csv
from datetime import datetime
from db.schema import setup_people_and_relationship_schema
from db.DBconn import pg_conn, mongo_db

def import_people_from_csv(csv_path: str, pg_conn):
    """
    Imports people from a CSV file into the 'people' table.
    
    :param csv_path: Path to the CSV file
    :param pg_conn: psycopg2 database connection
    """
    
    # build the entity for people
    setup_people_and_relationship_schema(pg_conn)
    
    with open(csv_path, newline='', encoding='latin1') as csvfile:

        reader = csv.DictReader(csvfile)
        people = list(reader)

    insert_query = """
        INSERT INTO people (
            slug,
            name,
            industry,
            institution,
            interests,
            bio,
            website,
            email,
            is_approved,
            created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    """
    
    # create slug for each person
    for person in people:
        name = person.get('Name', '').strip()
        if name:
            slug = name.lower().replace(' ', '-').replace('.', '').replace(',', '')
            person['slug'] = slug
        else:
            person['slug'] = None

    with pg_conn.cursor() as cur:
        for person in people:
            try:
                cur.execute(insert_query, (
                    person.get('slug'),
                    person.get('Name'),
                    person.get('Industry/Research'),
                    person.get('Affiliation'),
                    person.get('Field of interest'),
                    person.get('Good to know'),
                    person.get('Website'),
                    person.get('Email'),
                    True,
                    datetime.utcnow()
                ))
            except Exception as e:
                print(f"[import_people_from_csv] Skipped row due to error: {e}\nRow: {person}")
        pg_conn.commit()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python init_members.py <csv_path> <db_connection_string>")
        sys.exit(1)
    
    csv_path = "cluster_members.csv"

    import_people_from_csv(csv_path, pg_conn)
    
    pg_conn.close()
    print("[init_members] Completed importing members from CSV.")