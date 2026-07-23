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

## Project Structure

```
EuclidCamSDK/
├── sdk.py              # Main Flet application entry point & desktop UI
├── run_sdk.sh          # One-click launch and environment setup script
├── requirements.txt    # Python dependencies (Flet, HTTPX, etc.)
├── releases/           # Firmware release bundles and stock images
├── assets/             # Logos and graphic assets
├── bin/ & exec/        # Native helper binaries
├── LICENSE             # GNU Affero General Public License v3.0 (AGPLv3)
└── README.md           # Documentation & usage guide
```

---

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPLv3)** — see the [LICENSE](LICENSE) file for details.
