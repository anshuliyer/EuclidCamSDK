import os
import socket
import qrcode
import shutil
from flask import Flask, render_template, send_from_directory, request, redirect, url_for

app = Flask(__name__)

# Config
BASE_DIR = os.path.dirname(__file__)
PHOTO_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../Captured"))
STATIC_DIR = os.path.join(BASE_DIR, "static")

def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def generate_qr_code(url):
    qr = qrcode.QRCode(version=1, border=2, box_size=10)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    qr_path = os.path.join(STATIC_DIR, "qr_code.png")
    img.save(qr_path)
    return qr_path

def get_storage_info():
    try:
        usage = shutil.disk_usage(PHOTO_DIR)
        free_gb = usage.free / (1024**3)
        total_gb = usage.total / (1024**3)
        percent = (usage.used / usage.total) * 100
        return {
            "free": f"{free_gb:.1f} GB",
            "total": f"{total_gb:.1f} GB",
            "percent": round(percent, 1)
        }
    except Exception:
        return {"free": "Unknown", "total": "Unknown", "percent": 0}

@app.route('/')
def index():
    if not os.path.exists(PHOTO_DIR):
        os.makedirs(PHOTO_DIR, exist_ok=True)
    
    # Verify files
    files = sorted([f for f in os.listdir(PHOTO_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))], reverse=True)
    
    server_ip = get_ip_address()
    server_url = f"http://{server_ip}:5000"
    generate_qr_code(server_url)
    
    storage = get_storage_info()
    
    return render_template('index.html', images=files, server_url=server_url, storage=storage)

# Generate QR on startup
server_ip = get_ip_address()
generate_qr_code(f"http://{server_ip}:5000")

@app.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory(PHOTO_DIR, filename)

@app.route('/download/<filename>')
def download_image(filename):
    return send_from_directory(PHOTO_DIR, filename, as_attachment=True)

@app.route('/delete/<filename>', methods=['POST'])
def delete_image(filename):
    img_path = os.path.join(PHOTO_DIR, filename)
    if os.path.exists(img_path):
        os.remove(img_path)
    return redirect(url_for('index'))

@app.route('/delete-batch', methods=['POST'])
def delete_batch():
    data = request.get_json()
    filenames = data.get('filenames', [])
    for filename in filenames:
        img_path = os.path.join(PHOTO_DIR, filename)
        if os.path.exists(img_path):
            os.remove(img_path)
    return {"status": "success"}, 200

if __name__ == '__main__':
    # Run server on all interfaces so it's accessible over network
    app.run(host='0.0.0.0', port=5000, debug=False)
