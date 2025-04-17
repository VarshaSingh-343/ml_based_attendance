import sqlite3
import numpy as np

DB_PATH = 'database/student_data.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT * from student_details")
rows = cursor.fetchall()

print("=== Student Records ===")
for row in rows:
    print(f"Roll No: {row[0]}, Name: {row[1]}, Course: {row[2]}, Semester: {row[3]}")

conn.close()
