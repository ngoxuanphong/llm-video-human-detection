#!/usr/bin/env python3
"""
Setup script for Fall Detection System
This script helps users set up the system quickly
"""

import os
import subprocess
import sys


def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def create_env_file():
    """Create .env file from template"""
    if os.path.exists(".env"):
        print("⚠️  .env file already exists, skipping creation")
        return True

    if not os.path.exists("env_template.txt"):
        print("❌ env_template.txt not found")
        return False

    try:
        with open("env_template.txt", "r") as template:
            content = template.read()

        with open(".env", "w") as env_file:
            env_file.write(content)

        print("✅ .env file created from template")
        print("📝 Please edit .env file with your actual credentials")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def check_camera():
    """Check if camera is available"""
    try:
        import cv2

        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✅ Camera found and accessible")
            cap.release()
            return True
        else:
            print("⚠️  Camera not accessible (this might be normal if no camera is connected)")
            return False
    except Exception as e:
        print(f"⚠️  Camera check failed: {e}")
        return False


def print_next_steps():
    """Print instructions for next steps"""
    print("\n" + "=" * 50)
    print("🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Edit .env file with your credentials:")
    print("   - OPENAI_API_KEY (required - get from https://platform.openai.com/api-keys)")
    print("   - USE_TELE_ALERT=true/false (optional - enable/disable Telegram alerts)")
    print("   - TELEGRAM_BOT_TOKEN (optional - get from @BotFather on Telegram)")
    print("   - TELEGRAM_CHAT_ID (optional - get from bot updates)")
    print("\n2. Test the system:")
    print("   python test_system.py")
    print("\n3. Run the fall detection system:")
    print("   python fall_detection_system.py")
    print("\n📖 See README.md for detailed instructions")
    print("=" * 50)


def main():
    """Main setup function"""
    print("=== Fall Detection System Setup ===\n")

    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return

    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

    # Install dependencies
    if not install_dependencies():
        return

    # Create environment file
    if not create_env_file():
        return

    # Check camera (optional)
    check_camera()

    # Show next steps
    print_next_steps()


if __name__ == "__main__":
    main()
