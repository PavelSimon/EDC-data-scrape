import sqlite3
import pandas as pd

def get_all_data():
    """Get all data from the database."""
    conn = sqlite3.connect('okte_data.db')
    try:
        df = pd.read_sql_query("SELECT * FROM okte_data", conn)
        return df.to_dict('records')
    finally:
        conn.close()

def get_table_headers():
    """Get column names from the database."""
    conn = sqlite3.connect('okte_data.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM okte_data LIMIT 1")
        return [description[0] for description in cursor.description]
    finally:
        conn.close() 