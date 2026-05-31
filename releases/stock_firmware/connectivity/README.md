# connectivity/

| File            | Role                                                              |
|-----------------|-------------------------------------------------------------------|
| `server.py`     | Flask server, serves the `Captured/` directory over HTTP port 5000|
| `wifi_utils.py` | Gets device IP, generates QR code string for display             |

**Flow:** User selects Connect → `ServerManager.start()` spawns `server.py` as a subprocess → QR code rendered on display with `http://<ip>:5000` → any device on the same network can browse and download photos.

Stop via **Connect → Stop Conn** in settings menu.
