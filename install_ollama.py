#!/usr/bin/env python3
"""
Safe Ollama installer that doesn't hang on downloads.
Run: python install_ollama.py
"""
import os
import sys
import platform
import subprocess
import urllib.request
import zipfile
import tarfile
import time

def check_ollama_installed():
    """Check if Ollama is already installed and running"""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ Ollama is already installed")
            print(f"   Version: {result.stdout.strip()}")
            return True
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return False

def check_ollama_running():
    """Check if Ollama service is running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/version", timeout=3)
        if response.status_code == 200:
            print("✅ Ollama service is running")
            return True
    except:
        pass
    return False

def install_ollama_windows():
    """Install Ollama on Windows"""
    print("📥 Installing Ollama on Windows...")
    
    # Download installer
    url = "https://ollama.com/download/OllamaSetup.exe"
    installer_path = "OllamaSetup.exe"
    
    try:
        print(f"Downloading from {url}...")
        urllib.request.urlretrieve(url, installer_path)
        
        print("Running installer...")
        subprocess.run([installer_path, "/S"], check=True)
        
        # Wait for installation
        time.sleep(5)
        os.remove(installer_path)
        
        print("✅ Ollama installed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def install_ollama_mac():
    """Install Ollama on macOS"""
    print("📥 Installing Ollama on macOS...")
    
    try:
        # Using curl to download and install
        install_script = """
        /bin/bash -c "$(curl -fsSL https://ollama.com/install.sh)"
        """
        
        print("Running installation script...")
        result = subprocess.run(
            ["/bin/bash", "-c", install_script],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Ollama installed successfully!")
            return True
        else:
            print(f"❌ Installation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def install_ollama_linux():
    """Install Ollama on Linux"""
    print("📥 Installing Ollama on Linux...")
    
    try:
        # Using curl to download and install
        install_script = """
        curl -fsSL https://ollama.com/install.sh | sh
        """
        
        print("Running installation script...")
        result = subprocess.run(
            ["/bin/bash", "-c", install_script],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Ollama installed successfully!")
            return True
        else:
            print(f"❌ Installation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def start_ollama_service():
    """Start Ollama service"""
    print("🚀 Starting Ollama service...")
    
    system = platform.system()
    
    try:
        if system == "Windows":
            subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(["ollama", "serve"], start_new_session=True)
        
        # Wait for service to start
        print("Waiting for Ollama to start (10 seconds)...")
        time.sleep(10)
        
        if check_ollama_running():
            print("✅ Ollama service started successfully!")
            return True
        else:
            print("⚠️  Ollama might still be starting. Checking again in 5 seconds...")
            time.sleep(5)
            if check_ollama_running():
                print("✅ Ollama service started successfully!")
                return True
        
        print("⚠️  Ollama service might need to be started manually.")
        print("   Run 'ollama serve' in a separate terminal.")
        return False
        
    except Exception as e:
        print(f"❌ Failed to start Ollama: {e}")
        return False

def download_model_safe(model_name="phi"):
    """
    Safely download a model with progress and timeout
    """
    print(f"📦 Downloading model: {model_name}")
    print("   This may take a few minutes depending on your internet speed...")
    
    try:
        # Use subprocess with timeout
        process = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Read output line by line
        for line in process.stdout:
            line = line.strip()
            if line:
                print(f"   {line}")
        
        # Wait with timeout (10 minutes)
        try:
            return_code = process.wait(timeout=600)
            if return_code == 0:
                print(f"✅ Model '{model_name}' downloaded successfully!")
                return True
            else:
                print(f"❌ Model download failed with code: {return_code}")
                return False
        except subprocess.TimeoutExpired:
            print("❌ Model download timed out after 10 minutes")
            process.kill()
            return False
            
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        return False

def main():
    print("=" * 60)
    print("Ollama Setup Script")
    print("=" * 60)
    
    # Check current OS
    system = platform.system()
    print(f"Detected OS: {system}")
    
    # Step 1: Check if Ollama is already installed
    if not check_ollama_installed():
        # Step 2: Install Ollama based on OS
        print("\n📥 Ollama not found. Installing...")
        
        if system == "Windows":
            success = install_ollama_windows()
        elif system == "Darwin":  # macOS
            success = install_ollama_mac()
        elif system == "Linux":
            success = install_ollama_linux()
        else:
            print(f"❌ Unsupported OS: {system}")
            sys.exit(1)
        
        if not success:
            print("\n⚠️  Automatic installation failed.")
            print("Please install Ollama manually from: https://ollama.com")
            print("Then run this script again.")
            sys.exit(1)
    
    # Step 3: Start Ollama service
    if not check_ollama_running():
        print("\n🔧 Starting Ollama service...")
        start_ollama_service()
    
    # Step 4: Download a small model
    print("\n" + "=" * 60)
    print("Downloading a lightweight model for testing...")
    print("=" * 60)
    
    # List of small models (prioritized)
    small_models = ["phi", "tinyllama", "llama2:7b", "neural-chat"]
    
    for model in small_models:
        print(f"\nTrying to download: {model}")
        if download_model_safe(model):
            print(f"\n✅ Success! Using model: {model}")
            
            # Update config file
            update_config(model)
            break
        else:
            print(f"⚠️  Failed to download {model}, trying next...")
    else:
        print("\n❌ Could not download any models.")
        print("Please check your internet connection and try:")
        print("   ollama pull phi  # Smallest model")
    
    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the application: python -m app.main")
    print("2. Open browser to: http://localhost:8000")
    print("3. Login with admin/admin123")
    print("\nTo download more models manually:")
    print("   ollama pull llama2:7b      # 7B parameter model")
    print("   ollama pull mistral        # 7B model")
    print("   ollama pull neural-chat    # Chat-optimized")

def update_config(model_name):
    """Update the config file with the downloaded model"""
    config_file = "app/config.py"
    
    try:
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Update the model name
        import re
        new_content = re.sub(
            r'OLLAMA_MODEL: str = ".*?"',
            f'OLLAMA_MODEL: str = "{model_name}"',
            content
        )
        
        with open(config_file, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Updated config to use model: {model_name}")
        
    except Exception as e:
        print(f"⚠️  Could not update config: {e}")
        print(f"   Please set OLLAMA_MODEL = '{model_name}' in app/config.py manually")

if __name__ == "__main__":
    main()
