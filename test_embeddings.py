#!/usr/bin/env python3
"""
Test script to verify embeddings and search work correctly.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import config
from app.utils import VectorStore
import json

def test_embeddings():
    print("🧪 Testing Vector Store Embeddings")
    print("=" * 50)
    
    # Initialize vector store
    vector_store = VectorStore()
    
    # Try to load existing index
    print("📂 Loading vector store...")
    vector_store.load()
    
    if not vector_store.loaded:
        print("❌ Vector store not loaded. Please run ingestion first.")
        print("   Run: python ingest.py")
        return
    
    # Get stats
    stats = vector_store.get_stats()
    print(f"✅ Vector store loaded:")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Embedding model: {stats['embedding_model']}")
    
    if 'keyword_counts' in stats:
        print(f"   Keyword counts:")
        for keyword, count in stats['keyword_counts'].items():
            print(f"     {keyword}: {count}")
    
    print("\n🔍 Testing searches:")
    
    # Test queries
    test_queries = [
        "What is MyLOFT?",
        "How do I access past exam papers?",
        "What are the library borrowing rules?",
        "How do I avoid plagiarism?",
        "What are the library hours?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 30)
        
        # Extract keywords (using the function from utils)
        from app.utils import extract_key_query_terms
        keywords = extract_key_query_terms(query)
        print(f"   Keywords: {keywords}")
        
        # Search
        results = vector_store.search(query, k=3)
        
        if results:
            for i, result in enumerate(results[:2]):  # Show top 2
                print(f"   Result {i+1}: Score={result['score']:.3f}")
                
                # Show preview
                content_preview = result['content'][:150].replace('\n', ' ')
                if len(result['content']) > 150:
                    content_preview += "..."
                print(f"      Preview: {content_preview}")
                
                # Check for MyLOFT
                if 'myloft' in query.lower() and 'myloft' in result['content'].lower():
                    print(f"      ✅ Contains 'MyLOFT'")
        else:
            print("   ❌ No results found")
    
    # Test specific MyLOFT search
    print("\n" + "=" * 50)
    print("📱 Detailed MyLOFT Search Test")
    print("=" * 50)
    
    myloft_query = "What is MyLOFT and how do I use it?"
    results = vector_store.search(myloft_query, k=5)
    
    if results:
        print(f"Found {len(results)} results for MyLOFT:")
        for i, result in enumerate(results):
            has_myloft = 'myloft' in result['content'].lower()
            print(f"{i+1}. Score: {result['score']:.3f}, Has MyLOFT: {has_myloft}")
            
            # Show section if available
            lines = result['content'].split('\n')
            for line in lines[:3]:
                if line.strip() and len(line.strip()) > 10:
                    print(f"   {line[:100]}...")
                    break
    else:
        print("❌ No MyLOFT results found. The ingestion may have failed.")
    
    print("\n" + "=" * 50)
    print("✅ Test complete!")

if __name__ == "__main__":
    test_embeddings()
