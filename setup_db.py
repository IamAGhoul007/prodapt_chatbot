import sqlite3
import os

DB_NAME = 'data/telecom_ops.db'
SCHEMA_FILE = 'sql/01_schema.sql'
SEED_FILE = 'sql/02_seed_data.sql'

def setup_database():
    if os.path.exists(DB_NAME):
        print(f"Removing existing {DB_NAME}...")
        os.remove(DB_NAME)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print(f"Applying schema from {SCHEMA_FILE}...")
    with open(SCHEMA_FILE, 'r') as f:
        cursor.executescript(f.read())

    print(f"Applying seed data from {SEED_FILE}...")
    with open(SEED_FILE, 'r') as f:
        cursor.executescript(f.read())

    conn.commit()
    conn.close()
    print("Database setup complete.")

if __name__ == '__main__':
    setup_database()
