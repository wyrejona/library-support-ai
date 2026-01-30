#!/usr/bin/env python3
"""
Start the application
"""
import os
import sys
import subprocess
import time

def check_ollama():
    """Check if Ollama is running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/version", timeout=3)
        if response.status_code == 200:
            print("✅ Ollama service is running")
            return True
    except:
        print("❌ Ollama service is not running")
        print("   Please start Ollama in another terminal:")
        print("   $ ollama serve")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    required = [
        'fastapi',
        'sqlalchemy',
        'pydantic',
        'sentence_transformers',
        'ollama',
        'pypdf',
    ]
    
    print("🔍 Checking dependencies...")
    missing = []
    
    for package in required:
        try:
            __import__(package.replace('_', '-'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("   Install with: pip install " + " ".join(missing))
        return False
    
    return True

def main():
    print("=" * 60)
    print("Library AI Assistant - Startup")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check Ollama
    if not check_ollama():
        print("\n⚠️  Starting without Ollama check...")
        print("   (Make sure Ollama is running for chat functionality)")
    
    # Start the application
    print("\n🚀 Starting application...")
    print(f"   Web interface: http://localhost:8000")
    print("   Press Ctrl+C to stop\n")
    
    try:
        # Import and run the app
        from app.main import app
        import uvicorn
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
    except KeyboardInterrupt:
        print("\n👋 Application stopped")
    except Exception as e:
        print(f"❌ Error starting application: {e}")

if __name__ == "__main__":
    main()
