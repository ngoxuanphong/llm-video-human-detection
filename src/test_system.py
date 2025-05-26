#!/usr/bin/env python3
"""
Test script for the Fall Detection System
This script tests individual components before running the full system
"""

import cv2
import os
import dotenv
from openai import OpenAI
from telegram import Bot
import asyncio

dotenv.load_dotenv()

async def test_telegram_connection():
    """Test Telegram bot connection"""
    print("Testing Telegram connection...")
    
    # Check if Telegram is enabled
    use_tele_alert = os.environ.get("USE_TELE_ALERT", "false").lower() == "true"
    if not use_tele_alert:
        print("ℹ️  Telegram notifications disabled by configuration (USE_TELE_ALERT=false)")
        return True  # Not an error, just disabled
    
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("❌ Telegram credentials not found in .env file")
        return False
    
    try:
        bot = Bot(token=token)
        await bot.send_message(chat_id=chat_id, text="🤖 Fall detection system test message")
        print("✅ Telegram connection successful")
        return True
    except Exception as e:
        print(f"❌ Telegram connection failed: {e}")
        return False

def test_openai_connection():
    """Test OpenAI API connection"""
    print("Testing OpenAI connection...")
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OpenAI API key not found in .env file")
        return False
    
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello, this is a test message."}],
            max_tokens=10
        )
        print("✅ OpenAI connection successful")
        return True
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False

def test_camera():
    """Test camera connection"""
    print("Testing camera connection...")
    
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Camera not accessible")
            return False
        
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to capture frame")
            cap.release()
            return False
        
        print(f"✅ Camera working - Frame size: {frame.shape}")
        cap.release()
        return True
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("=== Fall Detection System Tests ===\n")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found. Please create one using env_template.txt as reference")
        return
    
    tests = [
        ("Camera", test_camera),
        ("OpenAI API", test_openai_connection),
        ("Telegram Bot", test_telegram_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        results.append((test_name, result))
        print()
    
    print("=== Test Results ===")
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "="*30)
    if all_passed:
        print("🎉 All tests passed! System ready to run.")
        print("Run: python fall_detection_system.py")
    else:
        print("⚠️  Some tests failed. Please fix the issues before running the system.")

if __name__ == "__main__":
    asyncio.run(main()) 