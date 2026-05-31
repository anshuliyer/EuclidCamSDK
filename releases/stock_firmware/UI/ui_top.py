import numpy as np
from PIL import Image, ImageDraw
from UI.themes import chalk as theme

class TopPanel:
    """
    Handles drawing and rendering of the top-panel UI indicators.
    """
    MAUVE = theme.MAUVE_PRIMARY

    def __init__(self, config, screen_res):
        self.config = config or {}
        self.screen_res = screen_res
        self.padding = self.config.get("ui_padding", 20)
        self.rotation = self.config.get("ui_rotation", 0)

    def _calculate_base_pos(self):
        w, h = self.screen_res
        if self.rotation == 0 or self.rotation == 180:
            return w - self.padding, self.padding
        elif self.rotation == 90:
            return w - self.padding, h - self.padding
        else: # 270
            return self.padding, self.padding

    def _draw_flash(self, draw, x_base, y_row):
        if self.config.get("flash"):
            x, y = x_base - 15, y_row - 14
            points = [
                (x, y), (x - 8, y + 8),
                (x - 4, y + 8), (x - 12, y + 20),
                (x - 4, y + 12), (x - 8, y + 12),
                (x, y)
            ]
            draw.polygon(points, fill=self.MAUVE)

    def _draw_battery(self, draw, x_base, y_row):
        x_batt = x_base - 75
        y_batt = y_row - 10
        draw.rectangle([x_batt, y_batt, x_batt + 20, y_batt + 10], outline=self.MAUVE, width=2)
        draw.rectangle([x_batt + 20, y_batt + 3, x_batt + 22, y_batt + 7], fill=self.MAUVE)

    def _draw_wifi(self, draw, x_base, y_row):
        x_wifi = x_base - 115
        y_wifi = y_row - 10
        for i in range(1, 4):
            r = i * 4
            bbox = [x_wifi + 10 - r, y_wifi + 10 - r, x_wifi + 10 + r, y_wifi + 10 + r]
            draw.arc(bbox, 225, 315, fill=self.MAUVE, width=2)

    def _draw_gear(self, draw):
        """
        Draws a small gear icon in the bottom-right corner.
        """
        w, h = self.screen_res
        x, y = w - self.padding - 10, h - self.padding - 10
        draw.ellipse([x-8, y-8, x+8, y+8], outline=self.MAUVE, width=2)
        for i in range(8):
            import math
            angle = i * (360/8)
            x1 = x + 8 * math.cos(math.radians(angle))
            y1 = y + 8 * math.sin(math.radians(angle))
            x2 = x + 12 * math.cos(math.radians(angle))
            y2 = y + 12 * math.sin(math.radians(angle))
            draw.line([x1, y1, x2, y2], fill=self.MAUVE, width=2)

    def _draw_gallery_icon(self, draw):
        """
        Draws a small gallery (picture) icon in the bottom-left corner.
        """
        w, h = self.screen_res
        x, y = self.padding, h - self.padding - 10
        # Draw a small "photo" frame
        draw.rectangle([x, y-12, x+16, y+4], outline=self.MAUVE, width=2)
        # Draw a "mountain" inside
        draw.polygon([(x+3, y+2), (x+8, y-6), (x+13, y+2)], fill=self.MAUVE)
        
        # Highlight if gallery is active
        if self.config.get("show_gallery"):
            draw.text((x + 20, y - 8), "GALLERY", fill=self.MAUVE)

    def _draw_gallery_view(self, draw):
        """
        Draws the gallery navigation arrows and header.
        """
        w, h = self.screen_res
        
        # 1. Reuse Settings Header Style
        from PIL import ImageFont
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            font_title = font_small = None
            
        title = "GALLERY"
        header_h = 65
        title_w = draw.textlength(title, font=font_title) if hasattr(draw, "textlength") else len(title) * 12
        draw.text(((w - title_w) // 2, 20), title, fill=(255, 255, 255), font=font_title)
        
        # Separator Line (Same as Menu)
        draw.line([(25, header_h), (w - 25, header_h)], fill=(60, 60, 75), width=1)
        draw.line([(w//2 - 30, header_h), (w//2 + 30, header_h)], fill=self.MAUVE, width=2)
        
        # Standard Cross Button (Top Right)
        bx, by = w - 60, 12
        draw.rectangle([bx, by, bx + 40, by + 40], outline=self.MAUVE, width=2)
        draw.line([bx + 10, by + 10, bx + 30, by + 30], fill=self.MAUVE, width=2)
        draw.line([bx + 30, by + 10, bx + 10, by + 30], fill=self.MAUVE, width=2)

        # 2. Navigation Arrows
        arrow_size = 25
        arrow_color = list(self.MAUVE) + [180]
        
        # Left Arrow
        lx, ly = 25, h // 2 + 20
        draw.polygon([(lx, ly), (lx + arrow_size, ly - arrow_size), (lx + arrow_size, ly + arrow_size)], fill=tuple(arrow_color))
        
        # Right Arrow
        rx, ry = w - 25, h // 2 + 20
        draw.polygon([(rx, ry), (rx - arrow_size, ry - arrow_size), (rx - arrow_size, ry + arrow_size)], fill=tuple(arrow_color))
        
        # 3. Navigation Arrows
        arrow_size = 25
        arrow_color = list(self.MAUVE) + [180]
        
        # Left Arrow
        lx, ly = 25, h // 2 + 20
        draw.polygon([(lx, ly), (lx + arrow_size, ly - arrow_size), (lx + arrow_size, ly + arrow_size)], fill=tuple(arrow_color))
        
        # Right Arrow
        rx, ry = w - 25, h // 2 + 20
        draw.polygon([(rx, ry), (rx - arrow_size, ry - arrow_size), (rx - arrow_size, ry + arrow_size)], fill=tuple(arrow_color))




    def _draw_menu(self, draw):
        """
        Draws a professional, aesthetic grid menu with card-based layout.
        """
        w, h = self.screen_res
        show_submenu = self.config.get("show_submenu", False)
        current_submenu = self.config.get("current_submenu", "Modes")
        
        if not show_submenu:
            items = ["Modes", "Connect", "Flash", "Grid"]
            selected_idx = self.config.get("menu_index", 0)
            title = "SYSTEM SETTINGS"
        elif current_submenu == "Modes":
            items = self.config.get("mode_names", ["Standard", "Glam", "Low Light", "Summer", "Indoor", "35mm", "UnI", "Nostalgia"])
            selected_idx = self.config.get("submenu_index", 0)
            title = "SELECT VISION"
        elif current_submenu == "Grid":
            items = ["OFF", "3x3", "Euclid"]
            selected_idx = self.config.get("submenu_index", 0)
            title = "COMPOSITION"
        elif current_submenu == "Connect":
            items = ["Show QR", "Stop Conn", "Back"]
            selected_idx = self.config.get("submenu_index", 0)
            title = "NETWORK"
        else:
            items = []
            selected_idx = 0
            title = "MENU"

        # 1. Solid Charcoal Background (Matching Capture Screen)
        overlay_margin = 0 # Full screen menu
        
        # Create a solid charcoal overlay image
        bg_color = list(theme.BG_CHARCOAL) + [255] # Ensure solid alpha
        overlay = Image.new('RGBA', self.screen_res, tuple(bg_color))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # --- PASTE LOGO WATERMARK ---
        try:
            import os
            # Use absolute path resolution from this file up to the project root
            # UI -> python -> firmware -> root -> splashscreen
            proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
            logo_path = os.path.join(proj_root, "splashscreen", "transparent_logo.png")
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((250, 250), Image.LANCZOS)
            r, g, b, a = logo.split()
            a = a.point(lambda i: i * theme.LOGO_OPACITY)
            logo = Image.merge('RGBA', (r, g, b, a))
            lw, lh = logo.size
            cx, cy = w // 2, h // 2
            # Paste onto the translucent overlay
            overlay.paste(logo, (cx - lw // 2, cy - lh // 2), logo)
        except Exception as e:
            print(f"Theme watermark error: {e}")

        # Mauve Accent Border
        overlay_draw.rectangle([overlay_margin, overlay_margin, w - overlay_margin, h - overlay_margin], outline=self.MAUVE, width=2)
        # Delay alpha composite until all UI elements are drawn on overlay_draw
        # Load Fonts

        from PIL import ImageFont
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
            font_item = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font_title = font_item = font_small = None

        # 2. Header Area
        header_h = 65
        title_w = overlay_draw.textlength(title, font=font_title) if hasattr(overlay_draw, "textlength") else len(title) * 12
        overlay_draw.text(((w - title_w) // 2, 20), title, fill=(255, 255, 255), font=font_title)
        
        # Massive Cross Button (Top Right)
        bx, by = w - 60, 12
        overlay_draw.rectangle([bx, by, bx + 40, by + 40], outline=self.MAUVE, width=2)
        # Draw a bold X
        overlay_draw.line([bx + 10, by + 10, bx + 30, by + 30], fill=self.MAUVE, width=2)
        overlay_draw.line([bx + 30, by + 10, bx + 10, by + 30], fill=self.MAUVE, width=2)
        
        # Separator Line
        overlay_draw.line([(25, header_h), (w - 25, header_h)], fill=(60, 60, 75), width=1)
        overlay_draw.line([(w//2 - 30, header_h), (w//2 + 30, header_h)], fill=self.MAUVE, width=2)

        # 3. Grid Calculation
        num_items = len(items)
        cols = 4
        rows = (num_items + cols - 1) // cols
        
        grid_margin_x = 25
        grid_margin_y = 15
        gap = 12
        
        available_w = w - (grid_margin_x * 2)
        available_h = h - header_h - (grid_margin_y * 2)
        
        btn_w = (available_w - (gap * (cols - 1))) // cols
        btn_h = (available_h - (gap * (rows - 1))) // rows
        
        for i, item in enumerate(items):
            row = i // cols
            col = i % cols
            
            bx = grid_margin_x + col * (btn_w + gap)
            by = header_h + grid_margin_y + row * (btn_h + gap)
            
            is_selected = (i == selected_idx)
            
            # Button Card Logic - TRANSLUCENT GLASS EFFECT
            card_fill = tuple(list(self.MAUVE) + [220]) if is_selected else (30, 30, 40, 150)
            card_outline = (255, 255, 255) if is_selected else (70, 70, 90)
            text_color = (0, 0, 0) if is_selected else (220, 220, 230)
            accent_color = (255, 255, 255, 180) if is_selected else self.MAUVE

            # Draw Card (rounded_rectangle fallback)
            draw_func = getattr(overlay_draw, "rounded_rectangle", overlay_draw.rectangle)
            draw_func([bx, by, bx + btn_w, by + btn_h], radius=10, fill=card_fill, outline=card_outline, width=2 if is_selected else 1)

            # 4. Professional Iconography
            icon_y = by + 22
            cx = bx + btn_w // 2
            
            if item == "Modes":
                overlay_draw.ellipse([cx-12, icon_y-12, cx+12, icon_y+12], outline=text_color, width=2)
                overlay_draw.ellipse([cx-4, icon_y-4, cx+4, icon_y+4], fill=text_color)
            elif item == "Flash":
                overlay_draw.polygon([(cx, icon_y-12), (cx-6, icon_y), (cx+4, icon_y), (cx-2, icon_y+12)], fill=text_color)
            elif item == "Connect":
                for r in [6, 12, 18]:
                    overlay_draw.arc([cx-r, icon_y-r, cx+r, icon_y+r], start=210, end=330, fill=text_color, width=2)
            elif item == "Grid":
                for off in [-6, 6]:
                    overlay_draw.line([cx+off, icon_y-10, cx+off, icon_y+10], fill=text_color, width=1)
                    overlay_draw.line([cx-10, icon_y+off, cx+10, icon_y+off], fill=text_color, width=1)

            # Content Text
            display_name = item
            if item == "Connect":
                status = "ON" if self.config.get("is_connected") else "OFF"
                overlay_draw.text((bx + btn_w - 30, by + 8), status, fill=accent_color, font=font_small)
            
            tw = overlay_draw.textlength(display_name, font=font_item) if hasattr(overlay_draw, "textlength") else len(display_name) * 9
            overlay_draw.text((bx + (btn_w - tw) // 2, by + btn_h - 22), display_name, fill=text_color, font=font_item)

        # Finally, blend the fully populated RGBA overlay onto the main RGB image
        main_img = draw._image.convert("RGBA")
        main_img = Image.alpha_composite(main_img, overlay)
        draw._image.paste(main_img)

    def _draw_bin_icon(self, draw):
        """
        Draws a transparent DELETE card in the top-left corner.
        """
        bx, by = 15, 12
        btn_w, btn_h = 100, 40
        
        # Transparent Card (Outline only)
        draw_func = getattr(draw, "rounded_rectangle", draw.rectangle)
        draw_func([bx, by, bx + btn_w, by + btn_h], radius=10, fill=(0, 0, 0, 0), outline=self.MAUVE, width=1)
        
        # Neutral Icon (White/Grey)
        ix, iy = bx + 12, by + 10
        icon_color = (220, 220, 230)
        draw.rectangle([ix, iy + 4, ix + 10, iy + 16], outline=icon_color, width=1)
        draw.line([(ix - 2, iy + 4), (ix + 12, iy + 4)], fill=icon_color, width=2)
        
        from PIL import ImageFont
        try:
            font_btn = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        except:
            font_btn = None
            
        draw.text((bx + 35, by + 10), "DELETE", fill=icon_color, font=font_btn)




    def _draw_connection_overlay(self, draw):
        """
        Draws a large QR code and connection details in the center of the screen.
        """
        w, h = self.screen_res
        overlay_w, overlay_h = 300, 240
        x, y = (w - overlay_w) // 2, (h - overlay_h) // 2
        
        # Transparent-ish background box
        draw.rectangle([x, y, x + overlay_w, y + overlay_h], fill=(0, 0, 0), outline=self.MAUVE, width=3)
        
        # Close Button (Top Right of overlay) - Massive and easily tappable
        bx, by = x + overlay_w - 70, y + 10
        draw.rectangle([bx, by, bx + 60, by + 60], outline=self.MAUVE, width=2)
        # Draw a bold X
        draw.line([bx + 15, by + 15, bx + 45, by + 45], fill=self.MAUVE, width=3)
        draw.line([bx + 45, by + 15, bx + 15, by + 45], fill=self.MAUVE, width=3)

        # Title
        draw.text((x + 20, y + 25), "CONNECTIVITY ACTIVE", fill=self.MAUVE)
        
        # Load the QR code image if it exists
        import os
        qr_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../connectivity/static/qr_code.png"))
        if os.path.exists(qr_path):
            try:
                qr_img = Image.open(qr_path).convert("RGB")
                qr_img = qr_img.resize((140, 140), Image.LANCZOS)
                # Paste it onto the draw surface's image
                draw._image.paste(qr_img, (x + (overlay_w - 140)//2, y + 50))
            except Exception as e:
                print(f"[ERROR] Loading QR for UI: {e}")
                draw.text((x + 20, y + 100), "QR ERROR", fill=(255, 0, 0))
        else:
             draw.text((x + 20, y + 100), "GENERATING QR...", fill=self.MAUVE)

        # Instructions
        draw.text((x + 20, y + overlay_h - 40), "Scan to browse images", fill=self.MAUVE)
        draw.text((x + 20, y + overlay_h - 20), "Tap [X] or edges to close", fill=self.MAUVE)

    def render(self, frame):
        """
        Applies the UI overlay to the provided frame.
        """
        img = Image.fromarray(frame)
        draw = ImageDraw.Draw(img)
        
        show_gallery = self.config.get("show_gallery", False)
        
        if show_gallery:
            self._draw_bin_icon(draw)
            self._draw_gallery_view(draw)

        elif self.config.get("show_connection_view", False):
            draw._image = img 
            self._draw_connection_overlay(draw)
        else:
            if self.config.get("show_menu"):
                self._draw_menu(draw)
            else:
                x_base, y_base = self._calculate_base_pos()
                y_row = y_base + 5
                
                self._draw_flash(draw, x_base, y_row)
                self._draw_battery(draw, x_base, y_row)
                self._draw_wifi(draw, x_base, y_row)
                
                self._draw_gear(draw)
                self._draw_gallery_icon(draw)

        return np.array(img)
