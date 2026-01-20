import faiss
import numpy as np
import os
import pickle
from typing import List, Tuple
from app.ai.embeddings import embed_text

# Paths must match what you defined in ingest_pdfs.py
INDEX_FILE = "app/data/library_index.faiss"
METADATA_FILE = "app/data/metadata.npy"

class Retriever:
    def __init__(self):
        self.index = None
        self.metadata = []
        self._load_index()

    def _load_index(self):
        """
        Loads the FAISS index and metadata from disk.
        """
        if not os.path.exists(INDEX_FILE) or not os.path.exists(METADATA_FILE):
            print(f"⚠️ Warning: Index files not found at {INDEX_FILE}. Search will return empty.")
            return

        try:
            self.index = faiss.read_index(INDEX_FILE)
            # Allow memory mapping for speed if index is huge (optional)
            # self.index = faiss.read_index(INDEX_FILE, faiss.IO_FLAG_MMAP)
            
            self.metadata = np.load(METADATA_FILE, allow_pickle=True).tolist()
            print(f"✅ Loaded Index: {self.index.ntotal} vectors available.")
        except Exception as e:
            print(f"❌ Error loading index: {e}")

    def search(self, query: str, k: int = 5) -> List[str]:
        """
        Embeds the query and searches the FAISS index for the top k similar chunks.
        
        Returns:
            List[str]: A list of the matching text chunks.
        """
        if not self.index:
            return []

        # 1. Embed the query (using the same embedding logic as ingestion)
        query_vector = embed_text(query)
        
        # 2. Reshape for FAISS (1, dimension)
        # FAISS expects a matrix of queries, even if it's just one.
        query_matrix = np.array([query_vector]).astype('float32')

        # 3. Search
        # D: Distances (lower is better for L2, higher is better for Inner Product)
        # I: Indices of the nearest neighbors
        D, I = self.index.search(query_matrix, k)
        
        results = []
        indices = I[0] # The results for the first (and only) query

        for idx in indices:
            if idx == -1: continue # FAISS returns -1 if not enough neighbors found
            
            # The metadata file stores "filename:::text_content"
            # We split it to get just the content, or return the whole thing.
            full_record = self.metadata[idx]
            
            # Optional parsing: remove filename to just give LLM the text
            # Assuming format: "filename.pdf:::Actual text here..."
            parts = full_record.split(":::", 1)
            content = parts[1] if len(parts) > 1 else full_record
            
            results.append(content)

        return results

# Singleton instance to avoid reloading index on every request
retriever = Retriever()
