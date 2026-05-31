from PIL import ImageEnhance, ImageFilter

def apply_low_light_filter(pil_img):
    """
    Optimizes images taken in low light by boosting brightness and applying sharpening.
    """
    # 1. Boost Brightness
    enhancer = ImageEnhance.Brightness(pil_img)
    pil_img = enhancer.enhance(1.4)
    
    # 2. Boost Contrast slightly to prevent washing out
    enhancer = ImageEnhance.Contrast(pil_img)
    pil_img = enhancer.enhance(1.2)
    
    # 3. Apply Denoise (Blur slightly then sharpen)
    pil_img = pil_img.filter(ImageFilter.SMOOTH_MORE)
    
    # 4. Sharpen edges
    pil_img = pil_img.filter(ImageFilter.SHARPEN)
    
    return pil_img
