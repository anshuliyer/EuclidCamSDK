#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import platform
import lzma
import shutil
import hashlib
import binascii

OS_TYPE = platform.system()

def is_admin():
    try:
        if OS_TYPE == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.geteuid() == 0
    except:
        return False

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
    except:
        return ""

def list_disks():
    print("Available Disks:")
    if OS_TYPE == "Windows":
        print(run_cmd("wmic diskdrive get caption,deviceid,size"))
    elif OS_TYPE == "Darwin":
        print(run_cmd("diskutil list | grep -E '(/dev/disk|NAME)'"))
    elif OS_TYPE == "Linux":
        print(run_cmd("lsblk -d -o NAME,SIZE,MODEL"))
        
def unmount_disk(disk):
    if OS_TYPE == "Darwin":
        os.system(f"diskutil unmountDisk {disk} > /dev/null 2>&1")
    elif OS_TYPE == "Linux":
        os.system(f"umount {disk}* > /dev/null 2>&1")

def wait_for_bootfs(disk):
    if OS_TYPE == "Darwin":
        for _ in range(10):
            if os.path.exists("/Volumes/bootfs"): return "/Volumes/bootfs"
            if os.path.exists("/Volumes/boot"): return "/Volumes/boot"
            time.sleep(1)
        os.system(f"diskutil mount {disk}s1 > /dev/null 2>&1")
        time.sleep(2)
        if os.path.exists("/Volumes/bootfs"): return "/Volumes/bootfs"
        if os.path.exists("/Volumes/boot"): return "/Volumes/boot"
        
        print("\n[!] macOS needs to refresh the partition table.")
        input("    Please REMOVE the SD card reader, RE-INSERT it, and press ENTER...")
        for _ in range(15):
            if os.path.exists("/Volumes/bootfs"): return "/Volumes/bootfs"
            if os.path.exists("/Volumes/boot"): return "/Volumes/boot"
            time.sleep(1)
        os.system(f"diskutil mount {disk}s1 > /dev/null 2>&1")
        time.sleep(2)
        if os.path.exists("/Volumes/bootfs"): return "/Volumes/bootfs"
        if os.path.exists("/Volumes/boot"): return "/Volumes/boot"
    elif OS_TYPE == "Linux":
        mnt_dir = "/tmp/euclid_boot"
        os.makedirs(mnt_dir, exist_ok=True)
        part = f"{disk}1" if "mmcblk" not in disk else f"{disk}p1"
        os.system(f"mount {part} {mnt_dir} > /dev/null 2>&1")
        if os.path.exists(os.path.join(mnt_dir, "cmdline.txt")): return mnt_dir
    elif OS_TYPE == "Windows":
        import string
        from ctypes import windll
        for _ in range(20):
            drives = [chr(i) for i in range(65, 91) if windll.kernel32.GetLogicalDrives() & (1 << (i - 65))]
            for d in drives:
                if os.path.exists(f"{d}:\\cmdline.txt"):
                    return f"{d}:\\"
            time.sleep(1)
    return None

def unmount_bootfs(disk, boot_vol):
    if OS_TYPE == "Darwin":
        os.system(f"diskutil unmountDisk {disk} > /dev/null 2>&1")
    elif OS_TYPE == "Linux":
        os.system(f"umount {boot_vol} > /dev/null 2>&1")

