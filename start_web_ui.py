#!/usr/bin/env python3
"""
Quick Start Script for Fall Detection Web UI
Checks dependencies and environment before launching
"""

import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required!")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}")
    return True


def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        ("gradio", "gradio"),
        ("cv2", "opencv-python"),
        ("openai", "openai"),
        ("dotenv", "python-dotenv"),
        ("rich", "rich"),
        ("numpy", "numpy"),
        ("PIL", "Pillow"),
    ]

    missing_packages = []

    for import_name, package_name in required_packages:
        try:
            __import__(import_name.replace("-", "_"))
            print(f"✅ {package_name}")
        except ImportError:
            missing_packages.append(package_name)
            print(f"❌ {package_name} - Missing!")

    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("🔧 Run: pip install -r requirements.txt")
        return False

    print("✅ All dependencies installed!")
    return True


def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path(".env")

    if not env_path.exists():
        print("❌ .env file not found!")
        print("🔧 Copy env_template.txt to .env and configure it")
        print("   cp env_template.txt .env")
        return False

    # Read .env file
    env_content = env_path.read_text()

    # Check for OPENAI_API_KEY
    if "OPENAI_API_KEY=" not in env_content or "your_openai_api_key_here" in env_content:
        print("❌ OPENAI_API_KEY not configured in .env!")
        print("🔧 Please set your OpenAI API key in .env file")
        return False

    print("✅ .env file configured")
    return True


def check_src_directory():
    """Check if src directory and modules exist"""
    src_path = Path("src")
    required_files = ["__init__.py", "utils.py", "alert.py"]

    if not src_path.exists():
        print("❌ src/ directory not found!")
        return False

    for file in required_files:
        if not (src_path / file).exists():
            print(f"❌ src/{file} not found!")
            return False

    print("✅ Source modules found")
    return True


def create_directories():
    """Create necessary directories"""
    dirs = ["temp", "evidence"]

    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Directory created/exists: {dir_name}/")


def main():
    """Main function to run all checks and start the web UI"""
    print("🏥 Fall Detection Web UI - Quick Start")
    print("=" * 50)

    # Run all checks
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("Source Modules", check_src_directory),
    ]

    print("\n🔍 Running pre-flight checks...")
    print("-" * 30)

    all_passed = True
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        if not check_func():
            all_passed = False

    if not all_passed:
        print("\n❌ Some checks failed!")
        print("Please fix the issues above before running the web UI.")
        sys.exit(1)

    # Create directories
    print("\n📁 Creating directories...")
    create_directories()

    print("\n✅ All checks passed!")
    print("🚀 Starting Fall Detection Web UI...")
    print("-" * 50)
    print("📱 Web UI will be available at: http://localhost:7860")
    print("🌐 Network access at: http://[your-ip]:7860")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)

    # Start the web UI
    try:
        subprocess.run([sys.executable, "main_ui.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Web UI stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting web UI: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ main_ui.py not found!")
        print("Make sure you're in the correct directory")
        sys.exit(1)


if __name__ == "__main__":
    main()
