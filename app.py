from flask import Flask, render_template, request, jsonify
import threading
import cv2
import numpy as np
import base64
from face_recognize import recognize_from_frame
import message_store

app = Flask(__name__)


@app.route('/')
def home():
    return render_template("index.html")

@app.route('/login')
def login():
    return render_template("login.html")

# ✅ Background OpenCV thread
@app.route('/start_recognition', methods=['POST'])
def start_recognition():
    from face_recognize import recognize_faces
    threading.Thread(target=recognize_faces).start()
    return jsonify({
        "message": {
            "text": "📸 Attendance window opened. Please check the camera.",
            "type": "info"
        }
    })

@app.route('/process_frame', methods=['POST'])
def process_frame():
    data = request.json
    frame_data = data['image']
    
    encoded_data = frame_data.split(',')[1]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    result = recognize_from_frame(img)

    return jsonify({"message": result})


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



if __name__ == '__main__':
    app.run(debug=True)
