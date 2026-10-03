import os
import cv2
import requests
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# --- LINE Notification Setup ---
LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN", "")

def send_line_message(message):
    if not LINE_ACCESS_TOKEN:
        return
    url = 'jnlApIVgKhlzKwr+VrcJ5qTrb7z3pS0PuGFoHAj9Is3J++VGcUCQBiDK+qctLF+wSAmeQQ+gxwOpSNhCFSctSYf0lQX0HwMLxYfCWY7lvAvled5mxpKu56vdhTrLc+jwQ85FoEPWsgZCHFALoeWwYwdB04t89/1O/w1cDnyilFU='
    headers = {'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
    data = {'message': message}
    try:
        requests.post(url, headers=headers, data=data)
    except Exception as e:
        print(f"Error sending LINE alert: {e}")

# --- Video Stream Generator ---
def generate_frames():
    # ใช้กล้อง webcam/DroidCam (index http://192.168.1.151:4747/video)
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # ตรงนี้สามารถใส่ logic การตรวจจับวัตถุ (Detection) เพิ่มเติมได้
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# --- OriginOS Styled HTML Template ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="th" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VLDAR Bot Dashboard</title>
    <style>
        :root[data-theme="dark"] {
            --bg-color: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --text-color: #f8fafc;
            --border-color: rgba(255, 255, 255, 0.1);
            --accent-color: #38bdf8;
        }
        :root[data-theme="light"] {
            --bg-color: #f1f5f9;
            --card-bg: rgba(255, 255, 255, 0.8);
            --text-color: #0f172a;
            --border-color: rgba(0, 0, 0, 0.1);
            --accent-color: #0284c7;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
            transition: all 0.3s ease;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .theme-btn {
            background: var(--card-bg);
            color: var(--text-color);
            border: 1px solid var(--border-color);
            padding: 8px 16px;
            border-radius: 20px;
            cursor: pointer;
            backdrop-filter: blur(10px);
        }
        .grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 24px;
            padding: 20px;
            backdrop-filter: blur(16px);
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
        }
        .video-feed {
            width: 100%;
            border-radius: 16px;
            background: #000;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            background: #22c55e;
            color: white;
            font-size: 0.8em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>VLDAR Bot Dashboard</h2>
            <button class="theme-btn" onclick="toggleTheme()">🌓 สลับธีม สว่าง/มืด</button>
        </div>
        <div class="grid">
            <div class="card">
                <h3>Camera Feed (Live)</h3>
                <img src="/video_feed" class="video-feed" alt="Live Stream">
            </div>
            <div class="card">
                <h3>System Status</h3>
                <p>Status: <span class="status-badge">ONLINE</span></p>
                <p>Detection: Active</p>
                <p>LINE Notify: Connected</p>
            </div>
        </div>
    </div>
    <script>
        function toggleTheme() {
            const html = document.documentElement;
            const current = html.getAttribute('data-theme');
            html.setAttribute('data-theme', current === 'dark' ? 'light' : 'dark');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
