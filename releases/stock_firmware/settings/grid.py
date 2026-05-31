import numpy as np
from PIL import Image, ImageDraw

class CompositionGrid:
    """
    Handles drawing compositional grids (3x3, Golden Ratio/Euclid) on PIL images.
    """
    OFF = "OFF"
    GRID_3x3 = "3x3"
    EUCLID = "Euclid"

    def __init__(self, color=(60, 60, 60), width=1):
        self.color = color
        self.width = width

    def apply(self, pil_img, mode):
        """
        Applies the selected grid mode to the PIL image.
        """
        if mode == self.OFF or not mode:
            return pil_img
        
        draw = ImageDraw.Draw(pil_img)
        w, h = pil_img.size

        if mode == self.GRID_3x3:
            # Rule of Thirds
            # Vertical
            draw.line([(w // 3, 0), (w // 3, h)], fill=self.color, width=self.width)
            draw.line([(2 * w // 3, 0), (2 * w // 3, h)], fill=self.color, width=self.width)
            # Horizontal
            draw.line([(0, h // 3), (w, h // 3)], fill=self.color, width=self.width)
            draw.line([(0, 2 * h // 3), (w, 2 * h // 3)], fill=self.color, width=self.width)
        
        elif mode == self.EUCLID:
            # Phi Grid (Golden Ratio: 1 : 0.618 : 1)
            # Ratios: 0.382 and 0.618
            v1, v2 = int(w * 0.382), int(w * 0.618)
            h1, h2 = int(h * 0.382), int(h * 0.618)
            
            # Vertical
            draw.line([(v1, 0), (v1, h)], fill=self.color, width=self.width)
            draw.line([(v2, 0), (v2, h)], fill=self.color, width=self.width)
            # Horizontal
            draw.line([(0, h1), (w, h1)], fill=self.color, width=self.width)
            draw.line([(0, h2), (w, h2)], fill=self.color, width=self.width)
            
        return pil_img

if __name__ == "__main__":
    # Simple standalone verification (Mocks FB/Camera if needed, but here just testing PIL)
    print("CompositionGrid Class test...")
    test_img = Image.new('RGB', (480, 320), color=(255, 255, 255))
    grid = CompositionGrid()
    
    # Test Euclid
    res = grid.apply(test_img.copy(), CompositionGrid.EUCLID)
    res.save("test_euclid.png")
    print("Saved test_euclid.png")
    
    # Test 3x3
    res = grid.apply(test_img.copy(), CompositionGrid.GRID_3x3)
    res.save("test_3x3.png")
    print("Saved test_3x3.png")
