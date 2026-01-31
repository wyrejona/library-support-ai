import os
import pickle
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import faiss  # Using FAISS for much faster vector search

class VectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # This model is ~80MB and very fast on CPUs
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.metadata = []
        
    def create_index(self, texts: List[str], metadata: List[Dict[str, Any]]):
        """Create a semantic search index"""
        print(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Initialize FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings).astype('float32'))
        
        self.metadata = metadata
        self._save()
    
    def _save(self):
        """Save vector index and metadata to disk"""
        os.makedirs("data", exist_ok=True)
        # Save FAISS index
        faiss.write_index(self.index, "data/vector_index.bin")
        # Save metadata
        with open("data/metadata.pkl", 'wb') as f:
            pickle.dump(self.metadata, f)
    
    def load(self) -> bool:
        """Load index from disk"""
        if not os.path.exists("data/vector_index.bin"):
            return False
        try:
            self.index = faiss.read_index("data/vector_index.bin")
            with open("data/metadata.pkl", 'rb') as f:
                self.metadata = pickle.load(f)
            return True
        except Exception as e:
            print(f"❌ Load error: {e}")
            return False

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Perform semantic search with strict limit 'k' to prevent LLM timeouts"""
        if not self.load():
            return []
        
        # Encode query to the same vector space
        query_vec = self.model.encode([query]).astype('float32')
        
        # Search FAISS
        distances, indices = self.index.search(query_vec, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata):
                res = self.metadata[idx]
                res['score'] = float(distances[0][i])
                results.append(res)
        return results

def format_context(search_results: List[Dict[str, Any]]) -> str:
    """Format results with source citations for the LLM"""
    if not search_results:
        return "No relevant library documents found."
    
    context_parts = []
    for res in search_results:
        # Cited context helps the LLM stay accurate
        context_parts.append(
            f"--- SOURCE: {res['source']} (Page {res.get('page', 'N/A')}) ---\n"
            f"{res['content']}"
        )
    return "\n\n".join(context_parts)
