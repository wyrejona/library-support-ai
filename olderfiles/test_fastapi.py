import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(project_root, 'app')
sys.path.insert(0, project_root)
sys.path.insert(0, app_dir)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=== Testing /chat endpoints ===")
print()

# Test GET
print("1. Testing GET /chat:")
response = client.get("/chat")
print(f"   Status: {response.status_code}")
print(f"   Content-Type: {response.headers.get('content-type')}")
if response.status_code == 200:
    print("   ✅ GET works!")
    # Check if it's HTML
    if "text/html" in response.headers.get("content-type", ""):
        print("   ✅ Returns HTML")
        # Check for title
        if "<title>" in response.text:
            title = response.text.split("<title>")[1].split("</title>")[0]
            print(f"   ✅ Page title: {title}")
elif response.status_code == 405:
    print("   ❌ GET returns 405 - Method Not Allowed")
    print("   Headers:", dict(response.headers))
else:
    print(f"   ❌ Unexpected status: {response.status_code}")

print()

# Test POST
print("2. Testing POST /chat:")
response = client.post("/chat", json={"message": "test message"})
print(f"   Status: {response.status_code}")
print(f"   Content-Type: {response.headers.get('content-type')}")
if response.status_code == 200:
    print("   ✅ POST works!")
    data = response.json()
    print(f"   Response: {data.get('response', 'No response')[:50]}...")
else:
    print(f"   ❌ POST failed: {response.status_code}")
    
print()
print("=== All routes ===")
for route in app.routes:
    methods = ', '.join(sorted(route.methods)) if hasattr(route, 'methods') else 'GET,HEAD'
    print(f"{methods:15} {route.path}")
