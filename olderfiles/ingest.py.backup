#!/usr/bin/env python3
"""
Optimized PDF ingestion script for Library Support AI.
Ensures the index is refreshed and only contains currently present PDFs.
"""
import os
import PyPDF2
import shutil
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter

def extract_text_from_pdf(pdf_path: str) -> List[Dict[Any, Any]]:
    """Extract and split text into efficient semantic chunks"""
    text_chunks = []
    filename = os.path.basename(pdf_path)
    
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

                clean_text = " ".join(raw_text.split())
                page_chunks = text_splitter.split_text(clean_text)
                
                for chunk in page_chunks:
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
    print("🔄 Refreshing PDF Ingestion Index")
    print("=" * 50)
    
    pdfs_dir = "pdfs"
    data_dir = "data"
    
    # --- OPTIMIZATION STEP: CLEAR OLD INDEX DATA ---
    # This ensures that if a PDF was deleted from the folder, 
    # its data is also removed from the AI's memory.
    if os.path.exists(data_dir):
        print("🧹 Cleaning old index files to ensure a fresh sync...")
        for file in os.listdir(data_dir):
            file_path = os.path.join(data_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"  ⚠️ Warning: Could not delete {file_path}: {e}")
    else:
        os.makedirs(data_dir)

    if not os.path.exists(pdfs_dir):
        os.makedirs(pdfs_dir)
        print(f"📁 Created '{pdfs_dir}' directory.")
        return
    
    pdf_files = [f for f in os.listdir(pdfs_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("❌ No PDF files found in 'pdfs/' directory. Index cleared.")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s) for indexing:")
    all_chunks = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdfs_dir, pdf_file)
        chunks = extract_text_from_pdf(pdf_path)
        all_chunks.extend(chunks)
    
    if not all_chunks:
        print("❌ No text could be extracted.")
        return
    
    # --- CREATE NEW VECTOR INDEX ---
    try:
        from app.utils import VectorStore
        
        texts = [chunk['content'] for chunk in all_chunks]
        metadata = all_chunks
        
        print(f"\n🧠 Generating fresh embeddings for {len(all_chunks)} chunks...")
        vector_store = VectorStore()
        vector_store.create_index(texts, metadata)
        
        print(f"\n🎉 Ingestion complete! The AI is now synced with your pdfs/ folder.")
        
    except Exception as e:
        print(f"\n❌ Error creating index: {e}")

if __name__ == "__main__":
    main()
