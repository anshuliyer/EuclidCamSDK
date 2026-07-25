import numpy as np
from PIL import Image, ImageDraw
from UI.themes import chalk as theme

class TopPanel:
    """
    Handles drawing and rendering of the top-panel UI indicators.
    """
    BEIGE = theme.BEIGE_PRIMARY

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
        flash_mode = str(self.config.get("flash_mode", "AUTO")).upper()
        if flash_mode != "OFF":
            x, y = x_base - 15, y_row - 14
            points = [
                (x, y), (x - 8, y + 8),
                (x - 4, y + 8), (x - 12, y + 20),
                (x - 4, y + 12), (x - 8, y + 12),
                (x, y)
            ]
            fill_color = self.BEIGE if flash_mode == "ON" else (255, 215, 0) # Gold for AUTO
            draw.polygon(points, fill=fill_color)
            if flash_mode == "AUTO":
                try:
                    from PIL import ImageFont
                    font_a = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 9)
                except Exception:
                    font_a = None
                draw.text((x - 18, y + 8), "A", fill=(255, 215, 0), font=font_a)

    def _draw_battery(self, draw, x_base, y_row):
        x_batt = x_base - 75
        y_batt = y_row - 10
        
        is_low = self.config.get("is_undervoltage", False)
        color = (255, 50, 50) if is_low else self.BEIGE
        
        if not is_low:
            # Solid beige fill when healthy
            draw.rectangle([x_batt, y_batt, x_batt + 20, y_batt + 10], fill=color)
        else:
            # Empty red outline when low
            draw.rectangle([x_batt, y_batt, x_batt + 20, y_batt + 10], outline=color, width=2)
            
        # Draw battery tip
        draw.rectangle([x_batt + 20, y_batt + 3, x_batt + 22, y_batt + 7], fill=color)
        
        if is_low:
            # Draw a warning slash through the battery to indicate power issues
            draw.line([x_batt + 2, y_batt + 8, x_batt + 18, y_batt + 2], fill=color, width=2)

    def _draw_wifi(self, draw, x_base, y_row):
        x_pos = x_base - 115
        y_pos = y_row - 10

        # Rule 1: The moment Hotspot is ON / in Connect mode -> Display "EC" badge
        if self.config.get("show_connection_view") or self.config.get("is_connected"):
            try:
                from PIL import ImageFont
                font_ec = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 11)
            except Exception:
                font_ec = None
            draw_func = getattr(draw, "rounded_rectangle", draw.rectangle)
            draw_func([x_pos - 4, y_pos - 1, x_pos + 22, y_pos + 15], radius=4, fill=(45, 40, 35), outline=self.BEIGE, width=1)
            draw.text((x_pos + 1, y_pos), "EC", fill=self.BEIGE, font=font_ec)

        # Rule 2: Otherwise, display Wi-Fi bars if connected to a Wi-Fi network
        elif self.config.get("is_wifi_active"):
            x_wifi = x_pos
            y_wifi = y_pos
            for i in range(1, 4):
                r = i * 4
                bbox = [x_wifi + 10 - r, y_wifi + 10 - r, x_wifi + 10 + r, y_wifi + 10 + r]
                draw.arc(bbox, 225, 315, fill=self.BEIGE, width=2)

        # Otherwise: Display nothing (no wifi / out of range)

    def _draw_gear(self, draw):
        """
        Draws a large gear icon in the bottom-right corner for easy tapping.
        """
        w, h = self.screen_res
        x, y = w - self.padding - 20, h - self.padding - 20
        draw.ellipse([x-14, y-14, x+14, y+14], outline=self.BEIGE, width=3)
        for i in range(8):
            import math
            angle = i * (360/8)
            x1 = x + 14 * math.cos(math.radians(angle))
            y1 = y + 14 * math.sin(math.radians(angle))
            x2 = x + 22 * math.cos(math.radians(angle))
            y2 = y + 22 * math.sin(math.radians(angle))
            draw.line([x1, y1, x2, y2], fill=self.BEIGE, width=4)
        draw.ellipse([x-6, y-6, x+6, y+6], fill=self.BEIGE)

    def _draw_gallery_icon(self, draw):
        """
        Draws a large gallery (picture) icon in the bottom-left corner.
        """
        w, h = self.screen_res
        x, y = self.padding + 5, h - self.padding - 35
        # Draw a large "photo" frame
        draw.rectangle([x, y, x+40, y+30], outline=self.BEIGE, width=3)
        # Draw a "mountain" inside
        draw.polygon([(x+5, y+25), (x+15, y+10), (x+25, y+25)], fill=self.BEIGE)
        draw.polygon([(x+20, y+25), (x+28, y+15), (x+35, y+25)], fill=self.BEIGE)
        # Sun
        draw.ellipse([x+8, y+5, x+14, y+11], fill=self.BEIGE)
        
        # Highlight if gallery is active
        if self.config.get("show_gallery"):
            draw.text((x + 50, y + 5), "GALLERY", fill=self.BEIGE)

    def _draw_gallery_view(self, draw):
        """
        Draws the gallery UI. For single-button mode, we want this to be completely immersive.
        """
        pass




    def _draw_menu(self, draw):
        """
        Draws a gorgeous horizontal scrolling carousel for single-button navigation.
        """
        w, h = self.screen_res
        show_submenu = self.config.get("show_submenu", False)
        current_submenu = self.config.get("current_submenu", "Modes")
        
        if not show_submenu:
            flash_pwr = f"Flash: {self.config.get('flash_mode', 'AUTO')}"
            exp_val = f"Exp: {self.config.get('exposure_label', 'Auto')}"
            items = ["Gallery", "Modes", exp_val, "Connect", flash_pwr, "Grid", "Exit"]
            selected_idx = self.config.get("menu_index", 0)
            title = "SYSTEM MENU"
        elif current_submenu == "Modes":
            items = self.config.get("mode_names", []) + ["Back"]
            selected_idx = self.config.get("submenu_index", 0)
            title = "SELECT VISION"
        elif current_submenu == "Exposure":
            items = ["Auto", "1/100s", "1/50s", "1/30s", "1/15s", "1/10s", "Back"]
            selected_idx = self.config.get("submenu_index", 0)
            title = "EXPOSURE TIME"
        elif current_submenu == "Grid":
            items = ["OFF", "3x3", "Euclid", "Back"]
            selected_idx = self.config.get("submenu_index", 0)
            title = "COMPOSITION"
        elif current_submenu == "Grid":
            items = ["OFF", "3x3", "Euclid", "Back"]
            selected_idx = self.config.get("submenu_index", 0)
            title = "COMPOSITION"
        elif current_submenu == "Connect":
            wifi_pwr = "Hotspot: ON" if self.config.get("is_connected") else "Hotspot: OFF"
            items = ["Show QR", wifi_pwr, "Back"]
            selected_idx = self.config.get("submenu_index", 0)
            title = "NETWORK"
        else:
            items = []
            selected_idx = 0
            title = "MENU"

        # Create a solid charcoal overlay image
        bg_color = list(theme.BG_CHARCOAL) + [255]
        overlay = Image.new('RGBA', self.screen_res, tuple(bg_color))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # --- PASTE LOGO WATERMARK ---
        try:
            import os
            proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
            logo_path = os.path.join(proj_root, "assets", "transparent_logo_light.png")
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((250, 250), Image.LANCZOS)
            r, g, b, a = logo.split()
            a = a.point(lambda i: i * theme.LOGO_OPACITY)
            logo = Image.merge('RGBA', (r, g, b, a))
            lw, lh = logo.size
            cx, cy = w // 2, h // 2
            overlay.paste(logo, (cx - lw // 2, cy - lh // 2), logo)
        except Exception as e:
            print(f"Theme watermark error: {e}")

        # Mauve Accent Border
        overlay_draw.rectangle([0, 0, w, h], outline=self.BEIGE, width=2)

        # Load Fonts
        from PIL import ImageFont
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            font_item = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            font_title = font_item = font_small = None

        # Header Area
        title_w = overlay_draw.textlength(title, font=font_title) if hasattr(overlay_draw, "textlength") else len(title) * 11
        overlay_draw.text(((w - title_w) // 2, 20), title, fill=(255, 255, 255), font=font_title)
        
        # Separator Line
        header_h = 55
        overlay_draw.line([(25, header_h), (w - 25, header_h)], fill=(90, 80, 70), width=1)
        overlay_draw.line([(w//2 - 30, header_h), (w//2 + 30, header_h)], fill=self.BEIGE, width=2)

        # Draw Carousel
        n = len(items)
        if n == 0:
            return

        prev_idx = (selected_idx - 1) % n
        next_idx = (selected_idx + 1) % n

        # Dimensions
        center_w, center_h = 140, 100
        cx, cy = w // 2, h // 2 + 25
        
        side_w, side_h = 100, 70
        lx, ly = cx - center_w//2 - 15 - side_w//2, cy
        rx, ry = cx + center_w//2 + 15 + side_w//2, cy

        def draw_card(idx, x, y, width, height, is_selected):
            bx = x - width // 2
            by = y - height // 2
            item = items[idx]
            
            card_fill = tuple(list(self.BEIGE) + [220]) if is_selected else (45, 40, 35, 180)
            card_outline = (255, 255, 255) if is_selected else (140, 125, 110)
            text_color = (15, 10, 5) if is_selected else (245, 240, 230)
            accent_color = (255, 255, 255, 180) if is_selected else self.BEIGE
            
            draw_func = getattr(overlay_draw, "rounded_rectangle", overlay_draw.rectangle)
            draw_func([bx, by, bx + width, by + height], radius=10, fill=card_fill, outline=card_outline, width=3 if is_selected else 1)
            
            # Content Text
            display_name = item
            if item == "Connect":
                status = "ON" if self.config.get("is_connected") else "OFF"
                if is_selected:
                    overlay_draw.text((bx + width - 35, by + 8), status, fill=accent_color, font=font_small)
            elif item.startswith("Flash"):
                status = "ON" if self.config.get("flash", True) else "OFF"
                if is_selected:
                    overlay_draw.text((bx + width - 35, by + 8), status, fill=accent_color, font=font_small)
            
            font = font_item if is_selected else font_small
            tw = overlay_draw.textlength(display_name, font=font) if hasattr(overlay_draw, "textlength") else len(display_name) * (9 if is_selected else 7)
            
            # Center the text vertically and horizontally
            overlay_draw.text((bx + (width - tw) // 2, by + height // 2 - 10), display_name, fill=text_color, font=font)

        # Draw left and right cards first (behind)
        if n > 2:
            draw_card(prev_idx, lx, ly, side_w, side_h, False)
        if n > 1:
            draw_card(next_idx, rx, ry, side_w, side_h, False)
        
        # Draw center card (in front)
        draw_card(selected_idx, cx, cy, center_w, center_h, True)
        
        # Instructional text at bottom
        inst_text = "Hold Shutter: Next  |  Click: Select"
        iw = overlay_draw.textlength(inst_text, font=font_small) if hasattr(overlay_draw, "textlength") else len(inst_text) * 7
        overlay_draw.text(((w - iw) // 2, h - 25), inst_text, fill=(150, 150, 150), font=font_small)

        # Blend
        main_img = draw._image.convert("RGBA")
        main_img = Image.alpha_composite(main_img, overlay)
        draw._image.paste(main_img)

    def _draw_bin_icon(self, draw):
        """
        Draws a transparent DELETE icon in the top-left corner.
        """
        bx, by = 12, 12
        btn_w, btn_h = 40, 40
        
        # Transparent Card (Outline only)
        draw_func = getattr(draw, "rounded_rectangle", draw.rectangle)
        draw_func([bx, by, bx + btn_w, by + btn_h], radius=8, fill=(0, 0, 0, 0), outline=self.BEIGE, width=2)
        
        # Neutral Trash Icon
        ix, iy = bx + 15, by + 10
        icon_color = (220, 220, 230)
        draw.rectangle([ix, iy + 4, ix + 10, iy + 20], outline=icon_color, width=2)
        draw.line([(ix - 4, iy + 4), (ix + 14, iy + 4)], fill=icon_color, width=2)
        draw.line([(ix + 2, iy + 4), (ix + 2, iy)], fill=icon_color, width=2)
        draw.line([(ix + 8, iy + 4), (ix + 8, iy)], fill=icon_color, width=2)
        draw.line([(ix + 2, iy), (ix + 8, iy)], fill=icon_color, width=2)

    def _draw_bt_icon(self, draw):
        """
        Draws a Bluetooth send icon next to the close button in the Gallery.
        """
        w, h = self.screen_res
        bx, by = w - 100, 12
        
        draw_func = getattr(draw, "rounded_rectangle", draw.rectangle)
        draw_func([bx, by, bx + 40, by + 40], radius=8, fill=(0, 0, 0, 0), outline=self.BEIGE, width=2)
        
        ix, iy = bx + 20, by + 10
        bt_color = (100, 150, 255)
        draw.line([(ix, iy), (ix, iy + 20)], fill=bt_color, width=2)
        draw.line([(ix, iy), (ix + 8, iy + 5)], fill=bt_color, width=2)
        draw.line([(ix + 8, iy + 5), (ix - 8, iy + 15)], fill=bt_color, width=2)
        draw.line([(ix, iy + 20), (ix + 8, iy + 15)], fill=bt_color, width=2)
        draw.line([(ix + 8, iy + 15), (ix - 8, iy + 5)], fill=bt_color, width=2)




    def _draw_connection_overlay(self, draw, overlay_img):
        """
        Draws a large QR code and connection details in the center of the screen.
        """
        w, h = self.screen_res
        overlay_w, overlay_h = 300, 240
        x, y = (w - overlay_w) // 2, (h - overlay_h) // 2
        
        # Opaque dark background box
        draw.rectangle([x, y, x + overlay_w, y + overlay_h], fill=(15, 12, 10, 245), outline=self.BEIGE, width=2)
        
        # Title
        draw.text((x + 20, y + 15), "CONNECTIVITY ACTIVE", fill=self.BEIGE)
        
        # Generate the QR code dynamically to ensure correct IP
        ip = "10.42.0.1" # default fallback hotspot IP
        try:
            import socket, fcntl, struct, qrcode
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                ip = socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', b'wlan0'))[20:24])
            except Exception:
                pass
                
            qr = qrcode.QRCode(version=1, border=2, box_size=10)
            qr.add_data(f"http://{ip}:5000")
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to RAM disk (/tmp) to avoid library kwargs mismatch
            tmp_path = "/tmp/euclidcam_qr.png"
            qr_img.save(tmp_path)
            
            from PIL import Image
            qr_pil = Image.open(tmp_path).convert("RGBA")
            qr_pil = qr_pil.resize((125, 125), Image.NEAREST)
            # Paste QR image directly onto overlay layer so it appears over the dark background card
            overlay_img.paste(qr_pil, (x + (overlay_w - 125) // 2, y + 42))
        except Exception as e:
            print(f"[ERROR] Live QR generation failed: {e}")
            draw.text((x + 10, y + 100), f"ERR: {str(e)[:30]}", fill=(255, 0, 0))

        # Instructions
        draw.text((x + 20, y + overlay_h - 45), f"SSID: EuclidCam | IP: {ip}:5000", fill=self.BEIGE)
        draw.text((x + 20, y + overlay_h - 24), "Scan QR to open web app (Shutter to exit)", fill=self.BEIGE)

    def _draw_toast(self, draw, text: str):
        """Draws a sleek notification toast banner at top center of screen with light glass styling."""
        w, h = self.screen_res
        try:
            from PIL import ImageFont
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        except Exception:
            font = None
            
        tw = draw.textlength(text, font=font) if hasattr(draw, "textlength") else len(text) * 8
        card_w, card_h = int(tw + 36), 32
        cx, cy = w // 2, 28
        bx, by = cx - card_w // 2, cy - card_h // 2
        
        draw_func = getattr(draw, "rounded_rectangle", draw.rectangle)
        # Very light glass background (30% opacity) with subtle white glass outline
        draw_func([bx, by, bx + card_w, by + card_h], radius=8, fill=(0, 0, 0, 45), outline=(255, 255, 255, 140), width=1)
        
        draw.text((bx + 18, by + 7), text, fill=(255, 255, 255, 255), font=font)

    def _draw_pro_hud(self, draw):
        """Draws a pro-camera HUD badge at top-left of viewfinder with light glass styling."""
        try:
            from PIL import ImageFont
            font_hud = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
        except Exception:
            font_hud = None

        mode_name = str(self.config.get("active_mode_name", "STANDARD")).upper()
        exp = str(self.config.get("exposure_label", "AUTO")).upper()
        
        hud_text = f"● {mode_name} | {exp}"
        tw = draw.textlength(hud_text, font=font_hud) if hasattr(draw, "textlength") else len(hud_text) * 6
        badge_w, badge_h = int(tw + 16), 18
        bx, by = 12, 10
        
        draw_func = getattr(draw, "rounded_rectangle", draw.rectangle)
        # Very light glass background (30% opacity) with subtle white glass outline
        draw_func([bx, by, bx + badge_w, by + badge_h], radius=5, fill=(0, 0, 0, 40), outline=(255, 255, 255, 130), width=1)
        draw.text((bx + 8, by + 3), hud_text, fill=(255, 255, 255, 255), font=font_hud)

    def render(self, frame):
        """
        Applies the UI overlay to the provided frame with RGBA alpha compositing for glass effects.
        """
        img = Image.fromarray(frame).convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        show_gallery = self.config.get("show_gallery", False)
        
        if show_gallery:
            self._draw_gallery_view(draw)

        elif self.config.get("show_connection_view", False):
            self._draw_connection_overlay(draw, overlay)
        else:
            if self.config.get("show_menu"):
                self._draw_menu(draw)
            else:
                x_base, y_base = self._calculate_base_pos()
                y_row = y_base + 5
                
                self._draw_flash(draw, x_base, y_row)
                self._draw_battery(draw, x_base, y_row)
                self._draw_wifi(draw, x_base, y_row)
                self._draw_pro_hud(draw)
                
                if self.config.get("is_benchmark_mode"):
                    uptime = self.config.get("benchmark_uptime", 0)
                    mins = uptime // 60
                    secs = uptime % 60
                    draw.text((10, self.screen_res[1] - 25), f"BENCHMARK: {mins:02d}:{secs:02d}", fill=(255, 50, 50))

        # Check for active toast notification
        toast_text = self.config.get("wifi_connected_toast")
        toast_time = self.config.get("wifi_connected_time", 0)
        import time
        if toast_text and (time.time() - toast_time < 4.0):
            self._draw_toast(draw, toast_text)

        img = Image.alpha_composite(img, overlay).convert("RGB")
        return np.array(img)
