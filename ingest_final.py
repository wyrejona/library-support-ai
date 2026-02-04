#!/usr/bin/env python3
"""
FINAL PDF INGESTION - Reliable and fast
"""
import os
import PyPDF2
import re
import json
import shutil
from typing import List, Dict, Any
import hashlib

def extract_pdf_simple(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract text with simple sentence-based chunking"""
    filename = os.path.basename(pdf_path)
    chunks = []
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if not text:
                    continue
                
                # Clean text
                text = re.sub(r'\s+', ' ', text)
                text = re.sub(r'(\w+)\n(\w+)', r'\1 \2', text)
                text = text.strip()
                
                # Split into sentences
                sentences = re.split(r'(?<=[.!?])\s+', text)
                
                # Create chunks of 2-3 sentences
                for i in range(0, len(sentences), 3):
                    chunk_sentences = sentences[i:i+3]
                    chunk_text = ' '.join(chunk_sentences).strip()
                    
                    if len(chunk_text) > 30:
                        chunk_id = hashlib.md5(f"{filename}_{page_num}_{i}".encode()).hexdigest()[:12]
                        
                        chunks.append({
                            'content': chunk_text,
                            'source': filename,
                            'page': page_num,
                            'chunk_id': chunk_id,
                            'length': len(chunk_text),
                            'is_procedure': bool(re.search(r'\b(step|procedure|how to|instructions?)\b', chunk_text, re.I)),
                            'is_critical': bool(re.search(r'past exam|exam paper|critical|important', chunk_text, re.I))
                        })
        
        return chunks
        
    except Exception as e:
        print(f"Error with {filename}: {e}")
        return []

def main():
    print("=" * 60)
    print("📚 LIBRARY PDF INGESTION")
    print("=" * 60)
    
    # Clean up
    for dir_path in ["data", "vector_store"]:
        if os.path.exists(dir_path):
            print(f"🗑️  Cleaning {dir_path}/...")
            shutil.rmtree(dir_path)
        os.makedirs(dir_path, exist_ok=True)
    
    # Check PDFs
    pdfs_dir = "pdfs"
    if not os.path.exists(pdfs_dir):
        os.makedirs(pdfs_dir)
        print(f"\n📁 Created '{pdfs_dir}' directory.")
        print("📄 Place 'Comprehensive University of Embu Library Guide.pdf' here.")
        return
    
    pdf_files = [f for f in os.listdir(pdfs_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print("\n✗ No PDF files found.")
        return
    
    print(f"\n📄 Processing {len(pdf_files)} PDF(s)...")
    all_chunks = []
    
    for pdf_file in pdf_files:
        print(f"\n🔄 {pdf_file}")
        chunks = extract_pdf_simple(os.path.join(pdfs_dir, pdf_file))
        print(f"  ✓ {len(chunks)} chunks")
        all_chunks.extend(chunks)
    
    if not all_chunks:
        print("\n✗ No content extracted.")
        return
    
    print(f"\n✅ Extraction: {len(all_chunks)} total chunks")
    
    # Save
    with open("data/extracted_chunks.json", 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    # Create vector store
    try:
        from app.utils import VectorStore
        
        print(f"\n🤖 Creating vector index...")
        
        texts = [c['content'] for c in all_chunks]
        metadata = all_chunks
        
        # Use small batch size for reliability
        vector_store = VectorStore()
        vector_store.create_index(texts, metadata, batch_size=3)
        
        # Quick test
        print(f"\n🔍 Quick test...")
        results = vector_store.search("library hours", k=2)
        if results:
            print(f"✓ Found {len(results)} results")
        else:
            print("✗ No results")
        
        print(f"\n🎉 INGESTION COMPLETE!")
        print(f"📊 Statistics:")
        print(f"   • Total chunks: {len(all_chunks)}")
        print(f"   • Vector store: vector_store/index.bin")
        print(f"   • Test query: python -c \"from app.utils import VectorStore; vs=VectorStore(); r=vs.search('library hours'); print(f'Results: {len(r)}')\"")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
