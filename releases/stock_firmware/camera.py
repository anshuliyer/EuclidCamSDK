import main
from IO import gpio_top as io_stubs

from UI.settings import ORIENTATION

# Initialize Hardware Interfaces
battery = io_stubs.BatteryManagement()
gpio = io_stubs.GPIOTop()

# UI Configuration
CONFIG = {
    "flash": gpio.flash_setting,      # Flash switchable (ON right now)
    "battery": battery.battery_level, # Battery status
    "wifi": None,       # Placeholder
    "photo_dir": "../../Captured",
    "ui_rotation": ORIENTATION,    # Rotation in degrees (0, 90, 180, 270)
    "ui_padding": 20     # Padding from edges
}

def start_camera():
    """
    Entry point to start the EuclidCam camera logic.
    """
    print("[SYSTEM] Starting EuclidCam Camera...")
    main.run(CONFIG)

if __name__ == "__main__":
    start_camera()
