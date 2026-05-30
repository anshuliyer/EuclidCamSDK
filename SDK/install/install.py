#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import platform

def main():
    print("========================================")
    print("    EuclidCamSDK Flasher Installer      ")
    print("========================================")

    print("\n[1/3] Ensuring PyInstaller is installed...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    except subprocess.CalledProcessError:
        print("Error: Failed to install PyInstaller. Please ensure pip is installed.")
        sys.exit(1)

    # Determine paths
    install_dir = os.path.dirname(os.path.abspath(__file__))
    sdk_dir = os.path.dirname(install_dir)
    src_file = os.path.join(sdk_dir, "src", "flash.py")
    
    if not os.path.exists(src_file):
        print(f"Error: Could not find source file at {src_file}")
        sys.exit(1)

    print("\n[2/3] Building OS-native standalone executable...")
    build_dir = os.path.join(install_dir, "build")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--distpath", sdk_dir,
            "--workpath", build_dir,
            "--specpath", install_dir,
            src_file
        ])
    except subprocess.CalledProcessError as e:
        print(f"Error: Build failed with code {e.returncode}")
        sys.exit(1)

    print("\n[3/3] Cleaning up build artifacts...")
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    spec_file = os.path.join(install_dir, "flash.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)

    exe_name = "flash.exe" if platform.system() == "Windows" else "flash"
    exe_path = os.path.join(sdk_dir, exe_name)
    
    print("\n" + "="*40)
    print("Installation Complete!")
    print(f"Standalone executable generated successfully at:")
    print(f"-> {exe_path}")
    print("="*40)

if __name__ == "__main__":
    main()
