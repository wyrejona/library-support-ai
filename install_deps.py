#!/usr/bin/env python3
"""
Install dependencies
"""
import subprocess
import sys

def install_packages():
    packages = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-multipart==0.0.6",
        "pypdf==3.17.4",
        "numpy==1.26.4",
        "ollama==0.6.1",
        "huggingface-hub==0.19.4",
        "transformers==4.36.2",
        "scikit-learn==1.3.2",
        "requests==2.31.0"
    ]
    
    print("Installing dependencies...")
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package}")
        except subprocess.CalledProcessError:
            print(f"⚠️  Failed to install {package}")
    
    print("\n✅ Installation complete!")
    print("\nNext steps:")
    print("1. Start Ollama: ollama serve")
    print("2. Download a model: ollama pull phi")
    print("3. Run the app: python run.py")

if __name__ == "__main__":
    install_packages()
