#!/usr/bin/env python3
"""
Debug script to test the chat pipeline.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import config
from app.utils import VectorStore, format_context
from app.ai.llm import OllamaClient

print("🔍 Debugging Chat Pipeline")
print("=" * 60)

# 1. Test Vector Store
print("1. Testing Vector Store...")
vector_store = VectorStore()
vector_store.load()

if not vector_store.loaded:
    print("❌ Vector store not loaded")
    sys.exit(1)

print(f"✅ Vector store loaded with {len(vector_store.chunks)} chunks")

# 2. Test search for "What is MyLOFT?"
query = "What is MyLOFT?"
print(f"\n2. Searching for: '{query}'")
search_results = vector_store.search(query, k=5)

if not search_results:
    print("❌ No search results found!")
    sys.exit(1)

print(f"✅ Found {len(search_results)} results")
for i, result in enumerate(search_results[:3]):
    print(f"   Result {i+1}: Score={result['score']:.3f}")
    preview = result['content'][:100].replace('\n', ' ')
    print(f"      Preview: {preview}...")

# 3. Test context formatting
print(f"\n3. Testing context formatting...")
context = format_context(search_results)
print(f"✅ Context length: {len(context)} characters")
print(f"\n📝 First 500 chars of context:")
print("-" * 50)
print(context[:500])
print("-" * 50)

# 4. Test LLM response
print(f"\n4. Testing LLM response...")
llm_client = OllamaClient()

# Check if Ollama is running
print(f"   Using model: {llm_client.model}")
print(f"   Ollama base URL: {llm_client.base_url}")

try:
    # Test connection
    import requests
    response = requests.get(f"{llm_client.base_url}/api/tags", timeout=5)
    if response.status_code == 200:
        print("✅ Ollama is running")
    else:
        print(f"❌ Ollama returned status {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Cannot connect to Ollama: {e}")
    sys.exit(1)

# Test generate_response with context
print(f"\n5. Testing generate_response with context...")
response = llm_client.generate_response(prompt=query, context=context)
print(f"✅ Response received ({len(response)} chars):")
print("=" * 60)
print(response)
print("=" * 60)

# 6. Test without context
print(f"\n6. Testing generate_response WITHOUT context...")
response_no_context = llm_client.generate_response(prompt=query, context="")
print(f"Response without context:")
print("=" * 60)
print(response_no_context)
print("=" * 60)

print("\n✅ Debug complete!")
