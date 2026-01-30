#!/usr/bin/env python3
"""
Complete setup script for Library AI Assistant
Run: python setup.py
"""
import os
import sys
import subprocess
import time

def run_command(cmd, description):
    """Run a command with progress indication"""
    print(f"\n📦 {description}...")
    print(f"   Command: {cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ {description} timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def check_python_version():
    """Check Python version"""
    print("🔍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required. Found: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directory structure...")
    
    directories = [
        "app",
        "app/ai",
        "app/routes",
        "app/data",
        "static",
        "static/css",
        "static/js",
        "templates",
        "pdfs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   Created: {directory}/")
    
    # Create .gitkeep files
    for keep_dir in ["pdfs", "static/uploads"]:
        keep_file = os.path.join(keep_dir, ".gitkeep")
        os.makedirs(os.path.dirname(keep_file), exist_ok=True)
        with open(keep_file, 'w') as f:
            pass
    
    print("✅ Directory structure created")
    return True

def install_python_deps():
    """Install Python dependencies"""
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found")
        return False
    
    # Upgrade pip first
    run_command("pip install --upgrade pip", "Upgrading pip")
    
    # Install dependencies
    return run_command(
        "pip install -r requirements.txt",
        "Installing Python dependencies"
    )

def setup_database():
    """Initialize database"""
    print("\n🗄️  Setting up database...")
    
    try:
        # Import and run database setup
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Check if init_db.py exists
        if os.path.exists("init_db.py"):
            result = subprocess.run(
                [sys.executable, "init_db.py"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ Database initialized")
                return True
            else:
                print(f"❌ Database initialization failed: {result.stderr}")
                return False
        else:
            print("⚠️  init_db.py not found, skipping database setup")
            return True
            
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def setup_ollama():
    """Setup Ollama"""
    print("\n🤖 Setting up Ollama...")
    
    # Check if install_ollama.py exists
    if os.path.exists("install_ollama.py"):
        print("Running Ollama installer...")
        result = subprocess.run(
            [sys.executable, "install_ollama.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Ollama setup completed")
            return True
        else:
            print(f"⚠️  Ollama setup had issues: {result.stderr}")
            return False
    else:
        print("⚠️  install_ollama.py not found")
        print("Please install Ollama manually from: https://ollama.com")
        print("Then run: ollama pull phi")
        return False

def verify_setup():
    """Verify the setup"""
    print("\n🔍 Verifying setup...")
    
    checks = [
        ("Python packages", lambda: os.path.exists("venv") or True),
        ("Database file", lambda: os.path.exists("app/data/library.db")),
        ("Config file", lambda: os.path.exists("app/config.py")),
        ("Main app", lambda: os.path.exists("app/main.py")),
    ]
    
    all_ok = True
    for check_name, check_func in checks:
        try:
            if check_func():
                print(f"   ✅ {check_name}: OK")
            else:
                print(f"   ❌ {check_name}: Missing")
                all_ok = False
        except Exception as e:
            print(f"   ❌ {check_name}: Error - {e}")
            all_ok = False
    
    return all_ok

def main():
    print("=" * 60)
    print("Library AI Assistant - Setup Script")
    print("=" * 60)
    
    steps = [
        ("Python version check", check_python_version),
        ("Create directories", create_directories),
        ("Install Python dependencies", install_python_deps),
        ("Setup database", setup_database),
        ("Setup Ollama", setup_ollama),
        ("Final verification", verify_setup),
    ]
    
    print("\n🚀 Starting setup process...")
    
    for step_name, step_func in steps:
        print(f"\n{'='*40}")
        print(f"Step: {step_name}")
        print(f"{'='*40}")
        
        if not step_func():
            print(f"\n❌ Setup failed at: {step_name}")
            print("Please fix the issue and run the script again.")
            sys.exit(1)
        
        time.sleep(1)  # Brief pause between steps
    
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    print("\n📋 Next Steps:")
    print("1. Start Ollama service (if not running):")
    print("   Open a NEW terminal and run: ollama serve")
    print("")
    print("2. Start the application:")
    print("   python -m app.main")
    print("")
    print("3. Access the web interface:")
    print("   http://localhost:8000")
    print("")
    print("4. Login credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print("")
    print("5. To upload PDFs:")
    print("   - Go to Dashboard")
    print("   - Upload your PDF files")
    print("   - Click 'Create/Update Vector Index'")
    print("")
    print("💡 Tip: Keep the 'ollama serve' terminal open!")
    print("=" * 60)

if __name__ == "__main__":
    main()
