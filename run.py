import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now import and run
from app.main import app

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Library Support AI Server...")
    print("📂 PDFs directory:", os.path.join(os.getcwd(), "pdfs"))
    print("🗄️  Data directory:", os.path.join(os.getcwd(), "data"))
    print("🌐 Web interface: http://localhost:8000")
    print("\n📊 Registered endpoints:")
    for route in app.routes:
        methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'GET'
        print(f"  {methods:15} {route.path}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
