from PIL import Image, ImageEnhance

def apply_nostalgia_filter(pil_img):
    """
    Recreates a vintage, overexposed film look with warm highlights 
    and a soft, nostalgic garden vibe.
    """
    # 1. Boost Brightness for that 'sunny overexposed' look
    enhancer = ImageEnhance.Brightness(pil_img)
    pil_img = enhancer.enhance(1.25)
    
    # 2. Adjust Contrast (keep it soft but punchy)
    enhancer = ImageEnhance.Contrast(pil_img)
    pil_img = enhancer.enhance(1.1)
    
    # 3. Reduce Saturation for a vintage feel
    enhancer = ImageEnhance.Color(pil_img)
    pil_img = enhancer.enhance(0.85)
    
    # 4. Apply Color Shift (Warm/Greenish Tint)
    r, g, b = pil_img.split()
    
    # Boost Green and Red slightly for warmth, drop Blue for yellowing
    r = r.point(lambda i: i * 1.05)
    g = g.point(lambda i: i * 1.1)
    b = b.point(lambda i: i * 0.85)
    
    pil_img = Image.merge('RGB', (r, g, b))
    
    # 5. Subtle Softening (reducing digital harshness)
    enhancer = ImageEnhance.Sharpness(pil_img)
    pil_img = enhancer.enhance(0.8)
    
    return pil_img
