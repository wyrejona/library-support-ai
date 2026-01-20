import os
import glob
import numpy as np
import faiss
from app.pdf.loader import load_pdf  # You need to implement this one
from app.pdf.chunker import chunk_text
from app.ai.embeddings import embed_text

# Configuration
PDF_DIR = "pdfs/"
INDEX_FILE = "app/data/library_index.faiss"
METADATA_FILE = "app/data/metadata.npy" # To store which chunk belongs to which file

def main():
    pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    if not pdf_files:
        print("No PDFs found in pdfs/ folder.")
        return

    all_vectors = []
    all_metadata = [] # Stores strings like "filename.pdf | chunk_index"

    print(f"Found {len(pdf_files)} PDFs. Starting ingestion...")

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"Processing {filename}...")
        
        # 1. Load Text
        try:
            raw_text = load_pdf(pdf_path) # Needs to be implemented
        except Exception as e:
            print(f"Failed to load {filename}: {e}")
            continue

        # 2. Chunk Text
        chunks = chunk_text(raw_text)
        print(f"  - Generated {len(chunks)} chunks.")

        # 3. Embed Chunks
        for i, chunk in enumerate(chunks):
            vector = embed_text(chunk)
            all_vectors.append(vector)
            all_metadata.append(f"{filename}:::{chunk}") # Store simple ref or full text

    if not all_vectors:
        print("No data to index.")
        return

    # 4. Create FAISS Index
    vectors_array = np.vstack(all_vectors)
    d = vectors_array.shape[1] # Should be 768
    
    print(f"Building FAISS index with dimension {d}...")
    index = faiss.IndexFlatL2(d)
    index.add(vectors_array)

    # 5. Save
    os.makedirs("app/data", exist_ok=True)
    faiss.write_index(index, INDEX_FILE)
    np.save(METADATA_FILE, all_metadata)
    
    print(f"Successfully saved index to {INDEX_FILE} with {index.ntotal} vectors.")

if __name__ == "__main__":
    main()
