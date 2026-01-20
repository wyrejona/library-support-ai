import faiss
import numpy as np
import os
import pickle
from app.ai.embeddings import embed_text

# Define exact paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # points to /app
DATA_DIR = os.path.join(BASE_DIR, "data")
INDEX_FILE = os.path.join(DATA_DIR, "library_index.faiss")
METADATA_FILE = os.path.join(DATA_DIR, "metadata.npy")

class Retriever:
    def __init__(self):
        self.index = None
        self.metadata = []
        self._load_index()

    def _load_index(self):
        if not os.path.exists(INDEX_FILE) or not os.path.exists(METADATA_FILE):
            print(f"⚠️  WARNING: Index file not found at {INDEX_FILE}")
            print("   (This is normal if you haven't run 'python ingest_pdfs.py' yet)")
            return

        try:
            self.index = faiss.read_index(INDEX_FILE)
            self.metadata = np.load(METADATA_FILE, allow_pickle=True).tolist()
            print(f"✅ Loaded Index: {self.index.ntotal} vectors available.")
        except Exception as e:
            print(f"❌ Error loading index: {e}")

    def search(self, query: str, k: int = 5):
        if not self.index:
            return [] # Return empty list if no index exists

        try:
            query_vector = embed_text(query)
            query_matrix = np.array([query_vector]).astype('float32')
            
            D, I = self.index.search(query_matrix, k)
            
            results = []
            indices = I[0]
            for idx in indices:
                if idx == -1: continue
                # Parse metadata (format: "filename:::text")
                full_record = self.metadata[idx]
                parts = full_record.split(":::", 1)
                content = parts[1] if len(parts) > 1 else full_record
                results.append(content)
                
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return []

# Create the instance
retriever = Retriever()
