#!/usr/bin/env python3
import sys
import os

# Add the app directory to Python path
current_file = os.path.abspath(__file__)
app_dir = os.path.dirname(os.path.dirname(current_file))
sys.path.insert(0, app_dir)

try:
    print("Testing imports...")
    
    # Test config import
    from app.config import config
    print(f"✓ Config loaded: chat_model = {config.chat_model}")
    
    # Test llm import
    from app.ai.llm import OllamaClient
    print("✓ OllamaClient imported successfully")
    
    # Test utils import
    from app.utils import VectorStore, format_context
    print("✓ VectorStore and format_context imported successfully")
    
    print("\n✅ All imports successful!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nPossible solutions:")
    print("1. Check file structure:")
    print("   - app/__init__.py should exist (can be empty)")
    print("   - app/ai/__init__.py should exist (can be empty)")
    print("   - app/utils.py should exist")
    print("2. Check file permissions")
    
except Exception as e:
    print(f"❌ Other error: {e}")
