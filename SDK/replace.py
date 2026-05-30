import re
import os

with open('/Users/anshul/Desktop/projects/camera/SDK/EuclidCamSDK/SDK/src/flash.py', 'r') as f:
    content = f.read()

# Replace the imports
content = content.replace("import uuid", "import uuid\nimport hashlib\nimport binascii")

# Replace from the beginning of nm_conn to the end of the inject_configuration function
start_marker = "    nm_conn = f\"\"\"[connection]"
end_marker = "        with open(cmdline_path, \"w\", newline='\\n') as f:\n            f.write(cmdline + \"\\n\")"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker) + len(end_marker)

replacement = """    psk_bytes = hashlib.pbkdf2_hmac('sha1', password.encode('utf-8'), ssid.encode('utf-8'), 4096, 32)
    wpa_psk = binascii.hexlify(psk_bytes).decode('utf-8')
    
    network_config = f\"\"\"network:
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
\"\"\"
    
    user_data = f\"\"\"#cloud-config
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

runcmd:
  - mkdir -p /etc/udev/rules.d
  - |
    cat << 'EOF' > /etc/udev/rules.d/99-calibration.rules
    ACTION=="add|change", KERNEL=="event[0-9]*", ENV{{ID_INPUT_TOUCHSCREEN}}=="1", ENV{{LIBINPUT_CALIBRATION_MATRIX}}="0 -1 1 1 0 0"
    EOF
  - |
    if [ -d /boot/firmware/firmware_payload ]; then
        mkdir -p /opt/euclidcam
        mv /boot/firmware/firmware_payload /opt/euclidcam/firmware
        
        cat << 'EOF2' > /usr/local/bin/start.sh
        #!/bin/bash
        if [ ! -f /opt/euclidcam/.setup_done ]; then
            clear
            echo "======================================"
            echo " Initializing EuclidCam for first use "
            echo " Waiting for Wi-Fi connection...      "
            echo "======================================"
            until ping -c 1 8.8.8.8 &>/dev/null; do
                sleep 2
            done
            
            echo "Installing dependencies..."
            cd /opt/euclidcam/firmware/python || exit 1
            pip install -r requirements.txt --break-system-packages
            touch /opt/euclidcam/.setup_done
        fi
        cd /opt/euclidcam/firmware/python || exit 1
        export DISPLAY=:0
        python3 main.py
        EOF2
        
        chmod +x /usr/local/bin/start.sh
        
        cat << 'EOF3' > /etc/profile.d/99-euclidcam.sh
        if [ -z "$DISPLAY" ] && [ $(tty) = /dev/tty1 ]; then
            /usr/local/bin/start.sh
        fi
        EOF3
    fi
\"\"\"
    
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
            
        with open(cmdline_path, "w", newline='\\n') as f:
            f.write(cmdline + "\\n")
"""

content = content[:start_idx] + replacement + content[end_idx:]

with open('/Users/anshul/Desktop/projects/camera/SDK/EuclidCamSDK/SDK/src/flash.py', 'w') as f:
    f.write(content)

