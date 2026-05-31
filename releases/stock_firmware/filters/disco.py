import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw

def apply_disco_filter(pil_img):
    """
    A 'heavy' processing filter that simulates a high-energy disco/club environment.
    Features: Chromatic aberration, horizontal glitch offsets, rainbow light leaks, and heavy bloom.
    """
    # 1. Boost Saturation and Contrast for that 'club' look
    enhancer_color = ImageEnhance.Color(pil_img)
    pil_img = enhancer_color.enhance(1.6)
    enhancer_contrast = ImageEnhance.Contrast(pil_img)
    pil_img = enhancer_contrast.enhance(1.3)

    # Convert to numpy for heavy pixel-level manipulation
    arr = np.array(pil_img).astype(np.float32)
    h, w, c = arr.shape

    # 2. Chromatic Aberration (R and B shifts)
    shift = 8
    new_arr = np.zeros_like(arr)
    # Red shift left
    new_arr[:, :w-shift, 0] = arr[:, shift:, 0]
    # Green stays
    new_arr[:, :, 1] = arr[:, :, 1]
    # Blue shift right
    new_arr[:, shift:, 2] = arr[:, :w-shift, 2]
    arr = new_arr

    # 3. Horizontal Glitch (Row Shifting)
    # Shift random rows by random amounts to simulate 'heavy processing' glitch
    num_glitches = 15
    for _ in range(num_glitches):
        y = np.random.randint(0, h)
        row_h = np.random.randint(2, 10)
        offset = np.random.randint(-20, 20)
        if y + row_h < h:
            arr[y:y+row_h] = np.roll(arr[y:y+row_h], offset, axis=1)

    # Convert back to PIL for overlays and filters
    pil_img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    # 4. Bloom (Heavy Glow)
    # Create a mask of bright areas
    bright = pil_img.point(lambda i: i if i > 180 else 0)
    glow = bright.filter(ImageFilter.GaussianBlur(radius=15))
    pil_img = Image.blend(pil_img, glow, alpha=0.4)

    # 5. Disco Spotlights (Rainbow Light Leaks)
    # We use a separate RGBA layer for the spotlights to allow alpha blending
    lights_layer = Image.new('RGBA', pil_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(lights_layer)
    
    colors = [
        (255, 0, 255, 100),   # Magenta
        (0, 255, 255, 100),   # Cyan
        (255, 255, 0, 100),   # Yellow
        (255, 50, 50, 100),   # Red
        (50, 255, 50, 100),   # Green
    ]
    
    for _ in range(6):  # Draw 6 random spotlights
        color = colors[np.random.randint(0, len(colors))]
        cx = np.random.randint(0, w)
        cy = np.random.randint(0, h)
        radius = np.random.randint(w//4, w//2)
        
        # Draw a soft-edged circle by layering multiple ellipses with decreasing opacity
        for r in range(radius, 0, -30):
            alpha = int(color[3] * (1 - r/radius))
            soft_color = (color[0], color[1], color[2], alpha)
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=soft_color)
    
    # 6. Final Compositing
    pil_img = pil_img.convert("RGBA")
    pil_img = Image.alpha_composite(pil_img, lights_layer).convert("RGB")

    return pil_img
