#!/usr/bin/env python3
"""
Improved ingestion for better accuracy
"""
import os
import shutil
import json
from app.utils import VectorStore

print("🔄 RE-INGESTING FOR BETTER ACCURACY")
print("=" * 60)

# 1. Backup old data
if os.path.exists("vector_store"):
    shutil.move("vector_store", "vector_store_backup")
    print("📦 Backed up old vector store")

# 2. Load existing chunks
if not os.path.exists("data/extracted_chunks.json"):
    print("❌ No extracted chunks found")
    exit(1)

with open("data/extracted_chunks.json", 'r') as f:
    chunks = json.load(f)

print(f"📊 Loaded {len(chunks)} chunks")

# 3. Filter and improve chunks
improved_chunks = []
for chunk in chunks:
    content = chunk['content'].strip()
    
    # Skip very short chunks
    if len(content) < 30:
        continue
    
    # Skip chunks that are mostly special characters
    if sum(1 for c in content if c.isalpha()) < len(content) * 0.3:
        continue
    
    # Enhance metadata
    chunk['content'] = content
    improved_chunks.append(chunk)

print(f"📈 After filtering: {len(improved_chunks)} chunks")

# 4. Create new vector store
texts = [c['content'] for c in improved_chunks]
metadata = improved_chunks

vector_store = VectorStore()
print("\n🤖 Creating improved vector index...")
vector_store.create_index(texts, metadata)

print("\n✅ Re-ingestion complete!")
print("   Test with: python validate_responses.py")
