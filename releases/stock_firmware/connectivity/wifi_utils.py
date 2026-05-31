import os
import subprocess
import time

def parse_wifi_qr(text):
    """
    Parses a WiFi QR string: WIFI:S:<SSID>;T:<TYPE>;P:<PASS>;;
    Returns (ssid, password) or (None, None)
    """
    if not text.startswith("WIFI:"):
        return None, None
    
    parts = text[5:].split(";")
    ssid = None
    password = None
    
    for part in parts:
        if part.startswith("S:"):
            ssid = part[2:]
        elif part.startswith("P:"):
            password = part[2:]
            
    return ssid, password

def connect_to_wifi(ssid, password):
    """
    Attempts to connect to WiFi using nmcli.
    Returns (success, message)
    """
    if not ssid:
        return False, "No SSID provided"
    
    print(f"[SYSTEM] Attempting to connect to {ssid}...")
    
    try:
        # Check if nmcli is available
        subprocess.check_output(["which", "nmcli"])
        
        # Connect using nmcli
        cmd = ["nmcli", "device", "wifi", "connect", ssid]
        if password:
            cmd.extend(["password", password])
            
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            return True, f"Connected to {ssid}"
        else:
            return False, f"Failed: {result.stderr.strip()}"
            
    except subprocess.CalledProcessError:
        # fallback or nmcli missing
        return False, "nmcli not found or error"
    except Exception as e:
        return False, f"Error: {e}"

def is_online():
    """Checks if we have an IP address that isn't localhost"""
    try:
        output = subprocess.check_output(["hostname", "-I"]).decode().strip()
        return len(output.split()) > 0
    except:
        return False
