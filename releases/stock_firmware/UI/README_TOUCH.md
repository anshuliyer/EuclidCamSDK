# EuclidCam Touchscreen Configuration Guide

This guide explains how to set up, calibrate, and use a 3.5" TFT Touchscreen with the Raspberry Pi Zero 2W for EuclidCam.

## 1. Hardware Connection
Ensure the 3.5" TFT display is correctly mounted on the 40-pin GPIO header of the Pi Zero 2W.
- **Interface:** SPI
- **Resolution:** 480x320

## 2. Driver Installation
EuclidCam is designed for displays using the `ADS7846` touch controller and `ILI9486` LCD driver (common for WaveShare 3.5a clones).

### Step A: Enable SPI
1. Run `sudo raspi-config`.
2. Go to **Interface Options** -> **SPI** -> **Yes**.
3. Finish and reboot.

### Step B: Install the LCD Driver
We recommend using the standard `LCD-show` repository:
```bash
git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show
cd LCD-show/
sudo ./LCD35-show
```
The Pi will automatically reboot. The display should now show the console or desktop.

## 3. Calibration
EuclidCam provides a custom Python-based calibration utility to map touch events precisely to the UI.

### Install Dependencies
```bash
pip3 install evdev numpy Pillow
```

### Run Calibration
From the `firmware/python/UI` directory:
```bash
python3 touch_config.py
```
1. A red dot will appear in each of the four corners of the screen sequentially.
2. Tap each dot as accurately as possible.
3. The script will generate `touch_settings.json` with the calibration data.

## 4. Integration with EuclidCam
To enable touch in the main application, the `main.py` loop should be updated to read from the touch device.

### Example Usage in Code:
```python
import json
from UI.touch_config import get_calibrated_touch

# Load config
with open("UI/touch_settings.json", "r") as f:
    t_config = json.load(f)

# Inside input loop:
# raw_x, raw_y = get_raw_touch_from_evdev()
# x, y = get_calibrated_touch(raw_x, raw_y, t_config)
# handle_touch_event(x, y)
```

## 5. Troubleshooting
- **Screen is White:** Ensure the driver is installed correctly. Check `/boot/config.txt` for `dtoverlay=tft35a`.
- **Touch is Inverted:** Edit `touch_settings.json` and set `invert_x` or `invert_y` to `true`.
- **No Device Found:** Run `ls /dev/input/` to see if touch devices are listed.
