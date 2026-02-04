import os
import PyPDF2
from typing import List, Dict, Any
from app.utils import VectorStore
from app.config import settings

def extract_text_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    text_chunks = []
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            filename = os.path.basename(pdf_path)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                    for paragraph in paragraphs:
                        if len(paragraph) > 50:
                            text_chunks.append({
                                'content': paragraph,
                                'source': filename,
                                'page': page_num
                            })
    except Exception as e:
        print(f"Error reading {pdf_path}: {str(e)}")
    return text_chunks

def ingest_pdfs():
    # FIXED: lowercase .pdfs_dir
    pdfs_dir = settings.pdfs_dir
    
    if not os.path.exists(pdfs_dir):
        print(f"PDFs directory '{pdfs_dir}' not found!")
        return
    
    all_chunks = []
    for filename in os.listdir(pdfs_dir):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(pdfs_dir, filename)
            print(f"Processing: {filename}")
            chunks = extract_text_from_pdf(pdf_path)
            all_chunks.extend(chunks)
            print(f"  Extracted {len(chunks)} chunks")
    
    if not all_chunks:
        print("No text extracted!")
        return
    
    texts = [chunk['content'] for chunk in all_chunks]
    metadata = all_chunks
    
    vector_store = VectorStore()
    vector_store.create_index(texts, metadata)
    
    print(f"\n✅ Ingestion complete! Processed {len(all_chunks)} chunks.")

if __name__ == "__main__":
    os.makedirs("app/data", exist_ok=True)
    print("Starting PDF ingestion...")
    ingest_pdfs()
