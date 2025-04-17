import cv2
import face_recognition
import numpy as np
import sqlite3
from datetime import datetime
import os

DB_PATH = 'database/student_data.db'
VIDEO_PATH = 'data/classroom_video.mp4'  # replace with your uploaded video path

def load_encodings_from_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT roll_no, name, course, semester, encoding FROM student_details")
    records = cursor.fetchall()
    conn.close()

    known_encodings = []
    metadata = []

    for roll_no, name, course, semester, encoding_blob in records:
        encoding_array = np.frombuffer(encoding_blob, dtype=np.float64)
        known_encodings.append(encoding_array)
        metadata.append({
            'roll_no': roll_no,
            'name': name,
            'course': course,
            'semester': semester
        })

    return known_encodings, metadata

def ensure_attendance_log_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT,
            name TEXT,
            course TEXT,
            semester TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def already_marked_today(conn, roll_no):
    cursor = conn.cursor()
    today_date = datetime.now().date().isoformat()
    cursor.execute("""
        SELECT 1 FROM attendance_log 
        WHERE roll_no = ? AND DATE(timestamp) = ?
    """, (roll_no, today_date))
    return cursor.fetchone() is not None

def log_attendance(conn, student):
    if not already_marked_today(conn, student['roll_no']):
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO attendance_log (roll_no, name, course, semester, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (student['roll_no'], student['name'], student['course'], student['semester'], timestamp))
        conn.commit()
        print(f"[LOGGED] {student['roll_no']} - {student['name']} at {timestamp}")
    else:
        print(f"[SKIPPED] Already marked today: {student['roll_no']} - {student['name']}")

def recognize_from_video(video_path):
    print("[INFO] Loading face encodings...")
    known_encodings, metadata = load_encodings_from_db()
    ensure_attendance_log_table()

    print(f"[INFO] Opening video: {video_path}")
    video = cv2.VideoCapture(video_path)
    conn = sqlite3.connect(DB_PATH)

    frame_count = 0

    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % 2 != 0:
            continue  # Process every 2nd frame for speed

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        print(f"[DEBUG] Frame {frame_count}: Detected {len(face_locations)} faces")
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
            face_distances = face_recognition.face_distance(known_encodings, face_encoding)
            best_match_index = np.argmin(face_distances) if face_distances.size else None

            if best_match_index is not None and matches[best_match_index]:
                student = metadata[best_match_index]
                log_attendance(conn, student)
            else:
                print("[UNKNOWN] Face not recognized")

    video.release()
    conn.close()
    print("[INFO] Video attendance session completed.")

if __name__ == "__main__":
    recognize_from_video(VIDEO_PATH)
