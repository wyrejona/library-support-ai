#!/usr/bin/env python3
import os
import json

print("🔍 DEBUGGING INGESTION PROCESS")
print("=" * 60)

# Check if PDFs exist
pdfs_dir = "pdfs"
if os.path.exists(pdfs_dir):
    pdfs = [f for f in os.listdir(pdfs_dir) if f.endswith('.pdf')]
    print(f"📄 PDFs found: {len(pdfs)}")
    for pdf in pdfs:
        print(f"  • {pdf}")
else:
    print("❌ No 'pdfs' directory found")

# Check if data was extracted
if os.path.exists("data/extracted_chunks.json"):
    with open("data/extracted_chunks.json", 'r') as f:
        chunks = json.load(f)
    print(f"\n✅ Extracted chunks: {len(chunks)}")
    if chunks:
        print(f"Sample chunk:")
        print(f"  Content: {chunks[0]['content'][:100]}...")
else:
    print("\n❌ No extracted chunks found")

# Check vector store
if os.path.exists("vector_store/index.bin"):
    print(f"\n✅ Vector store exists")
    print(f"   Index size: {os.path.getsize('vector_store/index.bin') / 1024:.1f} KB")
else:
    print("\n❌ Vector store not created yet")

# Test Ollama
import requests
try:
    response = requests.get("http://localhost:11434/api/version", timeout=5)
    print(f"\n✅ Ollama is running: {response.status_code}")
except:
    print("\n❌ Ollama is NOT running or not accessible")

# Test embedding model
try:
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={"model": "nomic-embed-text:latest", "prompt": "test"},
        timeout=10
    )
    if response.status_code == 200:
        print(f"✅ Embedding model works")
        embedding = response.json()["embedding"]
        print(f"   Embedding dimension: {len(embedding)}")
    else:
        print(f"❌ Embedding model error: {response.status_code}")
except Exception as e:
    print(f"❌ Embedding test failed: {e}")
