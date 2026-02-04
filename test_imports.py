import sys
from pathlib import Path

print("Python path:")
for p in sys.path:
    print(f"  {p}")

print("\nTesting imports...")

try:
    from app.utils import VectorStore
    print("✓ Imported VectorStore from app.utils")
except ImportError as e:
    print(f"✗ Failed to import VectorStore: {e}")

try:
    from app.ai.llm import OllamaClient
    print("✓ Imported OllamaClient from app.ai.llm")
except ImportError as e:
    print(f"✗ Failed to import OllamaClient: {e}")

# Test basic dependencies
try:
    import fastapi
    print("✓ Imported fastapi")
except ImportError as e:
    print(f"✗ Failed to import fastapi: {e}")

try:
    import sentence_transformers
    print("✓ Imported sentence_transformers")
except ImportError as e:
    print(f"✗ Failed to import sentence_transformers: {e}")
