import os
import json

try:
    import evdev
    from evdev import ecodes
except ImportError:
    evdev = None

class TouchInterface:
    def __init__(self, config_path, screen_res):
        self.device = self._find_touch_device()
        self.config = self._load_config(config_path)
        self.screen_res = screen_res
        self.last_x = 0
        self.last_y = 0
        self.touch_active = False

    def _find_touch_device(self):
        if not evdev: return None
        try:
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            for dev in devices:
                if "touchscreen" in dev.name.lower() or "ads7846" in dev.name.lower():
                    return dev
        except:
            pass
        return None

    def _load_config(self, path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            return None

    def get_touch_command(self, ui_state):
        if not self.device or not self.config: return None
        
        try:
            while True: # Drain the event queue
                event = self.device.read_one()
                if event is None: break
                
                if event.type == ecodes.EV_ABS:
                    if event.code == ecodes.ABS_X: self.last_x = event.value
                    if event.code == ecodes.ABS_Y: self.last_y = event.value
                elif event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
                    if event.value == 1: # Touch start
                        self.touch_active = True
                    else: # Touch release
                        self.touch_active = False
                        cmd, x, y = self._map_to_command(self.last_x, self.last_y, ui_state)
                        if cmd:
                            print(f"[TOUCH] {cmd} at ({int(x)}, {int(y)})")
                        return cmd
        except Exception as e:
            pass
        return None

    def _map_to_command(self, raw_x, raw_y, ui_state):
        c = self.config
        if c.get("swap_xy"): raw_x, raw_y = raw_y, raw_x
        
        x_norm = (raw_x - c["x_min"]) / (c["x_max"] - c["x_min"])
        y_norm = (raw_y - c["y_min"]) / (c["y_max"] - c["y_min"])
        if c.get("invert_x"): x_norm = 1.0 - x_norm
        if c.get("invert_y"): y_norm = 1.0 - y_norm
        
        # Apply orientation flip if set to 180
        if ui_state.get("ui_rotation") == 180:
            x_norm = 1.0 - x_norm
            y_norm = 1.0 - y_norm
        
        x = x_norm * self.screen_res[0]
        y = y_norm * self.screen_res[1]
        w, h = self.screen_res

        # --- Layer 1: High Priority Overlays (Gallery/Connection) ---
        if ui_state.get("show_connection_view"):
            overlay_w, overlay_h = 300, 240
            ox, oy = (w - overlay_w) // 2, (h - overlay_h) // 2
            # Expand the close button (cross) hitbox for easier tapping
            if (x > ox + overlay_w - 80 and y < oy + 80) or (x < ox or x > ox + overlay_w or y < oy or y > oy + overlay_h):
                return "BACK", x, y
            # Block fallthrough: if they tapped inside the QR box but missed the cross, ignore the touch
            return None, x, y

        if ui_state.get("show_gallery"):
            # 1. Delete Button (Top Left)
            if x < 130 and y < 85: return "DOWN", x, y
            
            # 2. Exit Gallery (Top Right Cross - Matching Settings)
            if x > w - 80 and y < 80: return "BACK", x, y
            
            # 3. Navigation (Sides)
            return ("LEFT" if x < w // 2 else "RIGHT"), x, y

        # --- Layer 2: Menu System (Grid + Header) ---
        if ui_state.get("show_menu"):
            # Massive Cross Button Area (Top Right)
            if x > w - 80 and y < 80: return "BACK", x, y
            
            # Grid Detection (Prioritize this over edge-back)
            sub = ui_state.get("current_submenu")
            is_sub = ui_state.get("show_submenu")
            
            if is_sub and sub == "Modes": max_items, cols, rows = 8, 4, 2
            elif is_sub and (sub == "Grid" or sub == "Connect"): max_items, cols, rows = 3, 3, 1
            else: max_items, cols, rows = 4, 4, 1
            
            grid_m_x, grid_m_y, header_h, gap = 25, 15, 65, 12
            avail_w = w - (grid_m_x * 2)
            avail_h = h - header_h - (grid_m_y * 2)
            btn_w = (avail_w - (gap * (cols - 1))) // cols
            btn_h = (avail_h - (gap * (rows - 1))) // rows
            
            rel_x = x - grid_m_x
            rel_y = y - (header_h + grid_m_y)
            
            col = int(rel_x // (btn_w + gap))
            row = int(rel_y // (btn_h + gap))
            
            if 0 <= col < cols and 0 <= row < rows:
                lx, ly = rel_x % (btn_w + gap), rel_y % (btn_h + gap)
                if lx < btn_w and ly < btn_h:
                    idx = row * cols + col
                    if idx < max_items:
                        ui_state["touch_menu_idx"] = idx
                        return "TOUCH_SELECT", x, y
            
            # If in menu area but not on a button, check for edge close (Strict)
            if x < 10 or x > w - 10 or y > h - 10:
                return "BACK", x, y

        # --- Layer 3: Main UI State ---
        # Gear (Bottom Right)
        if x > w - 85 and y > h - 85: return "SPACE", x, y
        # Gallery (Bottom Left)
        if x < 85 and y > h - 85: return "GALLERY", x, y
        # Capture (Center)
        if not ui_state.get("show_menu") and not ui_state.get("show_gallery"):
            if 80 < x < w - 80 and 80 < y < h - 80: return "ENTER", x, y

        return None, x, y
