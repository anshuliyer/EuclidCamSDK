import os
import socket
import shutil
from flask import Flask, render_template, send_from_directory, request, redirect, url_for, Response, send_file

app = Flask(__name__)

# Config
BASE_DIR = os.path.dirname(__file__)
PHOTO_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../Captured"))
os.makedirs(PHOTO_DIR, exist_ok=True)
STATIC_DIR = os.path.join(BASE_DIR, "static")
ASSETS_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../assets"))

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(ASSETS_DIR, filename)

def get_ip_address():
    try:
        import fcntl
        import struct
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip = socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', b'wlan0')
        )[20:24])
        return ip
    except Exception:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "10.42.0.1"

def generate_qr_code(url):
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, border=2, box_size=10)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        os.makedirs(STATIC_DIR, exist_ok=True)
        qr_path = os.path.join(STATIC_DIR, "qr_code.png")
        img.save(qr_path)
        return qr_path
    except Exception as e:
        print(f"[SERVER] QR generation note: {e}")
        return None

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
    
    # Verify files sorted by modification time (most recent first)
    raw_files = [f for f in os.listdir(PHOTO_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    files = sorted(raw_files, key=lambda f: os.path.getmtime(os.path.join(PHOTO_DIR, f)), reverse=True)
    
    server_ip = get_ip_address()
    server_url = f"http://{server_ip}:5000"
    generate_qr_code(server_url)
    
    storage = get_storage_info()
    
    return render_template('index.html', images=files, server_url=server_url, storage=storage)

# Generate QR on startup defensively
try:
    server_ip = get_ip_address()
    generate_qr_code(f"http://{server_ip}:5000")
except Exception as e:
    print(f"[SERVER] Startup QR generation note: {e}")

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

DEFAULT_MODES = ["Standard", "'90s", "Glam", "Low Light", "Summer", "Indoor", "35mm", "UnI", "Nostalgia"]

@app.route('/snapshot.jpg')
def snapshot():
    stream_path = "/tmp/euclidcam_stream.jpg"
    if os.path.exists(stream_path):
        try:
            return send_file(stream_path, mimetype='image/jpeg', max_age=0)
        except Exception:
            pass
    return "", 204

@app.route('/video_feed')
def video_feed():
    def gen_frames():
        stream_path = "/tmp/euclidcam_stream.jpg"
        while True:
            if os.path.exists(stream_path):
                try:
                    with open(stream_path, "rb") as f:
                        frame_bytes = f.read()
                    if frame_bytes and len(frame_bytes) > 100:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                except Exception:
                    pass
            time.sleep(0.06)
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/remote/status')
def remote_status():
    return {"modes": DEFAULT_MODES}, 200

@app.route('/api/remote/capture', methods=['GET', 'POST'])
def remote_capture():
    try:
        import json, time
        with open("/tmp/euclidcam_remote_cmd.json", "w") as f:
            json.dump({"cmd": "capture", "time": time.time()}, f)
        return {"success": True, "message": "Capture triggered"}, 200
    except Exception as e:
        return {"success": False, "message": str(e)}, 500

@app.route('/api/remote/mode', methods=['GET', 'POST'])
def remote_mode():
    try:
        import json, time
        data = request.get_json(silent=True) or request.form or request.args
        mode_idx = int(data.get("mode_idx", 0))
        with open("/tmp/euclidcam_remote_cmd.json", "w") as f:
            json.dump({"cmd": "set_mode", "mode_idx": mode_idx, "time": time.time()}, f)
        return {"success": True, "message": f"Mode set to {mode_idx}"}, 200
    except Exception as e:
        return {"success": False, "message": str(e)}, 500

@app.route('/api/remote/flash', methods=['GET', 'POST'])
def remote_flash():
    try:
        import json, time
        data = request.get_json(silent=True) or request.form or request.args
        flash_val = data.get("flash", True)
        if isinstance(flash_val, str):
            flash_val = flash_val.lower() in ("true", "1", "on")
        with open("/tmp/euclidcam_remote_cmd.json", "w") as f:
            json.dump({"cmd": "set_flash", "flash": bool(flash_val), "time": time.time()}, f)
        return {"success": True, "flash": bool(flash_val)}, 200
    except Exception as e:
        return {"success": False, "message": str(e)}, 500

@app.route('/api/remote/flash_blip', methods=['GET', 'POST'])
def remote_flash_blip():
    try:
        import json, time
        with open("/tmp/euclidcam_remote_cmd.json", "w") as f:
            json.dump({"cmd": "flash_blip", "time": time.time()}, f)
        return {"success": True}, 200
    except Exception as e:
        return {"success": False, "message": str(e)}, 500

@app.route('/api/remote/grid', methods=['GET', 'POST'])
def remote_grid():
    try:
        import json, time
        data = request.get_json(silent=True) or request.form or request.args
        grid_val = str(data.get("grid", "OFF")).upper()
        with open("/tmp/euclidcam_remote_cmd.json", "w") as f:
            json.dump({"cmd": "set_grid", "grid": grid_val, "time": time.time()}, f)
        return {"success": True, "grid": grid_val}, 200
    except Exception as e:
        return {"success": False, "message": str(e)}, 500

@app.route('/api/wifi/config', methods=['POST'])
def wifi_config():
    try:
        data = request.get_json(silent=True) or request.form
        ssid = data.get('ssid', '').strip()
        password = data.get('password', '').strip()
        
        if not ssid:
            return {"success": False, "message": "SSID is required"}, 400
            
        try:
            from wifi_utils import connect_to_wifi
        except ImportError:
            from connectivity.wifi_utils import connect_to_wifi
            
        success, message = connect_to_wifi(ssid, password)
        if success:
            try:
                import json
                status_file = "/tmp/euclidcam_wifi_status.json"
                with open(status_file, "w") as f:
                    json.dump({"status": "connected", "ssid": ssid}, f)
            except Exception as ex:
                print(f"[SERVER] Failed to write status file: {ex}")
        return {"success": success, "message": message}, (200 if success else 400)
    except Exception as e:
        return {"success": False, "message": str(e)}, 500

if __name__ == '__main__':
    # Run server on all interfaces so it's accessible over network
    app.run(host='0.0.0.0', port=5000, debug=False)
