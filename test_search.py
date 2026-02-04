from app.utils import VectorStore

vector_store = VectorStore()
print("Testing search for 'library hours':")
results = vector_store.search("library hours", k=5)
for i, r in enumerate(results[:3]):
    print(f"\n--- Result {i+1} (score: {r.get('similarity_score', 0):.3f}) ---")
    print(f"Section: {r.get('section_number')} - {r.get('section_title', '')}")
    print(f"Content: {r['content'][:200]}...")

print("\n\nTesting search for 'plagiarism':")
results = vector_store.search("plagiarism", k=5)
for i, r in enumerate(results[:3]):
    print(f"\n--- Result {i+1} (score: {r.get('similarity_score', 0):.3f}) ---")
    print(f"Section: {r.get('section_number')} - {r.get('section_title', '')}")
    print(f"Content: {r['content'][:200]}...")
