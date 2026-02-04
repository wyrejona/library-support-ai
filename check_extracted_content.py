#!/usr/bin/env python3
"""
Check what content was actually extracted from PDF
"""
import json

try:
    with open('data/extracted_chunks.json', 'r') as f:
        chunks = json.load(f)
    
    print(f"📊 Extracted {len(chunks)} chunks")
    
    # Search for specific content
    search_terms = ['part-time', 'lecturer', 'borrow', 'circulation', 'hour', 'exam', 'plagiarism']
    
    for term in search_terms:
        matching = [c for c in chunks if term.lower() in c['content'].lower()]
        print(f"\n'{term}': Found in {len(matching)} chunks")
        if matching:
            for c in matching[:2]:  # Show first 2 matches
                print(f"  • {c['content'][:100]}...")
    
    # Check chunk statistics
    print(f"\n📈 Chunk statistics:")
    avg_len = sum(len(c['content']) for c in chunks) / len(chunks)
    print(f"  Average length: {avg_len:.0f} chars")
    
    # Check for procedures and critical info
    procedures = sum(1 for c in chunks if c.get('is_procedure', False))
    critical = sum(1 for c in chunks if c.get('is_critical', False))
    print(f"  Procedure chunks: {procedures}")
    print(f"  Critical chunks: {critical}")
    
    # Sample chunks
    print(f"\n🧪 Sample chunks (first 3):")
    for i, c in enumerate(chunks[:3]):
        print(f"\nChunk {i+1}:")
        print(f"  Content: {c['content'][:150]}...")
        print(f"  Source: {c.get('source', 'N/A')}")
        print(f"  Page: {c.get('page', 'N/A')}")
        
except FileNotFoundError:
    print("❌ No extracted chunks found. Run ingestion first.")
