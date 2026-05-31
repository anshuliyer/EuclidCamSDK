"""
EuclidCam — Main Camera Engine
=================================
Entry point and core orchestration for the EuclidCam firmware.

Architecture
------------
  CameraEngine          – owns the main loop, framebuffer, and config dict
    ├── GalleryManager  – photo listing, navigation, and deletion
    ├── ServerManager   – Flask subprocess lifecycle
    └── InputHandler    – decodes touch commands into domain actions

  CameraMode (base)
    ├── StandardMode    – clean crop, no filter
    ├── FilterMode      – any PIL filter module
    └── LowLightMode    – high-gain, noise-reduced capture
"""

from __future__ import annotations

# ─── Standard library ──────────────────────────────────────────────────────────
import mmap
import os
import subprocess
import sys
import threading
import time
from typing import Any

# ─── Third-party ───────────────────────────────────────────────────────────────
import numpy as np
from picamera2 import Picamera2
from PIL import Image, ImageDraw, ImageFont

# ─── Project: UI ───────────────────────────────────────────────────────────────
from UI import ui_top, touch_interface

# ─── Project: Filters ──────────────────────────────────────────────────────────
from filters import italian_summer, indoor, film35mm, uni, nostalgia, low_light, glam, disco

# ─── Project: Settings ─────────────────────────────────────────────────────────
from settings import grid as grid_settings

# ─── Project: Connectivity ─────────────────────────────────────────────────────
from connectivity import wifi_utils

# ─── Project: IO ───────────────────────────────────────────────────────────────
from IO import gpio_top as io_stubs
from IO import flash

# ─── Hardware constants ────────────────────────────────────────────────────────
FB_DEVICE: str   = "/dev/fb1"
SCREEN_RES: tuple = (480, 320)
FPS_CAP: int     = 8

# ─── Shared camera object ─────────────────────────────────────────────────────
picam2 = Picamera2()


# ==============================================================================
#  Helpers
# ==============================================================================

def display_to_map(data_array: np.ndarray, fb_map, config: dict = None) -> None:
    """Convert an RGB888 numpy array to RGB565 and write it to the framebuffer."""
    if config and config.get("ui_rotation") == 180:
        data_array = np.rot90(data_array, 2)
        
    data = data_array.astype(np.uint16)
    r = data[:, :, 0] >> 3
    g = (data[:, :, 1] >> 2) << 5
    b = (data[:, :, 2] >> 3) << 11
    fb_map[:] = (r | g | b).tobytes()


def start_preview() -> None:
    """Configure picam2 for the live preview stream."""
    cfg = picam2.create_video_configuration(
        main={"size": SCREEN_RES, "format": "RGB888"}
    )
    cfg["controls"] = {"Contrast": 1.03, "Brightness": 0.02, "Sharpness": 1.1}
    picam2.configure(cfg)
    picam2.start()


# ==============================================================================
#  CameraMode hierarchy
# ==============================================================================

