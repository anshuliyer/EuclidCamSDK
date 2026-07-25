"""
Cinematic Bokeh Filter Module for EuclidCam.
Simulates an f/1.2 prime lens shallow depth-of-field aesthetic:
1. Radial Depth-of-Field Blur Masking (keeps central subject razor-sharp while softly blurring background edges)
2. Specular Highlights / Aperture Bokeh Discs
3. Anamorphic Teal-and-Orange Cinematic Tone Curve
"""

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

def apply_bokeh_filter(pil_img: Image.Image, is_preview: bool = False) -> Image.Image:
    """
    Applies cinematic shallow depth-of-field bokeh filter to a PIL Image.
    Optimized for high-speed hardware execution using multi-scale processing.
    """
    w, h = pil_img.size

    # 1. Color Grading: Cinematic Teal & Orange / Anamorphic Tone Curve (C-level PIL LUT)
    r, g, b = pil_img.split()
    r = r.point(lambda i: min(255, int(i * 1.08 + 8))) # Warm highlights
    g = g.point(lambda i: min(255, int(i * 0.96 + 4)))
    b = b.point(lambda i: min(255, int(i * 0.90 + 15))) # Teal shadow lift
    img_graded = Image.merge('RGB', (r, g, b))
    img_graded = ImageEnhance.Contrast(img_graded).enhance(1.12)

    if is_preview:
        # Fast preview path: light downscaled blur for 30+ FPS preview
        pw, ph = 320, 240
        small = img_graded.resize((pw, ph), Image.NEAREST)
        blurred_small = small.filter(ImageFilter.BoxBlur(2))
        blurred = blurred_small.resize((w, h), Image.NEAREST)
        
        # Radial mask
        x = np.linspace(-1.0, 1.0, w, dtype=np.float32)
        y = np.linspace(-1.0, 1.0, h, dtype=np.float32)
        xx, yy = np.meshgrid(x, y)
        dist = np.sqrt(xx**2 + yy**2)
        mask_np = np.clip((dist - 0.35) * 1.8 * 255.0, 0, 255).astype(np.uint8)
        mask = Image.fromarray(mask_np, mode='L')
        return Image.composite(blurred, img_graded, mask)

    # 2. Still Capture High-Res Path (Multi-scale Fast Pyramidal Bokeh Blur)
    # Downscale image to 1/4 resolution for ultra-fast convolution (50x speedup)
    dw, dh = max(1, w // 4), max(1, h // 4)
    small_graded = img_graded.resize((dw, dh), Image.BILINEAR)

    # Gaussian blur on 1/4 size image
    blurred_bg_small = small_graded.filter(ImageFilter.GaussianBlur(radius=3.5))

    # Specular highlight extraction for round aperture bokeh discs on 1/4 size
    luminance_small = small_graded.convert('L')
    specular_mask_small = luminance_small.point(lambda i: 255 if i > 215 else 0)
    specular_bokeh_small = specular_mask_small.filter(ImageFilter.MaxFilter(size=5))
    specular_bokeh_small = specular_bokeh_small.filter(ImageFilter.GaussianBlur(radius=1.5))

    # Blend specular bokeh layer on 1/4 size
    bokeh_layer_small = Image.composite(small_graded, blurred_bg_small, specular_bokeh_small)

    # Upscale blurred bokeh layer back to full image size
    bokeh_layer = bokeh_layer_small.resize((w, h), Image.BILINEAR)

    # Compute radial depth-of-field mask at downscaled resolution and upscale
    mx = np.linspace(-1.0, 1.0, dw, dtype=np.float32)
    my = np.linspace(-1.0, 1.0, dh, dtype=np.float32)
    mxx, myy = np.meshgrid(mx, my)
    mdist = np.sqrt(mxx**2 + myy**2)
    mask_np_small = np.clip((mdist - 0.30) * 1.6 * 255.0, 0, 255).astype(np.uint8)
    dof_mask = Image.fromarray(mask_np_small, mode='L').resize((w, h), Image.BILINEAR)

    # Composite sharp subject center with blurred optical bokeh background
    final_img = Image.composite(bokeh_layer, img_graded, dof_mask)
    return ImageEnhance.Sharpness(final_img).enhance(1.08)
