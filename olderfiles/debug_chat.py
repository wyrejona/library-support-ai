import sys
import os

# Set up path
project_root = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(project_root, 'app')
sys.path.insert(0, project_root)
sys.path.insert(0, app_dir)

from app.main import app

print("=== Debugging /chat endpoint ===")
print()

# Find all /chat routes
chat_routes = []
for route in app.routes:
    if '/chat' in route.path:
        chat_routes.append(route)

if len(chat_routes) == 0:
    print("❌ No /chat routes found!")
elif len(chat_routes) == 1:
    route = chat_routes[0]
    methods = ', '.join(sorted(route.methods)) if hasattr(route, 'methods') else 'GET,HEAD'
    print(f"✅ Found 1 /chat route:")
    print(f"   Path: {route.path}")
    print(f"   Methods: {methods}")
    print(f"   Endpoint: {route.endpoint.__name__ if hasattr(route, 'endpoint') else 'N/A'}")
    
    # Check if it's the right endpoint
    endpoint = route.endpoint
    if hasattr(endpoint, '__name__'):
        if endpoint.__name__ == 'chat_page':
            print("   ✅ Endpoint is 'chat_page' (should handle GET)")
        elif endpoint.__name__ == 'chat_api':
            print("   ❌ Endpoint is 'chat_api' (should be for POST only)")
        else:
            print(f"   ⚠ Endpoint name: {endpoint.__name__}")
else:
    print(f"✅ Found {len(chat_routes)} /chat routes:")
    for i, route in enumerate(chat_routes, 1):
        methods = ', '.join(sorted(route.methods)) if hasattr(route, 'methods') else 'GET,HEAD'
        endpoint_name = route.endpoint.__name__ if hasattr(route.endpoint, '__name__') else 'N/A'
        print(f"  {i}. Path: {route.path}")
        print(f"     Methods: {methods}")
        print(f"     Endpoint: {endpoint_name}")

print()
print("=== Testing import ===")
try:
    from app.main import app
    print("✅ Successfully imported app")
    
    # Check if chat_page function exists
    from app.main import chat_page
    print("✅ chat_page function exists")
except ImportError as e:
    print(f"❌ Import error: {e}")
except AttributeError as e:
    print(f"❌ Attribute error: {e}")

print()
print("=== Quick test with test client ===")
try:
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # Test GET
    response = client.get("/chat")
    print(f"GET /chat status: {response.status_code}")
    if response.status_code == 200:
        print("✅ GET /chat works!")
    elif response.status_code == 405:
        print("❌ GET /chat returns 405 - Method Not Allowed")
        print("   This means the route exists but doesn't accept GET method")
    
    # Test POST
    response = client.post("/chat", json={"message": "test"})
    print(f"POST /chat status: {response.status_code}")
    if response.status_code == 200:
        print("✅ POST /chat works!")
    
except Exception as e:
    print(f"❌ Test client error: {e}")
