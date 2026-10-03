import os
import cv2
import requests
import numpy as np
import time
import threading
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# 1. ตั้งค่า DroidCam RTSP และ LINE Access Token
RTSP_URL = "http://192.168.1.151:4747/video"
LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN", "ใส่_LINE_ACCESS_TOKEN_ของคุณ")

# สร้างโฟลเดอร์สำหรับเก็บรูปภาพเบื้องหลังถ้ายังไม่มี
SAVE_DIR = "captured_images"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# 2. ฟังก์ชันส่งข้อความแจ้งเตือนผ่าน LINE Broadcast
def send_line_message(message):
    url = "jnlApIVgKhlzKwr+VrcJ5qTrb7z3pS0PuGFoHAj9Is3J++VGcUCQBiDK+qctLF+wSAmeQQ+gxwOpSNhCFSctSYf0lQX0HwMLxYfCWY7lvAvled5mxpKu56vdhTrLc+jwQ85FoEPWsgZCHFALoeWwYwdB04t89/1O/w1cDnyilFU="
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    data = {
        "messages": [
            {"type": "text", "text": message}
        ]
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        print("LINE notification status:", response.status_code)
    except Exception as e:
        print("Error sending LINE notification:", e)

# 3. ฟังก์ชันบันทึกรูปภาพลงโฟลเดอร์เบื้องหลัง
def save_captured_frame(frame):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"person_{timestamp}.jpg"
    filepath = os.path.join(SAVE_DIR, filename)
    
    # บันทึกรูปภาพลงโฟลเดอร์
    cv2.imwrite(filepath, frame)
    print(f"📸 บันทึกรูปภาพสำเร็จ: {filepath}")
    return filepath

# 4. ระบบตรวจจับคนจาก DroidCam (Background Thread)
def detect_people():
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    cap = cv2.VideoCapture(RTSP_URL)
    last_notify_time = 0
    notify_cooldown = 10  # หน่วงเวลาแจ้งเตือนอย่างน้อย 10 วินาที

    print("เริ่มต้นระบบตรวจจับคนและบันทึกภาพจาก DroidCam...")

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(2)
            cap = cv2.VideoCapture(RTSP_URL)
            continue

        frame_resized = cv2.resize(frame, (640, 480))
        boxes, weights = hog.detectMultiScale(frame_resized, winStride=(8, 8), padding=(8, 8), scale=1.05)

        if len(boxes) > 0:
            current_time = time.time()
            if current_time - last_notify_time > notify_cooldown:
                # บันทึกรูปภาพลงดิสก์เบื้องหลัง
                img_path = save_captured_frame(frame_resized)
                
                # ส่งแจ้งเตือนผ่าน LINE
                message = f"🚨 ตรวจพบคนผ่าน DroidCam! จำนวน: {len(boxes)} คน\nบันทึกภาพไว้ที่: {os.path.basename(img_path)}"
                send_line_message(message)
                
                last_notify_time = current_time

# รันระบบตรวจจับคนแบบ Thread แยกทำงานด้านหลัง
threading.Thread(target=detect_people, daemon=True).start()

# 5. หน้า Web Server (Flask) สำหรับ Render และเปิดดูรูปภาพที่บันทึกไว้
@app.route("/", methods=["GET"])
def home():
    return "VLDAR Bot (DroidCam + Detection + Save Image + LINE) is running!"

@app.route("/images/<filename>", methods=["GET"])
def get_image(filename):
    return send_from_directory(SAVE_DIR, filename)

@app.route("/webhook", methods=["POST"])
def webhook():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
