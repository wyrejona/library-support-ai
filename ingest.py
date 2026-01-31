#!/usr/bin/env python3
"""
Optimized PDF ingestion script for Library Support AI
Uses Recursive Character Splitting for better LLM performance.
"""
import os
import PyPDF2
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter

def extract_text_from_pdf(pdf_path: str) -> List[Dict[ Any, Any]]:
    """Extract and split text into efficient semantic chunks"""
    text_chunks = []
    filename = os.path.basename(pdf_path)
    
    # 600 characters is a "sweet spot" for local models on hardware like the OptiPlex 3040.
    # It provides enough context without triggering timeouts.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=60,
        length_function=len,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                raw_text = page.extract_text()
                if not raw_text or not raw_text.strip():
                    continue

                # Basic cleaning: remove extra whitespace
                clean_text = " ".join(raw_text.split())
                
                # Split page text into manageable chunks
                page_chunks = text_splitter.split_text(clean_text)
                
                for chunk in page_chunks:
                    # Filter out uselessly small fragments (e.g., just a page number)
                    if len(chunk.strip()) > 60:
                        text_chunks.append({
                            'content': chunk.strip(),
                            'source': filename,
                            'page': page_num
                        })
        
        print(f"  ✅ Extracted {len(text_chunks)} optimized chunks from {filename}")
        
    except Exception as e:
        print(f"  ❌ Error reading {pdf_path}: {str(e)}")
    
    return text_chunks

def main():
    print("=" * 50)
    print("📄 Optimized PDF Ingestion Script")
    print("=" * 50)
    
    pdfs_dir = "pdfs"
    if not os.path.exists(pdfs_dir):
        os.makedirs(pdfs_dir)
        print(f"📁 Created '{pdfs_dir}' directory. Place your PDFs there and re-run.")
        return
    
    pdf_files = [f for f in os.listdir(pdfs_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("❌ No PDF files found in 'pdfs/' directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s):")
    for pdf in pdf_files:
        print(f"  • {pdf}")
    
    all_chunks = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdfs_dir, pdf_file)
        chunks = extract_text_from_pdf(pdf_path)
        all_chunks.extend(chunks)
    
    if not all_chunks:
        print("❌ No text could be extracted.")
        return
    
    print(f"\n📊 Total chunks to index: {len(all_chunks)}")
    
    # Create vector index
    try:
        from app.utils import VectorStore
        
        texts = [chunk['content'] for chunk in all_chunks]
        # Passing full chunk dicts as metadata
        metadata = all_chunks
        
        print("🧠 Generating embeddings and saving index...")
        vector_store = VectorStore()
        vector_store.create_index(texts, metadata)
        
        print(f"\n🎉 Ingestion complete!")
        print(f"  Index saved to: data/metadata.pkl (and your vector store path)")
        
    except Exception as e:
        print(f"\n❌ Error creating index: {e}")
        print("  Ensure dependencies are installed: pip install sentence-transformers faiss-cpu")

if __name__ == "__main__":
    main()
