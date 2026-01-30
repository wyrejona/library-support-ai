#!/usr/bin/env python3
"""
Simple PDF ingestion script
"""
import os
import PyPDF2
from typing import List, Dict, Any

def extract_text_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract text from PDF"""
    text_chunks = []
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            filename = os.path.basename(pdf_path)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    # Split into sentences/paragraphs
                    paragraphs = []
                    current_para = []
                    
                    for line in text.split('\n'):
                        line = line.strip()
                        if line:
                            current_para.append(line)
                        elif current_para:
                            paragraphs.append(' '.join(current_para))
                            current_para = []
                    
                    if current_para:
                        paragraphs.append(' '.join(current_para))
                    
                    # Add chunks
                    for para in paragraphs:
                        if len(para) > 30:  # Minimum length
                            text_chunks.append({
                                'content': para,
                                'source': filename,
                                'page': page_num
                            })
        
        print(f"  Extracted {len(text_chunks)} chunks from {filename}")
        
    except Exception as e:
        print(f"  Error reading {pdf_path}: {str(e)}")
    
    return text_chunks

def main():
    print("=" * 50)
    print("📄 PDF Ingestion Script")
    print("=" * 50)
    
    # Check PDFs directory
    pdfs_dir = "pdfs"
    if not os.path.exists(pdfs_dir):
        print(f"❌ PDFs directory '{pdfs_dir}' not found!")
        print(f"   Create it with: mkdir {pdfs_dir}")
        return
    
    # Get PDF files
    pdf_files = [f for f in os.listdir(pdfs_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("❌ No PDF files found in 'pdfs/' directory")
        print("   Please upload PDF files first using the web interface")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s):")
    for pdf in pdf_files:
        print(f"  • {pdf}")
    
    # Extract text from all PDFs
    all_chunks = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdfs_dir, pdf_file)
        chunks = extract_text_from_pdf(pdf_path)
        all_chunks.extend(chunks)
    
    if not all_chunks:
        print("❌ No text could be extracted from PDFs")
        return
    
    print(f"\n✅ Extracted {len(all_chunks)} text chunks in total")
    
    # Create vector index
    try:
        from app.utils import VectorStore
        
        texts = [chunk['content'] for chunk in all_chunks]
        metadata = all_chunks
        
        vector_store = VectorStore()
        vector_store.create_index(texts, metadata)
        
        print(f"\n🎉 Ingestion complete!")
        print(f"   Index saved to: data/metadata.pkl")
        print(f"   You can now chat about your documents!")
        
    except ImportError as e:
        print(f"\n⚠️  Missing dependency: {e}")
        print("   Install scikit-learn with: pip install scikit-learn")
    except Exception as e:
        print(f"\n❌ Error creating index: {e}")

if __name__ == "__main__":
    main()
