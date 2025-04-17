import sqlite3

DB_PATH = 'database/student_data.db'

def clear_attendance_logs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendance_log where id=15")
    conn.commit()
    conn.close()
    print("[INFO] All attendance records have been deleted.")

if __name__ == "__main__":
    clear_attendance_logs()
