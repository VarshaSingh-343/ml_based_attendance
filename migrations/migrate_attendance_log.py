import sqlite3

DB_PATH = 'database/student_data.db'

def migrate_attendance_log_with_foreign_key():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Step 1: Enable foreign keys (important in SQLite!)
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Step 2: Rename old table
        print("[STEP] Renaming old attendance_log table...")
        cursor.execute("ALTER TABLE attendance_log RENAME TO attendance_log_old;")

        # Step 3: Create new table with foreign key constraint
        print("[STEP] Creating new attendance_log table with foreign key...")
        cursor.execute("""
            CREATE TABLE attendance_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT,
                name TEXT,
                course TEXT,
                semester TEXT,
                timestamp TEXT,
                FOREIGN KEY (roll_no) REFERENCES student_details(roll_no)
            );
        """)

        # Step 4: Copy data from old table to new one
        print("[STEP] Copying data from old to new table...")
        cursor.execute("""
            INSERT INTO attendance_log (roll_no, name, course, semester, timestamp)
            SELECT roll_no, name, course, semester, timestamp FROM attendance_log_old;
        """)

        # Step 5: Drop old table
        print("[STEP] Dropping old table...")
        cursor.execute("DROP TABLE attendance_log_old;")

        conn.commit()
        print("[SUCCESS] Migration completed successfully.")

    except Exception as e:
        conn.rollback()
        print("[ERROR] Migration failed:", e)

    finally:
        conn.close()

if __name__ == "__main__":
    migrate_attendance_log_with_foreign_key()
