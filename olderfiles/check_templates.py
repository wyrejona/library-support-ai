import os
import sys
from pathlib import Path

print("=== Template File Check ===")
print()

# Check from project root
project_root = Path(os.getcwd())
print(f"Project root: {project_root}")

# Possible template locations
possible_locations = [
    project_root / "app" / "templates",
    project_root / "templates", 
    project_root / "app" / "templates" / "chat.html",
    project_root / "templates" / "chat.html"
]

for loc in possible_locations:
    if loc.exists():
        if loc.is_file():
            print(f"✅ Found: {loc} (file)")
        else:
            print(f"✅ Found: {loc} (directory)")
            # List contents
            try:
                files = os.listdir(loc)
                print(f"   Contents: {files}")
                if "chat.html" in files:
                    print(f"   ✅ chat.html found in directory")
                    chat_path = loc / "chat.html"
                    print(f"   Full path: {chat_path}")
                    print(f"   File size: {os.path.getsize(chat_path)} bytes")
            except Exception as e:
                print(f"   Error listing: {e}")
    else:
        print(f"❌ Not found: {loc}")

print()
print("=== Current working directory contents ===")
for item in os.listdir(project_root):
    print(f"  {item}/" if os.path.isdir(os.path.join(project_root, item)) else f"  {item}")

print()
print("=== app/ directory contents ===")
app_dir = project_root / "app"
if app_dir.exists():
    for item in os.listdir(app_dir):
        path = app_dir / item
        print(f"  {item}/" if path.is_dir() else f"  {item}")
else:
    print("❌ app/ directory not found!")

