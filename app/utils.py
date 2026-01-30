import os
import pickle
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from app.config import settings

class LocalEmbedder:
    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embeddings for a single text string"""
        return self.model.encode(text)
    
    def embed_documents(self, documents: List[str]) -> np.ndarray:
        """Generate embeddings for multiple documents"""
        return self.model.encode(documents)

class VectorStore:
    def __init__(self):
        self.index = None
        self.metadata = []
        self.embedder = LocalEmbedder()
    
    def create_index(self, texts: List[str], metadata: List[Dict[str, Any]]):
        """Create FAISS index from texts"""
        import faiss
        
        embeddings = self.embedder.embed_documents(texts)
        dimension = embeddings.shape[1]
        
        # Create FAISS index
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))
        self.metadata = metadata
        
        # Save index and metadata
        self.save()
    
    def save(self):
        """Save index and metadata to disk"""
        import faiss
        faiss.write_index(self.index, settings.FAISS_INDEX_PATH)
        
        with open(settings.METADATA_PATH, 'wb') as f:
            pickle.dump(self.metadata, f)
    
    def load(self):
        """Load index and metadata from disk"""
        import faiss
        
        if os.path.exists(settings.FAISS_INDEX_PATH):
            self.index = faiss.read_index(settings.FAISS_INDEX_PATH)
            
            with open(settings.METADATA_PATH, 'rb') as f:
                self.metadata = pickle.load(f)
            return True
        return False
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if not self.index:
            if not self.load():
                return []
        
        query_embedding = self.embedder.embed_text(query).astype('float32').reshape(1, -1)
        
        # Search in FAISS index
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                results.append({
                    'content': self.metadata[idx]['content'],
                    'source': self.metadata[idx]['source'],
                    'page': self.metadata[idx].get('page'),
                    'distance': float(distances[0][i])
                })
        
        return results

def format_context(search_results: List[Dict[str, Any]]) -> str:
    """Format search results into context string for LLM"""
    context_parts = []
    for i, result in enumerate(search_results):
        source = result['source']
        page_info = f" (Page {result['page']})" if result.get('page') else ""
        context_parts.append(f"[Source: {source}{page_info}]:\n{result['content']}\n")
    
    return "\n".join(context_parts)
