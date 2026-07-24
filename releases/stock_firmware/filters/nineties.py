"""
90s Filter Module for EuclidCam.
Simulates a classic 1990s flash magazine & film stock aesthetic based on:
- Exposure: -1.6 (slightly darker, cinematic midtones)
- Contrast: +1.2 (punchy tone curve)
- Shadows: +8.4 & Fade: +3.2 (lifted matte black point & soft charcoal shadows)
- Saturation: -1.0 (muted, vintage film color palette)
- Clarity: +2.5 (enhanced edge definition)
"""

from PIL import Image, ImageEnhance, ImageFilter

def apply_nineties_filter(pil_img: Image.Image) -> Image.Image:
    """Applies 1990s vintage film filter to a PIL Image."""
    img = pil_img.copy()

    # 1. Exposure (-1.6): Dim brightness slightly for cinematic mood
    img = ImageEnhance.Brightness(img).enhance(0.86)

    # 2. Contrast (+1.2): Increase tonal contrast
    img = ImageEnhance.Contrast(img).enhance(1.20)

    # 3. Saturation (-1.0): Mute colors slightly for classic 90s print look
    img = ImageEnhance.Color(img).enhance(0.85)

    # 4. Clarity (+2.5): Boost sharpness / edge clarity
    img = ImageEnhance.Sharpness(img).enhance(1.45)

    # 5. Shadows (+8.4) & Fade (+3.2): Lift black point for soft matte charcoal shadows
    r, g, b = img.split()
    r = r.point(lambda i: min(255, int(i * 0.92 + 18)))
    g = g.point(lambda i: min(255, int(i * 0.90 + 16)))
    b = b.point(lambda i: min(255, int(i * 0.94 + 20)))
    img = Image.merge('RGB', (r, g, b))

    # 6. Apply light unsharp mask for subtle analog clarity
    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=110, threshold=3))

    return img
