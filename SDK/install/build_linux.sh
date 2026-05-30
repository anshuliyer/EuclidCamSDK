#!/bin/bash
# Cross-compile for Raspberry Pi Zero 2W (linux/arm64) using Docker

if ! command -v docker &> /dev/null; then
    echo "==========================================================="
    echo " ERROR: Docker is not installed or not running."
    echo " Please download and install Docker Desktop for Mac:"
    echo " https://www.docker.com/products/docker-desktop/"
    echo "==========================================================="
    exit 1
fi

echo "Starting Docker Cross-Compilation for Linux ARM64..."

FIRMWARE_DIR="/Users/anshul/Desktop/projects/camera/EuclidCam/firmware/python"
OUTPUT_DIR="/Users/anshul/Desktop/projects/camera/SDK/EuclidCamSDK/releases"

# Create a build container running Debian Bookworm (same base as Raspberry Pi OS)
# We compile under linux/arm64 to match the Pi Zero 2W
docker run --rm --platform linux/arm64 -v "$FIRMWARE_DIR:/src" -v "$OUTPUT_DIR:/dist" debian:bookworm /bin/bash -c "
    echo 'Installing build dependencies...' &&
    apt-get update &&
    apt-get install -y python3 python3-pip python3-venv build-essential python3-dev gcc &&
    
    echo 'Setting up virtual environment...' &&
    python3 -m venv /venv &&
    
    echo 'Installing python dependencies (evdev, flask, etc.)...' &&
    /venv/bin/pip install pyinstaller evdev numpy flask qrcode pillow &&
    
    echo 'Compiling firmware...' &&
    cd /src &&
    /venv/bin/pyinstaller --onefile --name test-release --distpath /dist main.py &&
    
    echo 'Compilation successful! Binary placed in /dist'
"

echo "==========================================================="
echo "Done! Your Linux executable is ready at:"
echo "$OUTPUT_DIR/test-release"
echo "==========================================================="
