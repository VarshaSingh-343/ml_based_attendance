import os
import pandas as pd
import face_recognition
import sqlite3
import numpy as np
import pickle

# Paths
CSV_PATH = 'data/student_data.csv'
IMAGES_DIR = 'data/images'
DB_PATH = 'database/student_data.db'
PKL_PATH = 'encodings/faces.pkl'

def create_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_details (
            roll_no TEXT PRIMARY KEY,
            name TEXT,
            course TEXT,
            semester TEXT,
            encoding BLOB
        )
    ''')
    conn.commit()

# Try to find the image with common extensions
def find_image_path(roll_no):
    for ext in ['.jpg', '.jpeg', '.png']:
        path = os.path.join(IMAGES_DIR, f"{roll_no}{ext}")
        if os.path.exists(path):
            return path
    return None

def encode_faces_to_db_and_pkl():
    print("[INFO] Loading student data...")
    df = pd.read_csv(CSV_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    known_encodings = []
    known_metadata = []

    for idx, row in df.iterrows():
        roll_no = row['roll_no']
        name = row['name']
        course = row['course']
        semester = row.get('semester') or ''

        image_path = find_image_path(roll_no)

        image_file = row.get('image_path')  # Get custom image file name
        if not image_file:
            print(f"[WARNING] Image path not provided for {roll_no} - Skipping")
            continue

        image_path = os.path.join(IMAGES_DIR, image_file)

        if not os.path.exists(image_path):
            print(f"[WARNING] Image not found at {image_path} - Skipping")
            continue


        print(f"[INFO] Processing image for {roll_no} - {name}")
        image = face_recognition.load_image_file(image_path)
        rgb_image = image[:, :, :3]  # Ensure RGB

        try:
            encodings = face_recognition.face_encodings(rgb_image)
            if encodings:
                encoding_array = encodings[0]
                encoding_blob = encoding_array.tobytes()

                # Insert into DB
                # Check for duplicates before inserting
                cursor.execute("SELECT 1 FROM student_details WHERE roll_no = ?", (roll_no,))
                exists = cursor.fetchone()

                if exists:
                    print(f"[INFO] Skipping duplicate entry for {roll_no}")
                else:
                    # Insert into DB
                    cursor.execute("""
                        INSERT INTO student_details (roll_no, name, course, semester, encoding)
                        VALUES (?, ?, ?, ?, ?)
                    """, (roll_no, name, course, semester, sqlite3.Binary(encoding_blob)))
                    print(f"[SUCCESS] Inserted into DB: {roll_no}")


                # Also prepare for faces.pkl
                known_encodings.append(encoding_array)
                known_metadata.append({
                    'roll_no': roll_no,
                    'name': name,
                    'course': course,
                    'semester': semester
                })
            else:
                print(f"[WARNING] No face found in image for {roll_no}")
        except Exception as e:
            print(f"[ERROR] Failed for {roll_no}: {e}")

    conn.commit()
    conn.close()

    # Save encodings to faces.pkl
    os.makedirs(os.path.dirname(PKL_PATH), exist_ok=True)
    with open(PKL_PATH, 'wb') as f:
        pickle.dump({'encodings': known_encodings, 'metadata': known_metadata}, f)
    print(f"[SUCCESS] All encodings saved to database and {PKL_PATH}")

if __name__ == "__main__":
    create_database()
    encode_faces_to_db_and_pkl()
