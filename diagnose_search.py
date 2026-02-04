#!/usr/bin/env python3
"""
Diagnostic script to see what's in the search results.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils import VectorStore

print("🔍 Diagnosing Search Results")
print("=" * 60)

# Load vector store
store = VectorStore()
store.load()

if not store.loaded:
    print("❌ Vector store not loaded")
    sys.exit(1)

print(f"✅ Vector store loaded with {len(store.chunks)} chunks")

# Show what's actually in the chunks
print("\n📝 Sample of stored chunks:")
for i in range(min(3, len(store.chunks))):
    print(f"\nChunk {i}:")
    print("-" * 40)
    print(store.chunks[i][:200])
    print("-" * 40)

# Test search
query = "What is MyLOFT?"
print(f"\n🔍 Searching for: '{query}'")
results = store.search(query, k=5)

print(f"Found {len(results)} results")

for i, result in enumerate(results):
    print(f"\nResult {i}:")
    print(f"  Score: {result.get('score', 0)}")
    print(f"  Has 'content' key: {'content' in result}")
    print(f"  Content type: {type(result.get('content', 'NO CONTENT'))}")
    print(f"  Content length: {len(result.get('content', ''))}")
    print(f"  Content preview: {result.get('content', 'NO CONTENT')[:100]}...")
    
    # Check if content is actually a string
    content = result.get('content', '')
    if isinstance(content, str):
        print(f"  Is string: YES, length: {len(content)}")
    else:
        print(f"  Is string: NO, type: {type(content)}")

# Check metadata too
print(f"\n📊 Metadata for first result:")
if results:
    metadata = results[0].get('metadata', {})
    print(f"  Metadata keys: {list(metadata.keys())}")
    print(f"  Metadata: {metadata}")
