import sys
print(f"Python: {sys.executable}")

try:
    import sentence_transformers
    print("✅ sentence_transformers imported successfully!")
    print(f"Location: {sentence_transformers.__file__}")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Trying from sentence_transformers import SentenceTransformer...")
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ from sentence_transformers import SentenceTransformer worked!")
    except ImportError as e2:
        print(f"❌ Also failed: {e2}")
