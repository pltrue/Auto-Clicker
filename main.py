import sys
import time
import threading
import requests
import keyboard  # ใช้แทน pynput
from flask import Flask, render_template, request, jsonify
from pynput.mouse import Button, Controller
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QSystemTrayIcon, QMenu
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QIcon, QPixmap
from urllib.request import urlretrieve

# ✅ ดาวน์โหลดไอคอนจาก URL
icon_url = "https://cdn-icons-png.flaticon.com/128/3646/3646251.png"
icon_path = "icon.png"
urlretrieve(icon_url, icon_path)  # บันทึกเป็นไฟล์ icon.png

# --------------- [ FLASK BACKEND ] --------------- #
app = Flask(__name__)
mouse = Controller()
clicking = False
click_speed = 10  # ค่าเริ่มต้น CPS

# ฟังก์ชัน Auto Click
def clicker():
    global clicking
    while True:
        if clicking:
            mouse.click(Button.left)
        time.sleep(1 / max(1, click_speed))

# เริ่ม Thread สำหรับ Auto Click
click_thread = threading.Thread(target=clicker, daemon=True)
click_thread.start()

@app.route('/')
def index():
    return render_template('index.html', click_speed=click_speed)

@app.route('/toggle', methods=['POST'])
def toggle():
    global clicking
    clicking = not clicking
    return jsonify({'status': 'running' if clicking else 'stopped', 'click_speed': click_speed})

@app.route('/update_speed', methods=['POST'])
def update_speed():
    global click_speed
    click_speed = int(request.form['speed'])
    return jsonify({'click_speed': click_speed})

# --------------- [ PyQt6 GUI ] --------------- #
class AutoClickerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Auto Clicker")
        self.setFixedSize(600, 400)  # กำหนดขนาดหน้าต่างให้คงที่

        # ✅ ตั้งค่าไอคอนหน้าต่างหลัก
        self.setWindowIcon(QIcon(icon_path))

        # ✅ ใช้ QUrl เพื่อโหลด Flask WebView
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("http://127.0.0.1:5000/"))

        # Layout
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # ✅ เพิ่ม System Tray
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(icon_path))  # ใช้ไอคอนที่ดาวน์โหลดมา
        self.tray_icon.setToolTip("Auto Clicker")

        # สร้างเมนู System Tray
        menu = QMenu()
        show_action = menu.addAction("Show Window")
        exit_action = menu.addAction("Exit")
        show_action.triggered.connect(self.show)
        exit_action.triggered.connect(self.close_app)
        self.tray_icon.setContextMenu(menu)

        # ทำให้ Tray Icon ทำงาน
        self.tray_icon.show()

    def closeEvent(self, event):
        """ กดปิดแล้วซ่อนหน้าต่างแทน """
        event.ignore()
        self.hide()
        self.tray_icon.showMessage("Auto Clicker", "Running in Background", QSystemTrayIcon.MessageIcon.Information)

    def close_app(self):
        """ ออกจากโปรแกรม """
        QApplication.quit()

# --------------- [ Keyboard Listener ] --------------- #
def listen_keyboard():
    while True:
        keyboard.wait("s")  # รอให้กดปุ่ม S
        try:
            requests.post("http://127.0.0.1:5000/toggle")  # ✅ ส่งคำสั่งไปที่ Flask
        except requests.exceptions.ConnectionError:
            pass  # ป้องกัน Error ถ้า Flask ยังไม่ Start

# เริ่ม Listener สำหรับ Keyboard (รันใน Thread)
keyboard_thread = threading.Thread(target=listen_keyboard, daemon=True)
keyboard_thread.start()

# --------------- [ RUN APPLICATION ] --------------- #
def run_flask():
    app.run(debug=False, use_reloader=False)  # ปิด Debug Mode

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # เริ่ม GUI
    qt_app = QApplication(sys.argv)
    window = AutoClickerApp()
    window.show()
    sys.exit(qt_app.exec())
