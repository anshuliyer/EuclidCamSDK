import flet as ft
import flet.canvas as cv
import subprocess
import platform
import os
import threading
import math
import time
import random

# Global mouse state
mouse_state = {"x": None, "y": None}

class GoldenParticle:
    def __init__(self, index, w, h):
        self.index = index
        self.c = 28
        golden_angle = math.pi * (3 - math.sqrt(5))
        self.r = self.c * math.sqrt(self.index)
        self.theta = self.index * golden_angle
        
        self.x = w / 2 + self.r * math.cos(self.theta)
        self.y = h / 2 + self.r * math.sin(self.theta)
        self.baseX = self.x
        self.baseY = self.y
        
        self.size = max(0.4, 2.5 - (self.r / 800))
        self.density = random.uniform(1, 21)
        self.shape = cv.Circle(self.x, self.y, self.size, paint=ft.Paint(color="#2A2A2A"))
        
    def update(self, w, h, rotation_offset):
        current_theta = self.theta + rotation_offset
        self.baseX = w / 2 + self.r * math.cos(current_theta)
        self.baseY = h / 2 + self.r * math.sin(current_theta)
        
        mx, my = mouse_state["x"], mouse_state["y"]
        dx = mx - self.x if mx is not None else 0
        dy = my - self.y if my is not None else 0
        distance = math.sqrt(dx*dx + dy*dy)
        maxDist = 200
        
        if mx is not None and distance < maxDist and distance > 0:
            forceDirectionX = dx / distance
            forceDirectionY = dy / distance
            force = (maxDist - distance) / maxDist
            directionX = forceDirectionX * force * self.density * 0.8
            directionY = forceDirectionY * force * self.density * 0.8
            self.x -= directionX
            self.y -= directionY
        else:
            if self.x != self.baseX:
                self.x -= (self.x - self.baseX) / 15
            if self.y != self.baseY:
                self.y -= (self.y - self.baseY) / 15
                
        self.shape.x = self.x
        self.shape.y = self.y

def create_bg_canvas(page):
    w = page.width or 850
    h = page.height or 700
    
    # Force 1200 particles at startup so it fully covers a 1080p monitor if the user maximizes the window later
    num_particles = 1200
    
    particles = [GoldenParticle(i, w, h) for i in range(1, num_particles + 1)]
    canvas = cv.Canvas([p.shape for p in particles], expand=True)
    
    def animate():
        rotation_offset = 0
        blink_timer = 0
        while True:
            time.sleep(1/30) # ~30 FPS
            if canvas.page is None: continue
            try:
                rotation_offset += 0.0006
                blink_timer += 1
                cw = page.width or 850
                ch = page.height or 700
                
                for p in particles:
                    p.update(cw, ch, rotation_offset)
                canvas.update()
                
                # Blinking cursor sync
                if "cursor" in state and getattr(state["cursor"], "page", None):
                    if blink_timer % 15 == 0:
                        state["cursor"].opacity = 0 if state["cursor"].opacity == 1 else 1
                        state["cursor"].update()
            except Exception:
                pass
            
    threading.Thread(target=animate, daemon=True).start()
    
    return ft.Container(content=canvas, width=w, height=h)

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore').strip()
    except:
        return ""

def get_disks():
    disks = []
    os_type = platform.system()
    if os_type == "Windows":
        out = run_cmd("wmic diskdrive get deviceid")
        disks = [line.strip() for line in out.splitlines() if "PhysicalDrive" in line]
    elif os_type == "Darwin":
        out = run_cmd("diskutil list | grep -E '^/dev/disk'")
        disks = [line.split()[0] for line in out.splitlines()]
    elif os_type == "Linux":
        out = run_cmd("lsblk -d -o NAME | grep -v NAME")
        disks = [f"/dev/{line.strip()}" for line in out.splitlines() if line.strip()]
    return disks if disks else ["No disks found"]