def main():
    if not is_admin():
        print("Error: This script must be run as root/Administrator to write directly to disks.")
        print("On Mac/Linux: sudo ./flash.py")
        print("On Windows: Run Command Prompt as Administrator, then run flash.exe")
        sys.exit(1)

    print("========================================")
    print("       EuclidCamSDK Flasher             ")
    print("========================================")
    
    list_disks()
    print("="*40)
    
    print("Target disk examples:")
    print("  Mac: /dev/disk4")
    print("  Linux: /dev/sdb or /dev/mmcblk0")
    print("  Windows: \\\\.\\PhysicalDrive1")
    disk = input("Enter the target disk: ").strip()
    if not disk: sys.exit(1)
        
    ssid = input("Enter Wi-Fi SSID (mandatory): ").strip()
    password = input("Enter Wi-Fi Password (mandatory): ").strip()
    if not ssid or not password:
        print("Error: SSID and password are mandatory.")
        sys.exit(1)
        
    print("\n" + "!"*40)
    confirm = input(f"WARNING: All data on {disk} will be DESTROYED.\nType 'YES' to proceed: ")
    if confirm != 'YES':
        print("Aborted.")
        sys.exit(0)
        
    write_disk = disk
    if OS_TYPE == "Darwin" and write_disk.startswith("/dev/disk"):
        write_disk = write_disk.replace("/dev/disk", "/dev/rdisk")
        
    # Look for image in bin relative to this executable/script
    base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
    if getattr(sys, 'frozen', False):
        # Executable runs from SDK/, so bin is ../bin/
        img_path = os.path.abspath(os.path.join(base_dir, "../bin/os.img.xz"))
    else:
        # Script runs from SDK/src/, so bin is ../../bin/
        img_path = os.path.abspath(os.path.join(base_dir, "../../bin/os.img.xz"))
    
    if not os.path.exists(img_path):
        print(f"Error: Image not found at {img_path}")
        sys.exit(1)
        
    print(f"\n[1/4] Unmounting {disk}...")
    unmount_disk(disk)
    
    print(f"[2/4] Flashing {os.path.basename(img_path)} to {write_disk}...")
    
    try:
        total_uncompressed = 2910846976
        try:
            if OS_TYPE in ["Darwin", "Linux"]:
                xz_info = run_cmd(f"xz -l --robot \"{img_path}\"")
                for line in xz_info.splitlines():
                    if line.startswith("file\t"):
                        total_uncompressed = int(line.split("\t")[4])
                        break
        except: pass

        with lzma.open(img_path, 'rb') as f_in:
            with open(write_disk, 'wb') as f_out:
                written = 0
                start = time.time()
                while True:
                    chunk = f_in.read(1024 * 1024)
                    if not chunk: break
                    f_out.write(chunk)
                    written += len(chunk)
                    elapsed = time.time() - start
                    speed = (written / 1024 / 1024) / (elapsed if elapsed > 0 else 1)
                    pct = (written / total_uncompressed) * 100
                    bar = '#' * int(pct / 2) + '-' * (50 - int(pct / 2))
                    sys.stdout.write(f'\\r[{bar}] {pct:.1f}% | {written/1024/1024:.1f} MB | {speed:.1f} MB/s')
                    sys.stdout.flush()
        print("\n")
    except Exception as e:
        print(f"\nError during flashing: {e}")
        sys.exit(1)
        
    print("[3/4] Flashing complete. Waiting for the boot partition to mount...")
    if OS_TYPE in ["Darwin", "Linux"]:
        time.sleep(2)
        
    boot_vol = wait_for_bootfs(disk)
    if not boot_vol:
        print("\nCould not automatically mount the boot partition. You will need to manually configure Wi-Fi.")
        sys.exit(1)
            
    print(f"\n[4/4] Boot partition found at {boot_vol}. Configuring Wi-Fi, Users, and Drivers...")
    
    # 1. Install custom drivers (e.g. waveshare35a.dtbo)
    drivers_dir = os.path.abspath(os.path.join(base_dir, "../bin/os_drivers" if getattr(sys, 'frozen', False) else "../../bin/os_drivers"))
    if os.path.exists(drivers_dir):
        overlays_dir = os.path.join(boot_vol, "overlays")
        os.makedirs(overlays_dir, exist_ok=True)
        for f_name in os.listdir(drivers_dir):
            if f_name.endswith(".dtbo"):
                shutil.copy2(os.path.join(drivers_dir, f_name), overlays_dir)

    # 2. Update config.txt for PiCam3 and 3.5" TFT SPI
    config_path = os.path.join(boot_vol, "config.txt")
    if os.path.exists(config_path):
        with open(config_path, "a", newline='\n') as f:
            f.write("\n# EuclidCam Custom Hardware\n")
            f.write("camera_auto_detect=1\n")
            f.write("dtoverlay=waveshare35a,rotate=270\n")

    # 3. Inject EuclidCam Firmware Payload
    firmware_src = os.path.abspath(os.path.join(base_dir, "../releases/firmware" if getattr(sys, 'frozen', False) else "../../releases/firmware"))
    if os.path.exists(firmware_src):
        print(f"Injecting Firmware Payload from {firmware_src}...")
        shutil.copytree(firmware_src, os.path.join(boot_vol, "firmware_payload"), dirs_exist_ok=True)

    psk_bytes = hashlib.pbkdf2_hmac('sha1', password.encode('utf-8'), ssid.encode('utf-8'), 4096, 32)
    wpa_psk = binascii.hexlify(psk_bytes).decode('utf-8')
    
    network_config = f"""network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      dhcp6: true
      optional: true
  wifis:
    wlan0:
      dhcp4: true
      regulatory-domain: "US"
      access-points:
        "{ssid}":
          password: "{wpa_psk}"
      optional: true
"""
    
    user_data = f"""#cloud-config
manage_resolv_conf: false

hostname: euclidcam
manage_etc_hosts: true
packages:
- avahi-daemon
apt:
  preserve_sources_list: true
  conf: |
    Acquire {{
      Check-Date "false";
    }};
users:
- name: euclidcam
  groups: users,adm,dialout,audio,netdev,video,plugdev,cdrom,games,input,gpio,spi,i2c,render,sudo
  shell: /bin/bash
  lock_passwd: false
  passwd: "$6$UmjwkqIRUxYJ6lMP$LvQFb927KgK1A6F1aVIipxtbDHsWejqsNLWtmlHoJ.ksK6UthhHxrbVffpylSXrKFVod/.Mj7Oagx1EBuUIDt1"
enable_ssh: true
ssh_pwauth: true
rpi:
  interfaces:
    serial: true

write_files:
  - path: /etc/udev/rules.d/99-calibration.rules
    content: |
      ACTION=="add|change", KERNEL=="event[0-9]*", ENV{{ID_INPUT_TOUCHSCREEN}}=="1", ENV{{LIBINPUT_CALIBRATION_MATRIX}}="0 -1 1 1 0 0"
  - path: /usr/local/bin/start.sh
    permissions: '0755'
    content: |
      #!/bin/bash
      if [ ! -f /opt/euclidcam/.setup_done ]; then
          clear
          echo "======================================"
          echo " Initializing EuclidCam for first use "
          echo "======================================"
          
          if [ -d /boot/firmware/firmware_payload ]; then
              echo "Extracting firmware payload from /boot/firmware..."
              sudo mkdir -p /opt/euclidcam
              sudo mv /boot/firmware/firmware_payload /opt/euclidcam/firmware
              sudo chown -R euclidcam:euclidcam /opt/euclidcam
          elif [ -d /boot/firmware_payload ]; then
              echo "Extracting firmware payload from /boot..."
              sudo mkdir -p /opt/euclidcam
              sudo mv /boot/firmware_payload /opt/euclidcam/firmware
              sudo chown -R euclidcam:euclidcam /opt/euclidcam
          else
              echo "Error: Firmware payload not found!"
              echo "Listing contents of /boot/firmware:"
              ls -la /boot/firmware || true
              echo "Listing contents of /boot:"
              ls -la /boot || true
              exit 1
          fi
          
          echo "Waiting for Wi-Fi connection..."
          until ping -c 1 8.8.8.8 &>/dev/null; do
              sleep 2
          done
          
          echo "Installing dependencies..."
          sudo apt-get update
          sudo apt-get install -y python3-numpy python3-pil python3-picamera2
          touch /opt/euclidcam/.setup_done
      fi
      cd /opt/euclidcam/firmware || exit 1
      export DISPLAY=:0
      python3 main.py
  - path: /etc/profile.d/99-euclidcam.sh
    content: |
      if [ -z "$DISPLAY" ] && [ $(tty) = /dev/tty1 ]; then
          /usr/local/bin/start.sh
      fi
"""
    
    with open(os.path.join(boot_vol, "network-config"), "w") as f:
        f.write(network_config)
        
    with open(os.path.join(boot_vol, "user-data"), "w") as f:
        f.write(user_data)
        
    cmdline_path = os.path.join(boot_vol, "cmdline.txt")
    if os.path.exists(cmdline_path):
        with open(cmdline_path, "r") as f:
            cmdline = f.read().strip()
            
        if "fbcon=map:10" not in cmdline:
            cmdline += " fbcon=map:10 fbcon=font:ProFont6x11 logo.nologo"
            
        import re
        cmdline = re.sub(r'systemd\.run[^\s]*', '', cmdline).strip()
        cmdline = re.sub(r'systemd\.unit[^\s]*', '', cmdline).strip()
        cmdline = re.sub(r'ds=nocloud;i=[^\s]*', '', cmdline).strip()
        
        if "ds=nocloud" not in cmdline:
            cmdline += " ds=nocloud;i=euclidcam-init"
            
        with open(cmdline_path, "w", newline='\n') as f:
            f.write(cmdline + "\n")

    else:
        print("Warning: cmdline.txt not found.")
        
    print("\nConfiguration written! Unmounting safely...")
    unmount_bootfs(disk, boot_vol)
    print(f"""
========================================
Done! You can now insert the SD card into your device.

[Default Device Credentials]
  Username: euclidcam
  Password: euclidcam

[SSH & Next Steps]
  If the device is on the same Wi-Fi network, you can access it via:
  $ ssh euclidcam@euclidcam.local
  
  To enable autologin and finish the configuration, run:
  $ sudo raspi-config
  (Go to System Options -> Boot / Auto Login -> Console Autologin)
  
  Afterward, you can manually trigger the firmware installation by running:
  $ /usr/local/bin/start.sh
========================================""")

if __name__ == "__main__":
    main()
