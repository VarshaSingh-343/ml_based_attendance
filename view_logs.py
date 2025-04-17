import sqlite3
import pandas as pd

DB_PATH = 'database/student_data.db'

def view_attendance_logs():
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM attendance_log ORDER BY timestamp DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("[INFO] No attendance records found.")
    else:
        print("[INFO] Attendance Records:")
        print(df)

if __name__ == "__main__":
    view_attendance_logs()
