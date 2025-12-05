import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import os

load_dotenv()  # Load DB credentials from .env


def get_db_connection():

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

    conn.cursor_factory = psycopg2.extras.DictCursor
    return conn
