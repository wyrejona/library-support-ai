import os
import pickle
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from app.config import settings

class LocalEmbedder:
    def __init__(self):
        # Uses your installed sentence-transformers
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
        embeddings = self.embedder.embed_documents(texts)
        self.metadata = metadata
        
        # Try to use FAISS if available, otherwise use numpy
        try:
            import faiss
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings.astype('float32'))
            self.use_faiss = True
            
            # Save FAISS index
            faiss.write_index(self.index, settings.FAISS_INDEX_PATH)
            print("✅ Created FAISS index")
            
        except ImportError:
            # Fallback to numpy array
            self.embeddings = embeddings
            self.use_faiss = False
            print("⚠️  FAISS not available, using numpy array for search")
        
        # Save metadata
        with open(settings.METADATA_PATH, 'wb') as f:
            pickle.dump({
                'metadata': metadata,
                'use_faiss': self.use_faiss
            }, f)
    
    def load(self):
        """Load index and metadata from disk"""
        if not os.path.exists(settings.METADATA_PATH):
            return False
        
        with open(settings.METADATA_PATH, 'rb') as f:
            data = pickle.load(f)
        
        self.metadata = data['metadata']
        self.use_faiss = data.get('use_faiss', False)
        
        if self.use_faiss and os.path.exists(settings.FAISS_INDEX_PATH):
            try:
                import faiss
                self.index = faiss.read_index(settings.FAISS_INDEX_PATH)
                return True
            except ImportError:
                print("❌ FAISS index exists but FAISS not installed")
                return False
        elif not self.use_faiss and 'embeddings' in data:
            self.embeddings = data['embeddings']
            return True
        
        return False
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if not self.load():
            return []
        
        query_embedding = self.embedder.embed_text(query)
        
        if self.use_faiss:
            # FAISS search
            query_embedding = query_embedding.astype('float32').reshape(1, -1)
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
        else:
            # Numpy cosine similarity search
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity(
                query_embedding.reshape(1, -1), 
                self.embeddings
            )[0]
            
            top_indices = np.argsort(similarities)[::-1][:k]
            results = []
            for idx in top_indices:
                if idx < len(self.metadata):
                    results.append({
                        'content': self.metadata[idx]['content'],
                        'source': self.metadata[idx]['source'],
                        'page': self.metadata[idx].get('page'),
                        'similarity': float(similarities[idx])
                    })
        
        return results

def format_context(search_results: List[Dict[str, Any]]) -> str:
    """Format search results into context string"""
    context_parts = []
    for i, result in enumerate(search_results):
        source = result['source']
        page_info = f" (Page {result['page']})" if result.get('page') else ""
        content = result['content']
        if len(content) > 500:
            content = content[:500] + "..."
        context_parts.append(f"[Source: {source}{page_info}]:\n{content}\n")
    
    return "\n".join(context_parts)
