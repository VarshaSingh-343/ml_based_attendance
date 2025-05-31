from flask import Flask, render_template, request, jsonify,  redirect, url_for, session, Response
import threading
import cv2
import numpy as np
import base64, sqlite3, csv, io
from face_recognize import recognize_from_frame
import message_store

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")


app.secret_key = 'secret-key'

ADMIN_ID = 'admin123'
ADMIN_PASS = 'pass123'


# code for login route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data['admin_id'] == ADMIN_ID and data['password'] == ADMIN_PASS:
        session['admin_logged_in'] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid ID or password"})

# admin dashboard route
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('home'))
    return render_template("admin_dashboard.html")


# route for view the attendance record by admin 
@app.route('/admin/attendance', methods=['POST'])
def view_attendance():
    if not session.get('admin_logged_in'):
        return jsonify({"records": []})

    data = request.get_json()
    course = data.get("course", "")
    date = data.get("date", "")
    status = data.get("status", "")

    conn = sqlite3.connect('database/student_data.db')
    cursor = conn.cursor()

    records = []

    if status == "Marked":
        query = """
            SELECT s.roll_no, s.name, s.course, 
                   DATE(a.timestamp) as date,
                   TIME(a.timestamp) as time
            FROM attendance_log a
            JOIN student_details s ON s.roll_no = a.roll_no
            WHERE 1=1
        """
        params = []

        if course:
            query += " AND s.course = ?"
            params.append(course)
        if date:
            query += " AND DATE(a.timestamp) = ?"
            params.append(date)

        cursor.execute(query, params)
        for row in cursor.fetchall():
            records.append({
                "roll_no": row[0],
                "name": row[1],
                "course": row[2],
                "date": row[3],
                "time": row[4],
                "status": "Marked"
            })

    elif status == "Unmarked":
        # All students not in attendance_log on selected date
        if not date:
            return jsonify({"records": []})  # Require a date for unmarked

        query = """
            SELECT s.roll_no, s.name, s.course
            FROM student_details s
            WHERE NOT EXISTS (
                SELECT 1 FROM attendance_log a
                WHERE s.roll_no = a.roll_no AND DATE(a.timestamp) = ?
            )
        """
        params = [date]

        if course:
            query += " AND s.course = ?"
            params.append(course)

        cursor.execute(query, params)
        for row in cursor.fetchall():
            records.append({
                "roll_no": row[0],
                "name": row[1],
                "course": row[2],
                "date": date,
                "status": "Unmarked"
            })

    else:
        # No filter, show all attendance log
        query = """
            SELECT s.roll_no, s.name, s.course, 
                   DATE(a.timestamp) as date,
                   TIME(a.timestamp) as time
            FROM attendance_log a
            JOIN student_details s ON s.roll_no = a.roll_no
        """
        params = []
        if course:
            query += " WHERE s.course = ?"
            params.append(course)
        if date:
            query += " AND DATE(a.timestamp) = ?" if params else " WHERE DATE(a.timestamp) = ?"
            params.append(date)

        cursor.execute(query, params)
        for row in cursor.fetchall():
            records.append({
                "roll_no": row[0],
                "name": row[1],
                "course": row[2],
                "date": row[3],
                "time": row[4],
                "status": "Marked"
            })

    conn.close()
    return jsonify({"records": records})


# admin logout route
@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))

# filter dropdown data
@app.route('/admin/filters')
def get_filter_options():
    conn = sqlite3.connect('database/student_data.db')
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT course FROM student_details")
    courses = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT DATE(timestamp) FROM attendance_log ORDER BY timestamp DESC")
    dates = [row[0] for row in cursor.fetchall()]

    conn.close()
    return jsonify({
        "courses": courses,
        "dates": dates,
        "statuses": ["Marked", "Unmarked"]
    })


# ✅ Background OpenCV thread
@app.route('/start_recognition', methods=['POST'])
def start_recognition():
    from face_recognize import recognize_faces
    threading.Thread(target=recognize_faces).start()
    return jsonify({
        "message": {
            "text": "Attendance window opened!",
            "type": "info"
        }
    })

@app.route('/process_frame', methods=['POST'])
def process_frame():
    data = request.json
    frame_data = data['image']
    
     # Decode base64 image
    encoded_data = frame_data.split(',')[1]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Run recognition and get results
    result = recognize_from_frame(img)

    return jsonify({
        "message": {
            "text": result.get("text", ""),
            "type": result.get("type", "info")
        },
        "faces": result.get("faces", [])
    })


@app.route('/get_status', methods=['GET'])
def get_status():
    from message_store import latest_message, last_updated

    # Copy current message to return
    response = {
        "message": latest_message.copy(),
        "timestamp": last_updated
    }

    # Reset message so it's only sent once
    latest_message["text"] = ""
    latest_message["type"] = ""

    return jsonify(response)


# admin export attendance
@app.route('/admin/export-attendance')
def export_attendance():
    course = request.args.get('course')
    date = request.args.get('date')
    status = request.args.get('status')

    conn = sqlite3.connect('database/student_data.db')
    cursor = conn.cursor()

    # Step 1: Get all students filtered by course
    student_query = "SELECT roll_no, name, course FROM student_details"
    student_filters = []
    params = []

    if course:
        student_filters.append("course = ?")
        params.append(course)

    if student_filters:
        student_query += " WHERE " + " AND ".join(student_filters)

    cursor.execute(student_query, params)
    students = cursor.fetchall()

    # Step 2: Get marked attendance with timestamps for the selected date
    marked_attendance = {}
    if date:
        cursor.execute("""
            SELECT roll_no, TIME(timestamp) as time 
            FROM attendance_log 
            WHERE DATE(timestamp) = ?
        """, (date,))
        marked_attendance = {row[0]: row[1] for row in cursor.fetchall()}

    # Step 3: Prepare CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Roll No', 'Name', 'Course', 'Date', 'Time', 'Status'])

    for roll_no, name, course in students:
        present = roll_no in marked_attendance
        record_status = "Marked" if present else "Unmarked"

        if status == "Marked" and not present:
            continue
        if status == "Unmarked" and present:
            continue

        writer.writerow([
            roll_no, 
            name, 
            course, 
            date if date else 'All', 
            marked_attendance.get(roll_no, '-'), 
            record_status
        ])

    output.seek(0)

    conn.close()

    return Response(
        output,
        mimetype='text/csv',
        headers={
            "Content-Disposition": f"attachment; filename=attendance_export.csv"
        }
    )



if __name__ == '__main__':
    app.run(debug=True)
