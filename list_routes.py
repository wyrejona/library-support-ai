import sys
import os

# Get the project root directory
project_root = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(project_root, 'app')

# Add both directories to Python path
sys.path.insert(0, project_root)
sys.path.insert(0, app_dir)

try:
    from app.main import app
    print("✅ Successfully imported app from app.main")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Trying alternative import...")
    # Try importing directly
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", os.path.join(app_dir, "main.py"))
    main_module = importlib.util.module_from_spec(spec)
    sys.modules["main"] = main_module
    spec.loader.exec_module(main_module)
    app = main_module.app

if __name__ == "__main__":
    print("\n=== Registered Routes ===")
    print(f"{'METHODS':15} {'PATH':30} {'NAME'}")
    print("-" * 60)
    
    for route in app.routes:
        methods = ', '.join(sorted(route.methods)) if hasattr(route, 'methods') else 'GET,HEAD'
        path = route.path
        name = getattr(route, 'name', 'N/A')
        print(f"{methods:15} {path:30} {name}")
    
    print(f"\nTotal routes: {len(app.routes)}")
