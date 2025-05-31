# ML_BASED_ATTENDANCE

This is a **Face Recognition-based Attendance System** built using **Python, Flask, and OpenCV**. It recognizes students' faces in real time using a webcam and automatically marks their attendance.

The system includes both student and admin interfaces, attendance logs, filtering options, and CSV export functionality.

## 🧠 Core Components

- **Face Recognition & Attendance**  
  Real-time face detection via webcam using the `face_recognition` library, with attendance logged in a SQLite database.

- **Face Encoding**  
  Encodes student images from a folder (`data/images/`), storing metadata and encodings in both a database and a `.pkl` file.

- **Flask Web App**  
  A user-friendly web interface for students and admins, offering dashboard views, filtering options, and attendance exports.

## 🗃️ Database Structure

- `student_details` — Stores student info and facial encodings  
- `attendance_log` — Records date, time, and attendance status

## 🔁 Workflow

1. Encode student face images at startup.
2. Webcam captures video and recognizes faces in real time.
3. Recognized students are marked as present automatically.
4. Admins can view, filter, and export attendance data.

## 🛠️ Technologies Used

- **Python 3**
- **Flask**
- **OpenCV**
- **face_recognition**
- **SQLite**
- **Pickle**

## 🚀 Getting Started

- Clone the repository:  
  ```bash
  git clone https://github.com/yourusername/Face-Recognition-Attendance-System.git
