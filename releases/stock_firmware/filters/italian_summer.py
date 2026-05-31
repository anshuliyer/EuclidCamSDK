import time
import sys
import select
import numpy as np
import mmap
from picamera2 import Picamera2
from PIL import Image, ImageDraw, ImageEnhance

# Config
FB_DEVICE = "/dev/fb1" 
SCREEN_RES = (480, 320)
FPS_CAP = 3 

def apply_italian_summer_filter(pil_img):
    """Adds a warm, golden tint and boosts saturation for a summer look."""
    # 1. Boost Saturation slightly
    converter = ImageEnhance.Color(pil_img)
    pil_img = converter.enhance(1.2)
    
    # 2. Apply Warm Tint (Golden/Yellow-Red)
    # R, G, B channels
    r, g, b = pil_img.split()
    
    # Red is boosted for warmth, Blue is slightly reduced for the golden effect
    r = r.point(lambda i: i * 1.1) 
    g = g.point(lambda i: i * 1.05)
    b = b.point(lambda i: i * 0.9)
    
    return Image.merge('RGB', (r, g, b))

def display_to_map(data_array, fb_map):
    r = data_array[:, :, 0].astype(np.uint16)
    g = data_array[:, :, 1].astype(np.uint16)
    b = data_array[:, :, 2].astype(np.uint16)
    rgb565 = ((b >> 3) << 11) | ((g >> 2) << 5) | (r >> 3)
    fb_map.seek(0)
    fb_map.write(rgb565.tobytes())

# Main Loop
if __name__ == "__main__":
    picam2 = Picamera2()

    def start_preview():
        config = picam2.create_video_configuration(main={"size": SCREEN_RES, "format": "RGB888"})
        picam2.configure(config)
        picam2.start()

    def take_photo(fb_map):
        print("\n[SHUTTER] Firing with Italian Summer Filter...")
        picam2.stop()
        config = picam2.create_still_configuration()
        picam2.configure(config)
        picam2.start()
        
        time.sleep(1)
        filename = f"italian_summer_{int(time.time())}.jpg"
        picam2.capture_file("temp.jpg") # Capture raw first
        
        # --- Processing: Crop + Filter ---
        img = Image.open("temp.jpg").convert("RGB")
        w, h = img.size
        target_ratio = 1.5
        
        # Center Crop to 3:2
        if w / h > target_ratio:
            new_width = h * target_ratio
            left, right = (w - new_width) / 2, (w + new_width) / 2
            img = img.crop((left, 0, right, h))
        else:
            new_height = w / target_ratio
            top, bottom = (h - new_height) / 2, (h + new_height) / 2
            img = img.crop((0, top, w, bottom))
        
        # Apply the Italian Summer Filter
        img = apply_italian_summer_filter(img)
        
        # Save final filtered image
        img.save(filename, quality=95)
        
        # --- Display Result ---
        review_img = img.resize(SCREEN_RES)
        display_to_map(np.array(review_img), fb_map)
        
        time.sleep(3.0) 
        picam2.stop()
        start_preview()

    def apply_ui(data_array):
        """Draws grid and preview filter tint."""
        img = Image.fromarray(data_array)
        
        # Apply filter to preview so you see the look before shooting
        img = apply_italian_summer_filter(img)
        
        draw = ImageDraw.Draw(img)
        w, h = SCREEN_RES
        color = (0, 0, 0)
        draw.line([(w//3, 0), (w//3, h)], fill=color, width=1)
        draw.line([(2*w//3, 0), (2*w//3, h)], fill=color, width=1)
        draw.line([(0, h//3), (w, h//3)], fill=color, width=1)
        draw.line([(0, 2*h//3), (w, 2*h//3)], fill=color, width=1)
        
        return np.array(img)

    start_preview()
    try:
        with open(FB_DEVICE, "r+b") as f:
            map_size = SCREEN_RES[0] * SCREEN_RES[1] * 2
            with mmap.mmap(f.fileno(), map_size) as fb_map:
                while True:
                    loop_start = time.time()
                    frame = picam2.capture_array()
                    if frame is not None:
                        # Show filtered preview with grid
                        ui_frame = apply_ui(frame)
                        display_to_map(ui_frame, fb_map)
                    
                    if select.select([sys.stdin], [], [], 0)[0]:
                        sys.stdin.readline()
                        take_photo(fb_map)
                    
                    time.sleep(max(0, (1.0 / FPS_CAP) - (time.time() - loop_start)))
    except KeyboardInterrupt:
        picam2.stop()
