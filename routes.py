from flask import render_template, Response, jsonify, request, redirect, url_for, session
import os
import json
import cv2
import mediapipe as mp
import pyautogui
import math
import numpy as np

# Global trạng thái
mouse_control_enabled = False
dragging = False

# Khởi tạo camera và Mediapipe
cap = cv2.VideoCapture(0)
screen_width, screen_height = pyautogui.size()
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

def register_routes(app):
    def generate_frames():
        global dragging, mouse_control_enabled
        while True:
            success, img = cap.read()
            img = cv2.flip(img, 1)
            h, w, _ = img.shape
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = hands.process(img_rgb)

            if results.multi_hand_landmarks:
                for handLms in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)
                    lm = handLms.landmark
                    x_index, y_index = int(lm[8].x * w), int(lm[8].y * h)
                    x_thumb, y_thumb = int(lm[4].x * w), int(lm[4].y * h)
                    x_middle, y_middle = int(lm[12].x * w), int(lm[12].y * h)

                    screen_x = np.interp(x_index, [0, w], [0, screen_width])
                    screen_y = np.interp(y_index, [0, h], [0, screen_height])

                    if mouse_control_enabled:
                        pyautogui.moveTo(screen_x, screen_y, duration=0.01)

                        dist_thumb_index = math.hypot(x_index - x_thumb, y_index - y_thumb)
                        if dist_thumb_index < 30 and not dragging:
                            pyautogui.mouseDown()
                            dragging = True
                        elif dist_thumb_index >= 30 and dragging:
                            pyautogui.mouseUp()
                            dragging = False

                        dist_thumb_middle = math.hypot(x_thumb - x_middle, y_thumb - y_middle)
                        if dist_thumb_middle < 40:
                            pyautogui.rightClick()

            _, buffer = cv2.imencode('.jpg', img)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    # ========== ROUTES ==========

    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/index')
    def index():
        return render_template('index.html')

    @app.route('/video')
    def video():
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/toggle-mouse')
    def toggle_mouse():
        global mouse_control_enabled
        mouse_control_enabled = not mouse_control_enabled
        return jsonify({'status': 'ok', 'enabled': mouse_control_enabled})

    @app.route('/mouse-status')
    def mouse_status():
        return jsonify({'enabled': mouse_control_enabled})

    # ========== AUTH ==========

    def load_users():
        if not os.path.exists('users.json'):
            return []
        with open('users.json', 'r') as f:
            return json.load(f)

    def save_users(users):
        with open('users.json', 'w') as f:
            json.dump(users, f, indent=4)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            users = load_users()
            username = request.form['username']
            password = request.form['password']
            for user in users:
                if user['username'] == username and user['password'] == password:
                    session['username'] = username
                    return redirect(url_for('index'))
            return render_template('login.html', error='Sai tài khoản hoặc mật khẩu!')
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            users = load_users()
            username = request.form['username']
            password = request.form['password']
            if any(user['username'] == username for user in users):
                return render_template('register.html', error='Tài khoản đã tồn tại!')
            users.append({'username': username, 'password': password})
            save_users(users)
            return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/logout')
    def logout():
        session.pop('username', None)
        return redirect(url_for('login'))
