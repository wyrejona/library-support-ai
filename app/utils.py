import os
import pickle
import numpy as np
from typing import List, Dict, Any
import hashlib

class SimpleEmbedder:
    """Simple TF-IDF based embedder without sentence-transformers"""
    
    def __init__(self):
        self.vectorizer = None
        self.is_fitted = False
        
    def fit(self, texts: List[str]):
        """Fit TF-IDF vectorizer"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.vectorizer.fit(texts)
        self.is_fitted = True
    
    def encode(self, text: str) -> np.ndarray:
        """Encode text to vector"""
        if not self.is_fitted:
            raise ValueError("Vectorizer not fitted")
        
        return self.vectorizer.transform([text]).toarray()[0]
    
    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """Encode multiple texts"""
        if not self.is_fitted:
            raise ValueError("Vectorizer not fitted")
        
        return self.vectorizer.transform(texts).toarray()

class VectorStore:
    def __init__(self):
        self.embedder = SimpleEmbedder()
        self.embeddings = None
        self.metadata = []
        
    def create_index(self, texts: List[str], metadata: List[Dict[str, Any]]):
        """Create search index from texts"""
        print(f"Creating index for {len(texts)} text chunks...")
        
        # Fit embedder and generate embeddings
        self.embedder.fit(texts)
        self.embeddings = self.embedder.encode_batch(texts)
        self.metadata = metadata
        
        # Save to disk
        self._save()
        print(f"✅ Index saved with {len(texts)} chunks")
    
    def _save(self):
        """Save index to disk"""
        os.makedirs("data", exist_ok=True)
        
        data = {
            'embeddings': self.embeddings,
            'metadata': self.metadata,
            'vocabulary': self.embedder.vectorizer.vocabulary_,
            'idf': self.embedder.vectorizer.idf_
        }
        
        with open("data/metadata.pkl", 'wb') as f:
            pickle.dump(data, f)
    
    def load(self):
        """Load index from disk"""
        if not os.path.exists("data/metadata.pkl"):
            return False
        
        try:
            with open("data/metadata.pkl", 'rb') as f:
                data = pickle.load(f)
            
            self.embeddings = data['embeddings']
            self.metadata = data['metadata']
            
            # Recreate vectorizer
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.embedder.vectorizer = TfidfVectorizer(
                vocabulary=data['vocabulary']
            )
            self.embedder.vectorizer.idf_ = data['idf']
            self.embedder.is_fitted = True
            
            print(f"✅ Loaded index with {len(self.metadata)} chunks")
            return True
            
        except Exception as e:
            print(f"❌ Error loading index: {e}")
            return False
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if not self.load():
            return []
        
        # Encode query
        query_embedding = self.embedder.encode(query)
        
        # Calculate cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(
            query_embedding.reshape(1, -1), 
            self.embeddings
        )[0]
        
        # Get top k results
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
    """Format search results for LLM context"""
    if not search_results:
        return ""
    
    context_parts = []
    for result in search_results:
        source = result['source']
        page = result.get('page')
        page_info = f" (page {page})" if page else ""
        content = result['content']
        
        # Limit content length
        if len(content) > 500:
            content = content[:500] + "..."
        
        context_parts.append(f"[From {source}{page_info}]: {content}")
    
    return "\n\n".join(context_parts)
