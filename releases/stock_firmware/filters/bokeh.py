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
    """
    w, h = pil_img.size

    # 1. Color Grading: Cinematic Teal & Orange / Anamorphic Tone Curve
    r, g, b = pil_img.split()
    r = r.point(lambda i: min(255, int(i * 1.08 + 8))) # Warm highlights
    g = g.point(lambda i: min(255, int(i * 0.96 + 4)))
    b = b.point(lambda i: min(255, int(i * 0.90 + 15))) # Teal shadow lift
    img_graded = Image.merge('RGB', (r, g, b))
    img_graded = ImageEnhance.Contrast(img_graded).enhance(1.12)

    if is_preview:
        # Fast preview path: light gaussian blur composite for 30+ FPS preview
        blurred = img_graded.filter(ImageFilter.GaussianBlur(radius=3.0))
        
        # Radial vignette mask (center 0 = sharp, outer 255 = blurred)
        x = np.linspace(-1.0, 1.0, w, dtype=np.float32)
        y = np.linspace(-1.0, 1.0, h, dtype=np.float32)
        xx, yy = np.meshgrid(x, y)
        dist = np.sqrt(xx**2 + yy**2)
        mask_np = np.clip((dist - 0.35) * 1.8 * 255.0, 0, 255).astype(np.uint8)
        mask = Image.fromarray(mask_np, mode='L')
        
        return Image.composite(blurred, img_graded, mask)

    # 2. Still Capture High-Res Path: Multi-pass Bokeh Blur + Specular Bokeh Discs
    blurred_bg = img_graded.filter(ImageFilter.GaussianBlur(radius=7.0))
    
    # Specular highlight extraction for round aperture bokeh discs
    luminance = img_graded.convert('L')
    specular_mask = luminance.point(lambda i: 255 if i > 215 else 0)
    specular_bokeh = specular_mask.filter(ImageFilter.MaxFilter(size=11))
    specular_bokeh = specular_bokeh.filter(ImageFilter.GaussianBlur(radius=2.0))
    
    # Blend specular bokeh highlights into blurred background
    bokeh_layer = Image.composite(img_graded, blurred_bg, specular_bokeh)
    
    # Precise radial depth-of-field mask centered on subject
    x = np.linspace(-1.0, 1.0, w, dtype=np.float32)
    y = np.linspace(-1.0, 1.0, h, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    dist = np.sqrt(xx**2 + yy**2)
    # Smooth step transition: sharp inside radius 0.30, gradual blur towards edges
    mask_np = np.clip((dist - 0.30) * 1.6 * 255.0, 0, 255).astype(np.uint8)
    dof_mask = Image.fromarray(mask_np, mode='L')

    final_img = Image.composite(bokeh_layer, img_graded, dof_mask)
    return ImageEnhance.Sharpness(final_img).enhance(1.08)
