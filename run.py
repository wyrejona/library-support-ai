#!/usr/bin/env python3
"""
Start the application
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.main import app
    import uvicorn
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Run: python install_deps.py")
    sys.exit(1)

if __name__ == "__main__":
    print("🚀 Starting PDF Chat Assistant")
    print("=" * 50)
    
    # Check directories
    os.makedirs("pdfs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    print(f"📁 PDF directory: {os.path.abspath('pdfs')}")
    print(f"💾 Data directory: {os.path.abspath('data')}")
    
    # Check Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/version", timeout=2)
        print("✅ Ollama service is running")
        
        # Check models
        models = requests.get("http://localhost:11434/api/tags", timeout=2).json()
        if models.get('models'):
            print(f"✅ Models available: {[m['model'] for m in models['models']]}")
        else:
            print("⚠️  No models found. Run: ollama pull phi")
    except:
        print("⚠️  Ollama service not detected")
        print("   Start it with: ollama serve")
        print("   Or download from: https://ollama.com")
    
    print("\n📚 Open browser to: http://localhost:8000")
    print("\nUsage:")
    print("1. Upload PDF files using the web interface")
    print("2. Click 'Process PDFs' to make them searchable")
    print("3. Chat with your documents!")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
