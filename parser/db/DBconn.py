import os
import psycopg2
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL connection
pg_conn = psycopg2.connect(
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT")
)

# MongoDB connection
mongo_client = MongoClient(os.getenv("MONGODB_URI"))
mongo_db = mongo_client[os.getenv("MONGODB_DB")]

# Exported connections
__all__ = ["pg_conn", "mongo_db"]