class CameraMode:
    """Abstract base for all camera modes."""

    def __init__(self, name: str) -> None:
        self.name = name

    # ── Image processing ──────────────────────────────────────────────────────

    def _crop_and_zoom(
        self,
        pil_img: Image.Image,
        target_ratio: float = 1.5,
        zoom: float = 1.0,
    ) -> Image.Image:
        """
        Centre-crop to *target_ratio* (3:2) and apply a *zoom* factor to
        remove wide-angle lens distortion.  zoom=1.0 → pure 3:2 crop.
        """
        w, h = pil_img.size
        if w / h > target_ratio:
            crop_w, crop_h = h * target_ratio, float(h)
        else:
            crop_w, crop_h = float(w), w / target_ratio

        final_w = crop_w / zoom
        final_h = crop_h / zoom
        left   = (w - final_w) / 2
        top    = (h - final_h) / 2
        return pil_img.crop((left, top, left + final_w, top + final_h))

    def apply_filter(self, pil_img: Image.Image) -> Image.Image:
        """Apply mode-specific colour grading.  Override in subclasses."""
        return pil_img

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Transform a raw preview frame for display.  Override in subclasses."""
        return frame

    # ── Capture overlay ───────────────────────────────────────────────────────

    def _draw_capture_overlay(
        self, fb_map, config: dict, text: str, progress: float = 0.0
    ) -> None:
        """Render the branded capture/processing overlay to the framebuffer."""
        from UI.themes import chalk as theme

        w, h = SCREEN_RES
        img  = Image.new("RGB", SCREEN_RES, theme.BG_CHARCOAL)
        draw = ImageDraw.Draw(img)

        # Background watermark logo
        cx, cy = w // 2, h // 2 - 30
        try:
            logo_path = os.path.join(
                os.path.dirname(__file__),
                "../../splashscreen/transparent_logo.png",
            )
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((250, 250), Image.LANCZOS)
            r_, g_, b_, a_ = logo.split()
            a_ = a_.point(lambda i: i * theme.LOGO_OPACITY)
            logo = Image.merge("RGBA", (r_, g_, b_, a_))
            lw, lh = logo.size
            img.paste(logo, (cx - lw // 2, cy - lh // 2), logo)
        except Exception as e:
            print(f"[UI] Logo load failed: {e}")
            try:
                font_logo = ImageFont.truetype(theme.FONT_BOLD, 60)
                draw.text((cx - 20, cy - 30), "E", fill=(255, 255, 255), font=font_logo)
            except Exception:
                pass

        # Main status text — small, centred
        try:
            font_text = ImageFont.truetype(theme.FONT_BOLD, 22)
            if hasattr(draw, "textbbox"):
                bbox = draw.textbbox((0, 0), text, font=font_text)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
            else:
                tw, th = len(text) * 12, 22
            tx = (w - tw) // 2
            ty = h // 2 + 50 - th // 2
            draw.text((tx, ty), text, fill=(255, 255, 255), font=font_text)
        except Exception:
            draw.text((w // 2 - 40, h // 2 + 50), text, fill=(255, 255, 255))

        # Progress bar
        if progress > 0:
            bw, bh = theme.PROGRESS_BAR_WIDTH, theme.PROGRESS_BAR_HEIGHT
            bx, by = (w - bw) // 2, h // 2 + 90
            draw.rectangle([bx, by, bx + bw, by + bh], outline=(80, 80, 100), width=1)
            draw.rectangle(
                [bx, by, bx + int(bw * progress), by + bh],
                fill=theme.MAUVE_PRIMARY,
            )

        display_to_map(np.array(img), fb_map, config=config)

    # ── Hardware capture ──────────────────────────────────────────────────────

    def _do_capture_raw(self, controls: dict) -> Image.Image:
        """
        Switch picam2 into still mode, apply *controls*, shoot, and return a
        full-resolution PIL image.  Always restores preview afterwards.
        """
        picam2.stop()
        cfg = picam2.create_still_configuration()
        cfg["controls"] = controls
        picam2.configure(cfg)
        picam2.start()
        time.sleep(0.4)
        picam2.capture_file("temp.jpg")
        return Image.open("temp.jpg").convert("RGB")

    def capture(self, fb_map, config: dict, flash_drive: Any = None) -> None:
        """Standard capture pipeline shared by most modes."""
        photo_dir = config.get("photo_dir", ".")
        os.makedirs(photo_dir, exist_ok=True)

        print(f"\n[SHUTTER] Capturing in {self.name} mode…")
        self._draw_capture_overlay(fb_map, config, "HOLD STILL")

        # Physical Flash
        if config.get("flash") and flash_drive:
            import threading
            threading.Thread(target=flash_drive.trigger, args=(1.0,), daemon=True).start()

        # Screen Flash
        flash = np.full((SCREEN_RES[1], SCREEN_RES[0], 3), 255, dtype=np.uint8)
        display_to_map(flash, fb_map, config=config)

        self._draw_capture_overlay(fb_map, config, "PROCESSING…", progress=0.2)
        raw = self._do_capture_raw({
            "Contrast": 1.05, "Sharpness": 2.0,
            "AeExposureMode": 1, "AnalogueGain": 4.0,
        })

        self._draw_capture_overlay(fb_map, config, "APPLYING VISION…", progress=0.5)
        processed = self.apply_filter(raw)

        self._draw_capture_overlay(fb_map, config, "SAVING…", progress=0.8)
        filename = os.path.join(
            photo_dir, f"{self.name.lower()}_{int(time.time())}.jpg"
        )
        processed.save(filename, quality=95)

        self._draw_capture_overlay(fb_map, config, "DONE!", progress=1.0)
        time.sleep(0.3)

        review = processed.resize(SCREEN_RES, Image.LANCZOS)
        display_to_map(np.array(review), fb_map, config=config)
        time.sleep(1.5)

        picam2.stop()
        start_preview()


# ─── Concrete modes ────────────────────────────────────────────────────────────

class StandardMode(CameraMode):
    """Clean capture: crop + zoom only, no colour grading."""

    def __init__(self) -> None:
        super().__init__("Standard")

    def apply_filter(self, pil_img: Image.Image) -> Image.Image:
        return self._crop_and_zoom(pil_img)

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        img = self._crop_and_zoom(Image.fromarray(frame))
        return np.array(img.resize(SCREEN_RES, Image.LANCZOS))


class FilterMode(CameraMode):
    """
    Generic filter mode: auto-discovers the ``apply_*_filter`` function
    inside any filter module and applies it after cropping.
    """

    def __init__(self, name: str, filter_module) -> None:
        super().__init__(name)
        self.filter_module = filter_module
        self.filter_func = next(
            (
                getattr(filter_module, attr)
                for attr in dir(filter_module)
                if attr.startswith("apply_") and attr.endswith("_filter")
            ),
            None,
        )

    def apply_filter(self, pil_img: Image.Image) -> Image.Image:
        img = self._crop_and_zoom(pil_img)
        return self.filter_func(img) if self.filter_func else img

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        img = self._crop_and_zoom(Image.fromarray(frame))
        img = img.resize(SCREEN_RES, Image.LANCZOS)
        if self.filter_func:
            img = self.filter_func(img)
        return np.array(img)


class LowLightMode(CameraMode):
    """High-gain, noise-reduced capture for dark environments."""

    def __init__(self) -> None:
        super().__init__("Low Light")

    # Override: different sensor controls
    def capture(self, fb_map, config: dict, flash_drive: Any = None) -> None:
        photo_dir = config.get("photo_dir", ".")
        os.makedirs(photo_dir, exist_ok=True)

        print(f"\n[SHUTTER] Capturing in {self.name} mode…")
        self._draw_capture_overlay(fb_map, config, "HOLD STILL")

        # Physical Flash
        if config.get("flash") and flash_drive:
            import threading
            threading.Thread(target=flash_drive.trigger, args=(1.0,), daemon=True).start()

        flash = np.full((SCREEN_RES[1], SCREEN_RES[0], 3), 255, dtype=np.uint8)
        display_to_map(flash, fb_map, config=config)

        self._draw_capture_overlay(fb_map, config, "STABILIZING SENSOR…", progress=0.2)
        raw = self._do_capture_raw({
            "Contrast": 1.1, "Sharpness": 3.0,
            "NoiseReductionMode": 2,
            "AeExposureMode": 1, "AnalogueGain": 8.0,
        })
        # Low-light needs a slightly longer sensor settle
        time.sleep(0.1)

        self._draw_capture_overlay(fb_map, config, "ENHANCING LIGHT…", progress=0.5)
        processed = self.apply_filter(raw)

        self._draw_capture_overlay(fb_map, config, "SAVING RAW…", progress=0.8)
        filename = os.path.join(
            photo_dir,
            f"{self.name.lower().replace(' ', '_')}_{int(time.time())}.jpg",
        )
        processed.save(filename, quality=95)

        self._draw_capture_overlay(fb_map, config, "DONE!", progress=1.0)
        time.sleep(0.3)

        review = processed.resize(SCREEN_RES, Image.LANCZOS)
        display_to_map(np.array(review), fb_map, config=config)
        time.sleep(1.5)

        picam2.stop()
        start_preview()

    def apply_filter(self, pil_img: Image.Image) -> Image.Image:
        return low_light.apply_low_light_filter(self._crop_and_zoom(pil_img))

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        img = self._crop_and_zoom(Image.fromarray(frame))
        img = low_light.apply_low_light_filter(img.resize(SCREEN_RES, Image.LANCZOS))
        return np.array(img)


# ==============================================================================
#  GalleryManager
# ==============================================================================

class GalleryManager:
    """Manages photo listing, index navigation, and file deletion."""

    _IMAGE_EXTS = (".jpg", ".jpeg", ".png")

    def __init__(self, photo_dir: str) -> None:
        self.photo_dir = photo_dir
        self._idx: int = 0

    # ── Public interface ──────────────────────────────────────────────────────

    @property
    def index(self) -> int:
        return self._idx

    def files(self) -> list[str]:
        """Return a sorted list of image filenames in *photo_dir*."""
        if not os.path.isdir(self.photo_dir):
            return []
        return sorted(
            f for f in os.listdir(self.photo_dir)
            if f.lower().endswith(self._IMAGE_EXTS)
        )

    def current_path(self) -> str | None:
        """Return the absolute path to the currently selected photo."""
        all_files = self.files()
        if not all_files:
            return None
        self._idx = self._idx % len(all_files)
        return os.path.join(self.photo_dir, all_files[self._idx])

    def next(self) -> None:
        self._idx += 1

    def prev(self) -> None:
        self._idx -= 1

    def delete_current(self) -> None:
        """Delete the currently selected photo and adjust the index."""
        path = self.current_path()
        if path is None:
            return
        try:
            print(f"[GALLERY] Deleting {path}…")
            os.remove(path)
            remaining = self.files()
            self._idx = self._idx % len(remaining) if remaining else 0
        except OSError as e:
            print(f"[GALLERY] Delete failed: {e}")

    def load_frame(self) -> np.ndarray:
        """Return an RGB numpy array sized to SCREEN_RES for the current photo."""
        path = self.current_path()
        if path is None:
            # Return a friendly "Empty Gallery" frame instead of just black
            from UI.themes import chalk as theme
            img = Image.new("RGB", SCREEN_RES, theme.BG_CHARCOAL)
            draw = ImageDraw.Draw(img)
            msg = "EMPTY GALLERY"
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            except:
                font = None
            tw = draw.textlength(msg, font=font) if hasattr(draw, "textlength") else len(msg) * 12
            draw.text(((SCREEN_RES[0] - tw) // 2, SCREEN_RES[1] // 2 - 10), msg, fill=(100, 100, 120), font=font)
            return np.array(img)
            
        try:
            pil = Image.open(path).convert("RGB").resize(SCREEN_RES, Image.LANCZOS)
            return np.array(pil)
        except Exception as e:
            print(f"[GALLERY] Load error ({path}): {e}")
            return np.zeros((SCREEN_RES[1], SCREEN_RES[0], 3), dtype=np.uint8)


# ==============================================================================
#  ServerManager
# ==============================================================================

class ServerManager:
    """Manages the Flask connectivity subprocess."""

    def __init__(self, base_dir: str) -> None:
        self._base_dir = base_dir
        self._proc: subprocess.Popen | None = None

    @property
    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def start(self) -> None:
        """Spawn the Flask server in a daemon thread (non-blocking)."""
        if self.is_running:
            print("[SERVER] Already running.")
            return
        threading.Thread(target=self._spawn, daemon=True).start()

    def stop(self) -> None:
        """Terminate the Flask server process."""
        if self._proc:
            print("[SERVER] Stopping Flask server…")
            self._proc.terminate()
            self._proc = None

    def _spawn(self) -> None:
        print("[SERVER] Starting Flask server…")
        try:
            cmd = [sys.executable, os.path.join(self._base_dir, "connectivity/server.py")]
            self._proc = subprocess.Popen(cmd, cwd=self._base_dir)
        except Exception as e:
            print(f"[SERVER] Failed to start: {e}")


# ==============================================================================
#  InputHandler
# ==============================================================================

class InputHandler:
    """
    Decodes raw touch / key commands and mutates the config dict accordingly.
    Keeps all navigation / selection logic out of the main loop.
    """

    _MAIN_MENU_ITEMS = ["Modes", "Connect", "Flash", "Grid"]
    _GRID_OPTIONS    = ["OFF", "3x3", "Euclid"]

    def __init__(
        self,
        modes: list[CameraMode],
        gallery: GalleryManager,
        server: ServerManager,
        flash_drive: Any = None,
    ) -> None:
        self._modes   = modes
        self._gallery = gallery
        self._server  = server
        self._flash_drive = flash_drive

    def handle(self, key: str | None, config: dict, fb_map) -> None:
        """Dispatch *key* to the appropriate handler method."""
        if key is None:
            return

        # Resolve TOUCH_SELECT into SELECT + pre-set the menu index
        if key == "TOUCH_SELECT":
            if not config.get("show_submenu"):
                config["menu_index"] = config.get("touch_menu_idx", 0) % 4
            else:
                config["submenu_index"] = config.get("touch_menu_idx", 0)
            key = "SELECT"

        dispatch = {
            "ENTER":  self._on_capture,
            "SPACE":  self._on_menu_toggle,
            "UP":     self._on_up,
            "DOWN":   self._on_down,
            "LEFT":   self._on_left,
            "RIGHT":  self._on_right,
            "BACK":   self._on_back,
            "q":      self._on_back,
            "SELECT": self._on_select,
            "GALLERY": self._on_gallery_toggle,
        }
        handler = dispatch.get(key)
        if handler:
            handler(config, fb_map)

    # ── Per-command handlers ──────────────────────────────────────────────────

    def _on_gallery_toggle(self, config: dict, _fb_map) -> None:
        config["show_gallery"] = True
        config["show_menu"] = False
        config["show_submenu"] = False


    def _on_capture(self, config: dict, fb_map) -> None:
        self._modes[config["mode_idx"]].capture(fb_map, config, flash_drive=self._flash_drive)

    def _on_menu_toggle(self, config: dict, _fb_map) -> None:
        config["show_menu"]    = not config.get("show_menu", False)
        config["show_submenu"] = False

    def _on_up(self, config: dict, _fb_map) -> None:
        if config.get("show_menu"):
            if not config.get("show_submenu"):
                config["menu_index"] = (config["menu_index"] - 1) % 4
            else:
                n = self._submenu_length(config)
                config["submenu_index"] = (config["submenu_index"] - 1) % n

    def _on_down(self, config: dict, _fb_map) -> None:
        if config.get("show_menu"):
            if not config.get("show_submenu"):
                config["menu_index"] = (config["menu_index"] + 1) % 4
            else:
                n = self._submenu_length(config)
                config["submenu_index"] = (config["submenu_index"] + 1) % n
        elif config.get("show_gallery"):
            self._gallery.delete_current()

    def _on_left(self, config: dict, _fb_map) -> None:
        if config.get("show_gallery"):
            self._gallery.prev()

    def _on_right(self, config: dict, _fb_map) -> None:
        if config.get("show_gallery"):
            self._gallery.next()

    def _on_back(self, config: dict, _fb_map) -> None:
        if config.get("show_connection_view"):
            config["show_connection_view"] = False
        elif config.get("show_menu"):
            config["show_menu"]    = False
            config["show_submenu"] = False
        elif config.get("show_gallery"):
            config["show_gallery"] = False

    def _on_select(self, config: dict, _fb_map) -> None:
        if not config.get("show_menu"):
            return

        if not config.get("show_submenu"):
            self._enter_main_menu_item(config)
        else:
            self._confirm_submenu_item(config)

    # ── Main-menu navigation ──────────────────────────────────────────────────

    def _enter_main_menu_item(self, config: dict) -> None:
        selected = self._MAIN_MENU_ITEMS[config["menu_index"]]

        if selected == "Modes":
            config["show_submenu"]    = True
            config["current_submenu"] = "Modes"
            config["submenu_index"]   = config.get("mode_idx", 0)

        elif selected == "Grid":
            config["show_submenu"]    = True
            config["current_submenu"] = "Grid"
            try:
                config["submenu_index"] = self._GRID_OPTIONS.index(config["grid_mode"])
            except ValueError:
                config["submenu_index"] = 0

        elif selected == "Connect":
            if not self._server.is_running:
                print("[SYSTEM] Starting server…")
                self._server.start()
                config["is_connected"]   = True
                config["show_connection_view"] = True
                config["show_menu"]      = False
                config["show_submenu"]   = False
            else:
                config["show_submenu"]    = True
                config["current_submenu"] = "Connect"
                config["submenu_index"]   = 0

        elif selected == "Flash":
            config["flash"] = not config.get("flash", False)

    # ── Sub-menu confirmation ─────────────────────────────────────────────────

    def _confirm_submenu_item(self, config: dict) -> None:
        submenu = config.get("current_submenu")

        if submenu == "Modes":
            config["mode_idx"] = config["submenu_index"]
            print(f"[SYSTEM] Mode → {self._modes[config['mode_idx']].name}")

        elif submenu == "Grid":
            config["grid_mode"] = self._GRID_OPTIONS[config["submenu_index"]]
            print(f"[SYSTEM] Grid → {config['grid_mode']}")

        elif submenu == "Connect":
            idx = config["submenu_index"]
            if idx == 0:          # Show QR
                config["show_connection_view"] = True
            elif idx == 1:        # Stop connection
                self._server.stop()
                config["is_connected"]         = False
                config["show_connection_view"] = False
            # idx == 2 → Back (fall through, closes submenu below)

        config["show_submenu"] = False
        config["show_menu"]    = False

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _submenu_length(self, config: dict) -> int:
        if config.get("current_submenu") == "Modes":
            return len(self._modes)
        return 3  # Grid / Connect each have 3 options


# ==============================================================================
#  CameraEngine
# ==============================================================================

class CameraEngine:
    """
    Top-level orchestrator.  Owns the framebuffer, the main loop, and
    all sub-systems.  Call ``run()`` to start the camera.
    """

    def __init__(self, config: dict) -> None:
        self.config = config

        # Build mode registry
        self.modes: list[CameraMode] = [
            StandardMode(),
            FilterMode("Glam",     glam),
            LowLightMode(),
            FilterMode("Summer",   italian_summer),
            FilterMode("Indoor",   indoor),
            FilterMode("35mm",     film35mm),
            FilterMode("UnI",      uni),
            FilterMode("Nostalgia",nostalgia),
            FilterMode("Disco",    disco),
        ]

        # Sub-systems
        base_dir      = os.path.dirname(os.path.abspath(__file__))
        photo_dir     = config.get("photo_dir", "../../Captured")
        
        # Share mode names with UI
        self.config["mode_names"] = [m.name for m in self.modes]

        self.flash_drive = flash.FlashDrive()
        self.gallery  = GalleryManager(photo_dir)
        self.server   = ServerManager(base_dir)
        self.input    = InputHandler(self.modes, self.gallery, self.server, flash_drive=self.flash_drive)
        self.grid_mgr = grid_settings.CompositionGrid()
        self.panel    = ui_top.TopPanel(config, SCREEN_RES)
        self.touch    = touch_interface.TouchInterface(
            os.path.join(base_dir, "UI/touch_settings.json"), SCREEN_RES
        )

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self) -> None:
        """Open the framebuffer and enter the main event loop."""
        start_preview()
        try:
            with open(FB_DEVICE, "r+b") as f:
                map_size = SCREEN_RES[0] * SCREEN_RES[1] * 2
                with mmap.mmap(f.fileno(), map_size) as fb_map:
                    while True:
                        loop_start = time.time()
                        self._tick(fb_map)
                        elapsed = time.time() - loop_start
                        time.sleep(max(0.0, 1.0 / FPS_CAP - elapsed))
        except KeyboardInterrupt:
            print("\n[SYSTEM] Shutting down…")
        finally:
            self.server.stop()
            picam2.stop()

    # ── Per-frame tick ────────────────────────────────────────────────────────

    def _tick(self, fb_map) -> None:
        self._render(fb_map)
        self._process_input(fb_map)

    def _render(self, fb_map) -> None:
        """Produce one display frame and push it to the framebuffer."""
        if self.config.get("show_gallery"):
            frame = self.gallery.load_frame()
        else:
            raw   = picam2.capture_array()
            if raw is None:
                return
            mode  = self.modes[self.config["mode_idx"]]
            frame = mode.process_frame(raw)

            # Compositional grid overlay
            pil   = Image.fromarray(frame)
            pil   = self.grid_mgr.apply(pil, self.config["grid_mode"])
            frame = np.array(pil)

        frame = self.panel.render(frame)
        display_to_map(frame, fb_map, config=self.config)

    def _process_input(self, fb_map) -> None:
        """Read touch input and forward to InputHandler."""
        touch_cmd = self.touch.get_touch_command(self.config)
        self.input.handle(touch_cmd, self.config, fb_map)


# ==============================================================================
#  Configuration defaults
# ==============================================================================

def _build_default_config(argv: list[str]) -> dict:
    """Return the initial config dict, applying any CLI arguments."""
    config: dict[str, Any] = {
        "menu_index":           0,
        "submenu_index":        0,
        "show_menu":            False,
        "show_submenu":         False,
        "wifi_state":           None,
        "wifi_message":         "",
        "grid_mode":            grid_settings.CompositionGrid.OFF,
        "mode_idx":             0,
        "show_gallery":         False,
        "gallery_idx":          0,
        "photo_dir":            "../../Captured",
        "is_connected":         False,
        "server_proc":          None,
        "flash":                False,
        "show_connection_view": False,
    }

    # WiFi credentials from CLI args
    if len(argv) > 1:
        config["wifi_ssid"] = argv[1]
    if len(argv) > 2:
        config["wifi_pass"] = argv[2]
    if "wifi_ssid" in config:
        print(f"[SYSTEM] WiFi SSID set via CLI: {config['wifi_ssid']}")

    return config


# ==============================================================================
#  Public entry point (used by camera.py)
# ==============================================================================

def run(config: dict | None = None) -> None:
    """Initialise and run the camera engine.  Called by camera.py."""
    defaults = _build_default_config(sys.argv)
    if config:
        defaults.update(config)
    engine = CameraEngine(defaults)
    engine.run()


if __name__ == "__main__":
    run()