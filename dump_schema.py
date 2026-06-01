import sqlite3
import os

db_path = os.path.join('d:\\capstone2', 'data', 'telecom_ops.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT sql FROM sqlite_master WHERE type='table'")
for row in cur.fetchall():
    if row[0]:
        print(row[0])
conn.close()
