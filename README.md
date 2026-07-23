# EuclidCam SDK & Flasher Application

A cross-platform desktop manager, flasher utility, and deployment suite for the EuclidCam firmware. Built with Python and Flet (Flutter engine).

---

## Features

- **Automated Setup**: Instant virtual environment initialization and dependency resolution.
- **Firmware Flasher & Deployer**: Remotely SSH into a Raspberry Pi camera board, clone/update firmware, and trigger automated setup.
- **Real-Time Log Monitoring**: Live logging overlay for tracking installation progress and hardware initialization.
- **Cross-Platform**: Runs on macOS, Linux, and Windows.

---

## Quick Start (Recommended)

Run the included automated bootstrap script:

```bash
chmod +x run_sdk.sh
./run_sdk.sh
```

The script will automatically:
1. Create an isolated Python virtual environment (`venv`).
2. Install all required dependencies (`flet`, `httpx`, `certifi`).
3. Launch the **EuclidCam SDK** desktop interface.

---

## Manual Setup

If you prefer to set up your environment manually:

### 1. Prerequisites
- **Python 3.9+** installed on your computer.

### 2. Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the SDK
```bash
python3 sdk.py
```

---

## Firmware Selection & Flashing Engine

The SDK provides dual-mode firmware selection when provisioning camera boards:

### 1. Firmware Selection Modes
- **Stock Firmware (Default)**: Automatically fetches and installs the latest official live release directly from GitHub (`https://github.org/anshuliyer/EuclidCam.git`).
- **Custom Firmware**: Allows developers to specify a path to a custom local firmware build or modified Python directory to deploy to the target hardware.

### 2. Role of `releases/stock_firmware`
The [`releases/stock_firmware/`](file:///Users/anshul/Desktop/projects/camera/SDK/EuclidCamSDK/releases/stock_firmware) directory serves two key roles:
- **Offline First-Boot Fallback**: When flashing an SD card locally, `stock_firmware` is copied to `/boot/firmware_payload`. If the target Raspberry Pi is booted offline without internet access, the installation daemon automatically extracts and installs from this offline payload.
- **Developer Reference Snapshot**: Provides a local, offline template of the stock firmware codebase for inspecting, diffing, and building custom camera modules or UI themes.

---

## Project Structure

```
EuclidCamSDK/
├── sdk.py              # Main Flet desktop GUI & flasher controller
├── run_sdk.sh          # One-click environment bootstrap & launch script
├── requirements.txt    # Python dependencies (Flet, HTTPX, etc.)
├── releases/           # Offline firmware payload & stock release snapshots
│   └── stock_firmware/ # Offline fallback payload for network-less setups
├── SDK/src/flash.py    # Hardware deployment daemon & SD flasher script
├── assets/             # Logos and graphic UI assets
├── bin/ & exec/        # Native helper binaries
├── LICENSE             # GNU Affero General Public License v3.0 (AGPLv3)
└── README.md           # Documentation & architecture guide
```

---

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPLv3)** — see the [LICENSE](LICENSE) file for details.
