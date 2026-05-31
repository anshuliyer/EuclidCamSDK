import os
import sys
import json
import time
import mmap
import numpy as np
from PIL import Image, ImageDraw

try:
    import evdev
    from evdev import ecodes
except ImportError:
    print("[ERROR] evdev not found. Please install it with: pip install evdev")
    sys.exit(1)

# Configuration
FB_DEVICE = "/dev/fb1"
SCREEN_RES = (480, 320)
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "touch_settings.json")

def display_to_map(data_array, fb_map):
    """Writes a numpy array (RGB888) to the framebuffer (RGB565)."""
    r = data_array[:, :, 0].astype(np.uint16)
    g = data_array[:, :, 1].astype(np.uint16)
    b = data_array[:, :, 2].astype(np.uint16)
    
    # RGB565 conversion (Little Endian)
    rgb565 = ((b >> 3) << 11) | ((g >> 2) << 5) | (r >> 3)
    fb_map.seek(0)
    fb_map.write(rgb565.tobytes())

def get_touch_device():
    """Finds the touchscreen device among evdev inputs."""
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if "touchscreen" in device.name.lower() or "ads7846" in device.name.lower():
            return device
    return None

def calibrate():
    """Runs a calibration routine to map raw touch coordinates to screen pixels."""
    device = get_touch_device()
    if not device:
        print("[ERROR] Touchscreen device not found. Check connections and drivers.")
        return

    print(f"[SYSTEM] Found touchscreen: {device.name}")
    print("[SYSTEM] Starting calibration. Please tap the red dots on the screen.")

    points = [
        (50, 50),                 # Top-left
        (SCREEN_RES[0] - 50, 50),  # Top-right
        (50, SCREEN_RES[1] - 50),  # Bottom-left
        (SCREEN_RES[0] - 50, SCREEN_RES[1] - 50) # Bottom-right
    ]
    
    raw_samples = []

    try:
        with open(FB_DEVICE, "r+b") as f:
            map_size = SCREEN_RES[0] * SCREEN_RES[1] * 2
            with mmap.mmap(f.fileno(), map_size) as fb_map:
                for target_x, target_y in points:
                    # Draw calibration screen
                    img = Image.new("RGB", SCREEN_RES, (0, 0, 0))
                    draw = ImageDraw.Draw(img)
                    draw.ellipse([target_x-10, target_y-10, target_x+10, target_y+10], fill=(255, 0, 0))
                    draw.text((SCREEN_RES[0]//2 - 60, SCREEN_RES[1]//2), f"Tap the red dot", fill=(255, 255, 255))
                    
                    display_to_map(np.array(img), fb_map)
                    
                    # Capture raw touch
                    print(f"Waiting for tap at ({target_x}, {target_y})...")
                    x_raw, y_raw = None, None
                    for event in device.read_loop():
                        if event.type == ecodes.EV_ABS:
                            if event.code == ecodes.ABS_X:
                                x_raw = event.value
                            elif event.code == ecodes.ABS_Y:
                                y_raw = event.value
                        elif event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH and event.value == 0:
                            # Touch released
                            if x_raw is not None and y_raw is not None:
                                raw_samples.append((x_raw, y_raw))
                                break
                    time.sleep(0.5)

    except Exception as e:
        print(f"[ERROR] Calibration failed: {e}")
        return

    # Simple linear calibration: raw = (screen * scale) + offset
    # We'll calculate min/max raw values to map to screen bounds
    x_raws = [p[0] for p in raw_samples]
    y_raws = [p[1] for p in raw_samples]
    
    config = {
        "x_min": min(x_raws),
        "x_max": max(x_raws),
        "y_min": min(y_raws),
        "y_max": max(y_raws),
        "screen_width": SCREEN_RES[0],
        "screen_height": SCREEN_RES[1],
        "swap_xy": False, # Adjust if orientation is off
        "invert_x": False,
        "invert_y": False
    }

    with open(CONFIG_FILE, "w") as jf:
        json.dump(config, jf, indent=4)

    print(f"[SUCCESS] Calibration saved to {CONFIG_FILE}")

def get_calibrated_touch(raw_x, raw_y, config):
    """Maps raw coordinates to screen pixels based on saved config."""
    x = (raw_x - config["x_min"]) / (config["x_max"] - config["x_min"]) * config["screen_width"]
    y = (raw_y - config["y_min"]) / (config["y_max"] - config["y_min"]) * config["screen_height"]
    
    if config.get("invert_x"): x = config["screen_width"] - x
    if config.get("invert_y"): y = config["screen_height"] - y
    
    return int(max(0, min(config["screen_width"], x))), int(max(0, min(config["screen_height"], y)))

if __name__ == "__main__":
    calibrate()