def main(page: ft.Page):
    page.title = "EuclidCam Flasher"
    page.window_width = 850
    page.window_height = 700
    page.bgcolor = "#111111"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    
    page.fonts = {
        "JetBrains Mono": "https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip"
    }
    
    # State variables
    state = {
        "disk": "",
        "ssid": "",
        "pwd": "",
        "sudo_pwd": "",
        "fw_path": ""
    }
    
    def on_hover(e):
        mouse_state["x"] = e.local_x
        mouse_state["y"] = e.local_y
    
    def on_resize(e):
        if "bg" in state:
            state["bg"].width = page.width
            state["bg"].height = page.height
            state["bg"].update()

    page.on_hover = on_hover
    page.on_resize = on_resize
    
    # --- UI Generators ---
    def toggle_fullscreen(e):
        page.window.full_screen = not page.window.full_screen
        page.update()
        
    def create_header(step_text):
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Row([
                        ft.Text("EUCLIDCAM FLASHER", size=24, weight=ft.FontWeight.W_800, color="#FFFFFF", font_family="JetBrains Mono"),
                        ft.Container(
                            content=ft.Text(step_text, size=10, weight=ft.FontWeight.BOLD, color="#111111", font_family="JetBrains Mono"),
                            bgcolor="#D9C8B0",
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            border_radius=4,
                            margin=ft.margin.only(left=10)
                        )
                    ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Text("OS image deployment and zero-touch configuration tool.", size=13, color="#888888", font_family="JetBrains Mono")
                ], spacing=4),
                ft.IconButton(
                    icon=ft.Icons.FULLSCREEN_ROUNDED,
                    icon_color="#888888",
                    icon_size=24,
                    tooltip="Toggle Fullscreen",
                    on_click=toggle_fullscreen
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START),
            padding=ft.padding.only(left=40, top=40, right=40, bottom=40),
            bgcolor="#111111"
        )
        
    # Keep background persistent to preserve animation thread
    bg_canvas_layer = create_bg_canvas(page)
    state["bg"] = bg_canvas_layer
    foreground_view = ft.Container(alignment=ft.alignment.center, expand=True)
    page.add(ft.Stack([bg_canvas_layer, foreground_view], expand=True))
    
    def switch_view(new_view):
        foreground_view.content = new_view
        foreground_view.update()

    # --- VIEW 0: Boot Screen ---
    def build_view0():
        logo_stack = ft.Stack([
            ft.Image(src="logo.gif", width=320, fit=ft.ImageFit.CONTAIN),
            ft.Container(
                content=ft.Text("EuclidCam", size=24, weight=ft.FontWeight.W_700, color="#FFFFFF", font_family="JetBrains Mono"),
                left=16, bottom=25
            )
        ], width=320, height=320)
        
        state["cursor"] = ft.Text("_", size=13, color="#D9C8B0", font_family="JetBrains Mono", weight=ft.FontWeight.W_400)
        
        boot_content = ft.Column([
            logo_stack,
            ft.Row([
                ft.Text("built to be built upon", size=13, color="#888888", font_family="JetBrains Mono", weight=ft.FontWeight.W_400),
                state["cursor"]
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=0)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        return ft.Container(content=boot_content, alignment=ft.alignment.center, expand=True)


    # --- VIEW 1: Main Imager Dashboard ---
    
    # Dialogs for Input
    disk_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(d) for d in get_disks()],
        bgcolor="#111111", border_color="#333333", color="#FFFFFF", text_size=13,
        text_style=ft.TextStyle(font_family="JetBrains Mono"), width=350
    )
    if disk_dropdown.options: disk_dropdown.value = disk_dropdown.options[0].key

    ssid_input = ft.TextField(label="NETWORK SSID", bgcolor="#111111", border_color="#333333", color="#FFFFFF", text_size=13,
                              label_style=ft.TextStyle(color="#888888", font_family="JetBrains Mono"), text_style=ft.TextStyle(font_family="JetBrains Mono"), width=350)
    
    pwd_input = ft.TextField(label="NETWORK PASSWORD", password=True, can_reveal_password=True, bgcolor="#111111", border_color="#333333", color="#FFFFFF", text_size=13,
                             label_style=ft.TextStyle(color="#888888", font_family="JetBrains Mono"), text_style=ft.TextStyle(font_family="JetBrains Mono"), width=350)
                             
    sudo_pwd_input = ft.TextField(label="MAC/LINUX ADMIN PASSWORD", password=True, can_reveal_password=True, bgcolor="#111111", border_color="#333333", color="#FFFFFF", text_size=13,
                                  label_style=ft.TextStyle(color="#888888", font_family="JetBrains Mono"), text_style=ft.TextStyle(font_family="JetBrains Mono"), width=350)

    # Dynamic Labels for the big buttons
    os_label = ft.Text("STOCK FIRMWARE", size=14, color="#FFFFFF", weight=ft.FontWeight.W_700, font_family="JetBrains Mono")
    storage_label = ft.Text("CHOOSE STORAGE", size=14, color="#FFFFFF", weight=ft.FontWeight.W_700, font_family="JetBrains Mono")
    network_label = ft.Text("CONFIGURE NETWORK", size=14, color="#FFFFFF", weight=ft.FontWeight.W_700, font_family="JetBrains Mono")
    
    fw_type_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option("Stock Firmware"), ft.dropdown.Option("Custom Firmware")],
        value="Stock Firmware", bgcolor="#111111", border_color="#333333", color="#FFFFFF", text_size=13, width=350,
        text_style=ft.TextStyle(font_family="JetBrains Mono")
    )
    fw_path_input = ft.TextField(label="CUSTOM FIRMWARE PATH (ABS)", visible=False, bgcolor="#111111", border_color="#333333", color="#FFFFFF", text_size=13,
                                 label_style=ft.TextStyle(color="#888888", font_family="JetBrains Mono"), text_style=ft.TextStyle(font_family="JetBrains Mono"), width=350)
    
    def fw_type_changed(e):
        fw_path_input.visible = (fw_type_dropdown.value == "Custom Firmware")
        page.update()
        
    fw_type_dropdown.on_change = fw_type_changed
    
    def close_fw_dlg(e):
        page.close(fw_dlg)
        if fw_type_dropdown.value == "Custom Firmware" and fw_path_input.value:
            state["fw_path"] = fw_path_input.value
            os_label.value = "CUSTOM FIRMWARE"
            os_label.color = "#D9C8B0"
        else:
            state["fw_path"] = ""
            os_label.value = "STOCK FIRMWARE"
            os_label.color = "#FFFFFF"
        page.update()

    fw_dlg = ft.AlertDialog(
        modal=True, title=ft.Text("Select Firmware", font_family="JetBrains Mono"),
        content=ft.Column([fw_type_dropdown, fw_path_input], height=130), bgcolor="#161616",
        actions=[ft.TextButton("Confirm", on_click=close_fw_dlg, style=ft.ButtonStyle(color="#D9C8B0"))]
    )
    
    def close_storage_dlg(e):
        page.close(storage_dlg)
        if disk_dropdown.value and disk_dropdown.value != "No disks found":
            state["disk"] = disk_dropdown.value
            storage_label.value = state["disk"]
            storage_label.color = "#D9C8B0"
        page.update()
        
    def close_network_dlg(e):
        page.close(network_dlg)
        if ssid_input.value and pwd_input.value:
            state["ssid"] = ssid_input.value
            state["pwd"] = pwd_input.value
            network_label.value = f"WIFI: {state['ssid']}"
            network_label.color = "#D9C8B0"
        page.update()
        
    def close_auth_dlg(e):
        page.close(auth_dlg)
        state["sudo_pwd"] = sudo_pwd_input.value
        page.update()
        if state["disk"] and state["ssid"]:
            switch_view(build_view3())
            run_flash_thread()

    storage_dlg = ft.AlertDialog(
        modal=True, title=ft.Text("Select Target Drive", font_family="JetBrains Mono"),
        content=disk_dropdown, bgcolor="#161616",
        actions=[ft.TextButton("Confirm", on_click=close_storage_dlg, style=ft.ButtonStyle(color="#D9C8B0"))]
    )
    
    network_dlg = ft.AlertDialog(
        modal=True, title=ft.Text("Wi-Fi Configuration", font_family="JetBrains Mono"),
        content=ft.Column([ssid_input, pwd_input], height=130), bgcolor="#161616",
        actions=[ft.TextButton("Save Settings", on_click=close_network_dlg, style=ft.ButtonStyle(color="#D9C8B0"))]
    )
    
    auth_dlg = ft.AlertDialog(
        modal=True, title=ft.Text("Administrator Authentication", font_family="JetBrains Mono"),
        content=ft.Column([ft.Text("Raw disk writing requires system privileges.", color="#888888", size=12, font_family="JetBrains Mono"), sudo_pwd_input], height=100), bgcolor="#161616",
        actions=[ft.TextButton("Cancel", on_click=lambda e: page.close(auth_dlg)), ft.TextButton("Deploy", on_click=close_auth_dlg, style=ft.ButtonStyle(color="#D9C8B0"))]
    )

    def open_fw(e):
        page.open(fw_dlg)

    def open_storage(e):
        page.open(storage_dlg)
        
    def open_network(e):
        page.open(network_dlg)
        
    def attempt_deploy(e):
        if not state["disk"] or not state["ssid"]:
            return # Buttons should prevent this, but just in case
        page.open(auth_dlg)

    def build_view1():
        # RPi Imager style huge button blocks
        btn_style = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            bgcolor="#161616",
            padding=30
        )
        
        os_btn = ft.ElevatedButton(
            content=ft.Column([
                ft.Icon(ft.Icons.CAMERA_ROUNDED, size=40, color="#555555"),
                os_label
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            style=btn_style, width=220, height=160, on_click=open_fw
        )
        
        storage_btn_ui = ft.ElevatedButton(
            content=ft.Column([
                ft.Icon(ft.Icons.SD_STORAGE_ROUNDED, size=40, color="#D9C8B0"),
                storage_label
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            style=btn_style, width=220, height=160, on_click=open_storage
        )
        
        network_btn_ui = ft.ElevatedButton(
            content=ft.Column([
                ft.Icon(ft.Icons.WIFI_ROUNDED, size=40, color="#D9C8B0"),
                network_label
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            style=btn_style, width=220, height=160, on_click=open_network
        )
        
        button_row = ft.Row([os_btn, storage_btn_ui, network_btn_ui], alignment=ft.MainAxisAlignment.CENTER, spacing=30)
        
        next_btn = ft.ElevatedButton(
            content=ft.Row([ft.Text("NEXT", color="#111111", font_family="JetBrains Mono", weight=ft.FontWeight.W_800, size=16)], alignment=ft.MainAxisAlignment.CENTER),
            width=300, height=55, style=ft.ButtonStyle(color="#111111", bgcolor="#D9C8B0", shape=ft.RoundedRectangleBorder(radius=30)),
            on_click=attempt_deploy
        )
        
        main_layout = ft.Column([
            button_row,
            ft.Container(height=40),
            ft.Row([next_btn], alignment=ft.MainAxisAlignment.CENTER)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        return ft.Column([create_header("MAIN"), ft.Container(content=main_layout, padding=ft.padding.only(top=60))], expand=True)


    # --- VIEW 3: Progress ---
    log_output = ft.TextField(multiline=True, read_only=True, value="", expand=True, bgcolor="#0A0A0A", border_color="transparent", color="#D9C8B0", text_style=ft.TextStyle(font_family="JetBrains Mono", size=11), content_padding=15)
    progress_bar = ft.ProgressBar(width=700, color="#D9C8B0", bgcolor="#222222")

    def build_view3():
        log_output.value = f"> Initiating secure deployment to {state['disk']}...\n"
        card = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.TERMINAL_ROUNDED, color="#555555", size=16), ft.Text("SYSTEM CONSOLE", size=11, color="#888888", weight=ft.FontWeight.W_600, font_family="JetBrains Mono")], spacing=8),
                progress_bar,
                ft.Container(content=log_output, border=ft.border.all(1, "#222222"), border_radius=6, expand=True)
            ], expand=True, spacing=15),
            padding=30, bgcolor="#161616", border_radius=12, width=770, height=450
        )
        return ft.Column([create_header("DEPLOYING"), ft.Container(content=card, padding=ft.padding.only(left=40, top=20))], expand=True)

    def run_flash_thread():
        def run_flash_process():
            import sys
            base_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
            flash_bin = os.path.join(base_dir, "SDK", "flash")
            flash_script = os.path.join(base_dir, "SDK", "src", "flash.py")
            cmd = []
            if os.path.exists(flash_bin) and platform.system() == "Darwin": cmd = ["sudo", "-S", flash_bin]
            elif os.path.exists(flash_script): cmd = ["sudo", "-S", "python3", flash_script]
            else:
                log_output.value += "> Error: Deployment binary missing.\n"
                page.update()
                return
            
            fw_arg = state['fw_path'] if state['fw_path'] else "STOCK"
            cmd.extend([state['disk'], state['ssid'], state['pwd'], fw_arg, "YES"])

            try:
                process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                sudo_pwd_str = f"{state['sudo_pwd']}\n" if (platform.system() == "Darwin" or platform.system() == "Linux") else ""
                
                def write_inputs():
                    try: 
                        if sudo_pwd_str:
                            process.stdin.write(sudo_pwd_str)
                            process.stdin.flush()
                    except: pass
                
                threading.Thread(target=write_inputs, daemon=True).start()
                
                for line in iter(process.stdout.readline, ''):
                    if line:
                        if "Enter the target disk" in line or "Enter Wi-Fi SSID" in line or "Enter Wi-Fi Password" in line or "Enter custom firmware" in line or "Type 'YES' to proceed" in line: continue
                        log_output.value += f"> {line}"
                        page.update()
                        
                process.wait()
                if process.returncode == 0:
                    log_output.value += "\n> [SUCCESS] Deployment completed.\n"
                    page.update()
                    import time
                    time.sleep(1.5)
                    switch_view(build_view4())
                else:
                    log_output.value += f"\n> [ERROR] Deployment failed (code {process.returncode}).\n"
                    progress_bar.color = "#FF5555"
                    progress_bar.value = 1
                    page.update()
            except Exception as ex:
                log_output.value += f"> Exception: {str(ex)}\n"
                page.update()

        threading.Thread(target=run_flash_process, daemon=True).start()


    # --- VIEW 4: Instructions ---
    def build_view4():
        instructions = """DEPLOYMENT SUCCESSFUL

NEXT STEPS:
1. SSH into the device on the same Wi-Fi network:
   $ ssh euclidcam@euclidcam.local
   (Password: euclidcam)

2. Enable autologin and finish configuration:
   $ sudo raspi-config
   (Go to System Options -> Boot / Auto Login -> Console Autologin)

3. Trigger the firmware installation:
   $ /usr/local/bin/start.sh"""

        def launch_terminal(e):
            if platform.system() == "Darwin":
                cmd = f'osascript -e \'tell app "Terminal" to do script "ssh euclidcam@euclidcam.local"\' -e \'tell app "Terminal" to activate\''
                subprocess.Popen(cmd, shell=True)
            elif platform.system() == "Windows":
                subprocess.Popen(['start', 'cmd', '/k', 'ssh euclidcam@euclidcam.local'], shell=True)
            elif platform.system() == "Linux":
                subprocess.Popen(['x-terminal-emulator', '-e', 'ssh euclidcam@euclidcam.local'], shell=True)

        card = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color="#D9C8B0", size=24), ft.Text("HARDWARE READY", size=16, color="#D9C8B0", weight=ft.FontWeight.W_800, font_family="JetBrains Mono")], spacing=10),
                ft.Divider(height=20, color="#222222"),
                ft.Text(instructions, size=13, color="#D9C8B0", font_family="JetBrains Mono"),
                ft.Container(height=20),
                ft.ElevatedButton(
                    content=ft.Row([ft.Icon(ft.Icons.TERMINAL_ROUNDED, color="#111111", size=18), ft.Text("LAUNCH SSH SESSION", color="#111111", font_family="JetBrains Mono", weight=ft.FontWeight.W_700)], alignment=ft.MainAxisAlignment.CENTER),
                    width=400, height=45, style=ft.ButtonStyle(color="#111111", bgcolor="#D9C8B0", shape=ft.RoundedRectangleBorder(radius=4)),
                    on_click=launch_terminal
                ),
                ft.TextButton(
                    content=ft.Row([ft.Icon(ft.Icons.DONE_ALL_ROUNDED, color="#888888", size=18), ft.Text("MARK AS DONE", color="#888888", font_family="JetBrains Mono", weight=ft.FontWeight.W_700)], alignment=ft.MainAxisAlignment.CENTER),
                    width=400, height=45, style=ft.ButtonStyle(color="#111111", shape=ft.RoundedRectangleBorder(radius=4)),
                    on_click=lambda e: switch_view(build_view1())
                )
            ], spacing=12),
            padding=40, bgcolor="#161616", border_radius=12, width=480
        )
        return ft.Column([create_header("STEP 4/4"), ft.Container(content=card, padding=ft.padding.only(left=40, top=20))])

    # Start app on Boot Screen
    switch_view(build_view0())
    
    # Transition to View 1 after 3.6 seconds (matches webapp animation delay)
    def boot_transition():
        import time
        time.sleep(3.6)
        switch_view(build_view1())
        
    threading.Thread(target=boot_transition, daemon=True).start()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
