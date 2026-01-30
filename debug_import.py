import sys
import traceback

print(f"Python path: {sys.executable}")
print(f"Python version: {sys.version}")

try:
    import numpy
    print(f"NumPy: {numpy.__version__}")
except Exception as e:
    print(f"NumPy import error: {e}")

try:
    import scipy
    print(f"SciPy: {scipy.__version__}")
except Exception as e:
    print(f"SciPy import error: {e}")

print("\nTrying to import sentence_transformers...")
try:
    from sentence_transformers import SentenceTransformer
    print("✅ SUCCESS: sentence_transformers imported!")
    print(f"Location: {SentenceTransformer.__file__}")
except Exception as e:
    print("❌ ERROR importing sentence_transformers:")
    traceback.print_exc()
