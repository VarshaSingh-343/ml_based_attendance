import cv2
import face_recognition
import numpy as np
import sqlite3
from datetime import datetime
import encode
from message_store import update_message

encode.create_database()
encode.encode_faces_to_db_and_pkl()

DB_PATH = 'database/student_data.db'

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
        message = f"✅ Attendance marked for {student['roll_no']} - {student['name']}"
        update_message(message, "success")
        print(f"[LOGGED] {student['roll_no']} - {student['name']} at {timestamp}")
        return message, "success"
    else:
        message = f"⚠️ Already marked today: {student['roll_no']} - {student['name']}"
        update_message(message, "warning")
        print(f"[SKIPPED] Already marked today: {student['roll_no']} - {student['name']}")
        return message, "warning"


def recognize_faces():
    print("[INFO] Loading encodings from database...")
    known_encodings, metadata = load_encodings_from_db()
    ensure_attendance_log_table()

    print("[INFO] Starting webcam...")
    video = cv2.VideoCapture(0)
    conn = sqlite3.connect(DB_PATH)

    while True:
        ret, frame = video.read()
        if not ret:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        MIN_FACE_HEIGHT = 130

        for location, face_encoding in zip(face_locations, face_encodings):
            top, right, bottom, left = location
            face_height = (bottom - top) * 4  # Scale back up

            x1, y1 = left * 4, top * 4
            x2, y2 = right * 4, bottom * 4

            face_label = "Unknown"
            color = (0, 0, 255)  # Red

            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
            face_distances = face_recognition.face_distance(known_encodings, face_encoding)
            best_match_index = np.argmin(face_distances) if face_distances.size else None

            if face_height < MIN_FACE_HEIGHT:
                face_label = "Too Far"
            elif best_match_index is not None and matches[best_match_index]:
                student = metadata[best_match_index]
                face_label = student['roll_no']
                color = (0, 255, 0)
                log_attendance(conn, student)
            else:
                print("[UNKNOWN] Face not recognized")

            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Draw label above face
            cv2.putText(frame, face_label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Draw distance remark below face
            if face_height < MIN_FACE_HEIGHT:
                cv2.putText(frame, f"Height: {face_height:.1f} - Too Far", (x1, y2 + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            else:
                cv2.putText(frame, f"Height: {face_height:.1f}", (x1, y2 + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            if face_height < MIN_FACE_HEIGHT:
                update_message("📏 Please move closer to the camera", "warning")

                continue


            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
            face_distances = face_recognition.face_distance(known_encodings, face_encoding)
            best_match_index = np.argmin(face_distances) if face_distances.size else None

            if best_match_index is not None and matches[best_match_index]:
                student = metadata[best_match_index]
                log_attendance(conn, student)
            else:
                update_message("❌ Face not recognized", "error")
                print("[UNKNOWN] Face not recognized")

        cv2.putText(frame, "--Press Q to exit webcam", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        # 🖼️ Show webcam feed
        cv2.imshow("Attendance System", frame)

        # ⌨️ Quit on 'q'
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break


    video.release()
    cv2.destroyAllWindows()
    conn.close()

    print("[INFO] Attendance session ended.")


def recognize_from_frame(frame):
    known_encodings, metadata = load_encodings_from_db()
    ensure_attendance_log_table()
    conn = sqlite3.connect(DB_PATH)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    response_faces = []
    message_text = "No face detected"
    message_type = "info"

    for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
        face_data = {
            "box": [left, top, right - left, bottom - top],  # x, y, width, height
            "recognized": False
        }

        matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.5)
        face_distances = face_recognition.face_distance(known_encodings, encoding)
        best_match_index = np.argmin(face_distances)

        if matches[best_match_index]:
            student = metadata[best_match_index]
            face_data.update({
                "recognized": True,
                "roll_no": student["roll_no"],
                "name": student["name"]
            })

            message_text, message_type = log_attendance(conn, student)

        else:
            message_text = "❌ Face not recognized"
            message_type = "error"

        response_faces.append(face_data)

    conn.close()

    return {
        "text": message_text,
        "type": message_type,
        "faces": response_faces
    }


if __name__ == "__main__":
    recognize_faces()
