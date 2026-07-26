from PIL import Image, ImageEnhance

LUT_R = bytes([min(255, int(i * 1.05)) for i in range(256)])
LUT_G = bytes([min(255, int(i * 1.1)) for i in range(256)])
LUT_B = bytes([min(255, int(i * 0.85)) for i in range(256)])

def apply_nostalgia_filter(pil_img: Image.Image, is_preview: bool = False) -> Image.Image:
    """Recreates a vintage overexposed film look with warm nostalgic tones."""
    img = ImageEnhance.Brightness(pil_img).enhance(1.20)
    img = ImageEnhance.Contrast(img).enhance(1.1)
    img = ImageEnhance.Color(img).enhance(0.85)
    r, g, b = img.split()
    r = r.point(LUT_R)
    g = g.point(LUT_G)
    b = b.point(LUT_B)
    img = Image.merge('RGB', (r, g, b))
    if not is_preview:
        img = ImageEnhance.Sharpness(img).enhance(0.8)
    return img
