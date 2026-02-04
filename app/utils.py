import faiss
import numpy as np
import pickle
import os
import json
import logging
from typing import List, Dict, Any
import re
from pathlib import Path

# Import config
try:
    from app.config import config
except ImportError:
    from config import config

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.index = None
        self.chunks = []
        self.metadata = []
        self.loaded = False
        
        # Use config settings
        self.embedding_model = config.embedding_model
        self.ollama_base_url = config.ollama_base_url
        
        # Initialize embeddings
        self._init_embeddings()
    
    def _init_embeddings(self):
        """Initialize embeddings with fallback options"""
        try:
            # First try the newer langchain-ollama
            try:
                from langchain_ollama import OllamaEmbeddings
                self.embeddings = OllamaEmbeddings(
                    model=self.embedding_model,
                    base_url=self.ollama_base_url
                )
                logger.info(f"✅ Using langchain_ollama embeddings with model: {self.embedding_model}")
            except ImportError:
                # Fallback to langchain_community
                try:
                    from langchain_community.embeddings import OllamaEmbeddings
                    self.embeddings = OllamaEmbeddings(
                        model=self.embedding_model,
                        base_url=self.ollama_base_url
                    )
                    logger.info(f"✅ Using langchain_community embeddings with model: {self.embedding_model}")
                except ImportError:
                    logger.error("❌ Neither langchain_ollama nor langchain_community available")
                    self.embeddings = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize embeddings: {e}")
            self.embeddings = None
    
    def create_index(self, texts: List[str], metadata_list: List[Dict] = None):
        """Create FAISS index using configured embedding model"""
        if not self.embeddings:
            logger.error("Embeddings not available. Please install langchain-ollama or langchain-community")
            logger.info("Run: pip install langchain-ollama")
            return
        
        try:
            logger.info(f"Creating embeddings for {len(texts)} chunks using {self.embedding_model}")
            
            # Create embeddings
            embeddings_list = self.embeddings.embed_documents(texts)
            
            # Convert to numpy
            embeddings_array = np.array(embeddings_list).astype('float32')
            
            # Debug: Check embedding dimensions
            logger.info(f"Embedding dimension: {embeddings_array.shape[1]}")
            
            # Create FAISS index
            dimension = embeddings_array.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings_array)
            
            # Store metadata
            self.chunks = texts
            self.metadata = metadata_list if metadata_list else [{} for _ in texts]
            self.loaded = True
            
            # Save
            self.save()
            
            logger.info(f"✅ Created index with {len(texts)} chunks, dimension {dimension}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create index: {e}")
            raise
    
    def save(self):
        """Save to configured vector store path"""
        if not self.index:
            logger.warning("No index to save")
            return
            
        os.makedirs(config.vector_store_path, exist_ok=True)
        
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(config.vector_store_path / "vector_index.bin"))
            
            # Save metadata
            with open(config.vector_store_path / "metadata.pkl", 'wb') as f:
                pickle.dump({
                    'chunks': self.chunks,
                    'metadata': self.metadata,
                    'embedding_model': self.embedding_model
                }, f)
            
            logger.info(f"💾 Saved vector store to {config.vector_store_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save vector store: {e}")
    
    def load(self):
        """Load from configured vector store path"""
        index_path = config.vector_store_path / "vector_index.bin"
        metadata_path = config.vector_store_path / "metadata.pkl"
        
        if not index_path.exists() or not metadata_path.exists():
            logger.warning(f"Vector store not found at {config.vector_store_path}")
            logger.info("💡 Run ingestion first: python ingest.py")
            return
            
        try:
            # Load FAISS index
            logger.info(f"📂 Loading FAISS index from {index_path}")
            self.index = faiss.read_index(str(index_path))
            
            # Load metadata
            logger.info(f"📂 Loading metadata from {metadata_path}")
            with open(metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.chunks = data['chunks']
                self.metadata = data['metadata']
                stored_model = data.get('embedding_model', 'unknown')
                logger.info(f"Stored with embedding model: {stored_model}")
            
            # Reinitialize embeddings
            self._init_embeddings()
            
            self.loaded = True
            logger.info(f"✅ Loaded vector store with {len(self.chunks)} chunks")
            
            # Debug: Show sample chunks
            if self.chunks:
                logger.info(f"Sample chunk (first 100 chars): {self.chunks[0][:100]}...")
            
        except Exception as e:
            logger.error(f"❌ Failed to load vector store: {e}")
            self.loaded = False
    
    def search(self, query: str, k: int = None) -> List[Dict[str, Any]]:
        """Search using configured settings"""
        if not self.loaded:
            logger.warning("Vector store not loaded")
            return []
            
        if not self.embeddings:
            logger.warning("Embeddings not available")
            return []
        
        # Use config default if k not specified
        if k is None:
            k = config.search_default_k
        
        try:
            # Get query embedding
            query_embedding = self.embeddings.embed_query(query)
            query_vector = np.array([query_embedding]).astype('float32')
            
            # Search
            distances, indices = self.index.search(query_vector, k)
            
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < 0 or idx >= len(self.chunks):
                    continue
                
                content = self.chunks[idx]
                
                # Calculate score (inverse of distance, higher is better)
                score = 1.0 / (1.0 + distance)
                
                results.append({
                    'content': content,
                    'score': score,
                    'distance': float(distance),
                    'metadata': self.metadata[idx] if idx < len(self.metadata) else {},
                    'index': idx
                })
            
            # Sort by score (descending)
            results.sort(key=lambda x: x['score'], reverse=True)
            
            # Log search results for debugging
            if results:
                logger.info(f"🔍 Search for '{query}' found {len(results)} results")
                logger.info(f"   Top score: {results[0]['score']:.4f}")
                if 'myloft' in query.lower():
                    myloft_matches = sum(1 for r in results if 'myloft' in r['content'].lower())
                    logger.info(f"   MyLOFT matches: {myloft_matches}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        if not self.loaded:
            return {"status": "not_loaded"}
        
        stats = {
            "status": "loaded",
            "total_chunks": len(self.chunks),
            "index_size": self.index.ntotal if self.index else 0,
            "embedding_model": self.embedding_model,
            "loaded": self.loaded,
            "sample_chunks": min(3, len(self.chunks))
        }
        
        # Count chunks with common keywords
        keyword_counts = {}
        keywords_to_check = ['myloft', 'library', 'borrowing', 'e-resources', 'plagiarism']
        
        for keyword in keywords_to_check:
            count = sum(1 for chunk in self.chunks if keyword.lower() in chunk.lower())
            keyword_counts[keyword] = count
        
        stats["keyword_counts"] = keyword_counts
        
        return stats


def format_context(search_results: List[Dict[str, Any]], max_length: int = None) -> str:
    """Format search results into context - FIXED VERSION"""
    if max_length is None:
        max_length = config.max_context_length
    
    if not search_results:
        logger.warning("format_context: No search results provided")
        return ""
    
    # Debug logging
    logger.info(f"format_context: Processing {len(search_results)} results")
    
    context_parts = []
    current_length = 0
    
    # Add simple header
    header = "Based on the library documents:\n\n"
    context_parts.append(header)
    current_length += len(header)
    
    # Add each result
    for i, result in enumerate(search_results):
        content = result.get('content', '')
        
        # Skip if content is not a string or is empty
        if not isinstance(content, str) or not content.strip():
            logger.warning(f"format_context: Result {i} has invalid content")
            continue
        
        # Format this result
        formatted = f"[Document {i+1}]\n{content.strip()}\n\n"
        
        # Check if adding this would exceed max length
        if current_length + len(formatted) > max_length:
            # Try to add a shortened version
            space_left = max_length - current_length
            if space_left > 50:  # Only add if we have reasonable space
                shortened = formatted[:space_left] + "...\n\n"
                context_parts.append(shortened)
                current_length += len(shortened)
            break
        
        context_parts.append(formatted)
        current_length += len(formatted)
    
    # If we only have the header, return empty
    if current_length <= len(header) + 10:  # +10 for minimal content
        logger.warning("format_context: No substantial content added, returning empty")
        return ""
    
    context_text = ''.join(context_parts)
    logger.info(f"format_context: Created context of {len(context_text)} characters")
    
    # Debug: Log first 200 chars of context
    if context_text:
        logger.debug(f"Context preview: {context_text[:200]}...")
    
    return context_text


def extract_key_query_terms(query: str) -> List[str]:
    """Extract key terms from query for better search"""
    query_lower = query.lower()
    
    # Library-specific terms mapping
    term_mapping = {
        'myloft': ['myloft', 'mobile app', 'app', 'e-resources app'],
        'past exam': ['past exam', 'exam papers', 'previous papers'],
        'borrowing': ['borrowing', 'loan', 'checkout', 'circulation'],
        'library hours': ['library hours', 'opening hours', 'closing time'],
        'plagiarism': ['plagiarism', 'turnitin', 'academic integrity'],
        'citation': ['citation', 'apa', 'referencing', 'bibliography']
    }
    
    keywords = []
    
    # Add query terms (skip very short words)
    for word in query_lower.split():
        if len(word) > 3:
            keywords.append(word)
    
    # Add mapped terms
    for key, terms in term_mapping.items():
        if key in query_lower:
            keywords.extend(terms)
    
    # Remove duplicates and return
    return list(set(keywords))


# Simple test function
def test_vector_store():
    """Test the vector store functionality"""
    print("🧪 Testing Vector Store")
    print("=" * 50)
    
    store = VectorStore()
    store.load()
    
    if store.loaded:
        print(f"✅ Vector store loaded with {len(store.chunks)} chunks")
        
        # Test search
        query = "What is MyLOFT?"
        results = store.search(query, k=3)
        
        if results:
            print(f"✅ Search for '{query}' found {len(results)} results")
            for i, result in enumerate(results):
                print(f"  Result {i+1}: Score={result['score']:.4f}")
                print(f"    Preview: {result['content'][:80]}...")
                
                # Test format_context
                context = format_context([result])
                print(f"    Context length: {len(context)}")
        else:
            print(f"❌ No results found for '{query}'")
    else:
        print("❌ Vector store not loaded")
    
    print("=" * 50)
    print("Test complete!")


if __name__ == "__main__":
    test_vector_store()
