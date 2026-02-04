#!/usr/bin/env python3
"""
SIMPLE & RELIABLE PDF INGESTION
"""
import os
import PyPDF2
import re
import json
import shutil
from typing import List, Dict, Any
import hashlib

def clean_text(text: str) -> str:
    """Clean text"""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(\w+)\n(\w+)', r'\1 \2', text)
    return text.strip()

def extract_pdf_chunks(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract text and create simple chunks"""
    filename = os.path.basename(pdf_path)
    chunks = []
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            
            # Process each page
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if not text:
                    continue
                    
                # Clean text
                text = clean_text(text)
                
                # Simple chunking: split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', text)
                
                current_chunk = []
                current_length = 0
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    if current_length + len(sentence) < 300:  # Target chunk size
                        current_chunk.append(sentence)
                        current_length += len(sentence)
                    else:
                        # Save current chunk
                        if current_chunk:
                            chunk_text = ' '.join(current_chunk)
                            chunk_id = hashlib.md5(f"{filename}_{page_num}_{len(chunks)}".encode()).hexdigest()[:12]
                            
                            chunks.append({
                                'content': chunk_text,
                                'source': filename,
                                'page': page_num,
                                'chunk_id': chunk_id,
                                'length': len(chunk_text),
                                'is_procedure': bool(re.search(r'\b(step|procedure|how to|instructions?)\b', chunk_text, re.I)),
                                'is_critical': bool(re.search(r'past exam|exam paper|critical|important', chunk_text, re.I))
                            })
                        
                        # Start new chunk
                        current_chunk = [sentence]
                        current_length = len(sentence)
                
                # Add last chunk from page
                if current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    chunk_id = hashlib.md5(f"{filename}_{page_num}_{len(chunks)}".encode()).hexdigest()[:12]
                    
                    chunks.append({
                        'content': chunk_text,
                        'source': filename,
                        'page': page_num,
                        'chunk_id': chunk_id,
                        'length': len(chunk_text),
                        'is_procedure': bool(re.search(r'\b(step|procedure|how to|instructions?)\b', chunk_text, re.I)),
                        'is_critical': bool(re.search(r'past exam|exam paper|critical|important', chunk_text, re.I))
                    })
        
        return chunks
        
    except Exception as e:
        print(f"Error extracting {filename}: {e}")
        return []

def main():
    print("=" * 60)
    print("📚 SIMPLE PDF INGESTION")
    print("=" * 60)
    
    # Clean up
    for dir_path in ["data", "vector_store"]:
        if os.path.exists(dir_path):
            print(f"🗑️  Cleaning {dir_path}/...")
            shutil.rmtree(dir_path)
        os.makedirs(dir_path, exist_ok=True)
    
    # Check PDFs
    pdfs_dir = "pdfs"
    if not os.path.exists(pdfs_dir):
        os.makedirs(pdfs_dir)
        print(f"\n📁 Created '{pdfs_dir}' directory.")
        print("📄 Place your PDF files here.")
        return
    
    pdf_files = [f for f in os.listdir(pdfs_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print("\n✗ No PDF files found.")
        return
    
    print(f"\n📄 Processing {len(pdf_files)} PDF(s)...")
    all_chunks = []
    
    for pdf_file in pdf_files:
        print(f"\n🔄 {pdf_file}")
        pdf_path = os.path.join(pdfs_dir, pdf_file)
        chunks = extract_pdf_chunks(pdf_path)
        print(f"  ✓ Extracted {len(chunks)} chunks")
        all_chunks.extend(chunks)
    
    if not all_chunks:
        print("\n✗ No content extracted.")
        return
    
    print(f"\n✅ EXTRACTION COMPLETE")
    print(f"   Total chunks: {len(all_chunks)}")
    
    # Save chunks
    with open("data/extracted_chunks.json", 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    print("💾 Saved chunks to: data/extracted_chunks.json")
    
    # Now create vector store with SMALL batches
    try:
        # Create a simple utils module inline
        import sys
        import io
        
        # Create simple vector store
        utils_code = '''
import os
import pickle
import numpy as np
import faiss
import requests
import time

class SimpleVectorStore:
    def __init__(self, model="nomic-embed-text:latest"):
        self.url = "http://localhost:11434/api/embeddings"
        self.model = model
        self.index = None
        self.metadata = []
    
    def create_index(self, texts, metadata, batch_size=5):
        """Create index with small batches"""
        print(f"🔧 Generating embeddings (batch size: {batch_size})...")
        
        embeddings = []
        successful = 0
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            print(f"  Batch {i//batch_size + 1}/{(len(texts)+batch_size-1)//batch_size}...")
            
            for j, text in enumerate(batch_texts):
                try:
                    resp = requests.post(
                        self.url,
                        json={"model": self.model, "prompt": text},
                        timeout=20
                    )
                    if resp.status_code == 200:
                        embeddings.append(resp.json()["embedding"])
                        successful += 1
                    else:
                        print(f"    ⚠️  Failed: HTTP {resp.status_code}")
                        embeddings.append([0]*768)
                except Exception as e:
                    print(f"    ⚠️  Error: {str(e)[:30]}")
                    embeddings.append([0]*768)
            
            # Small delay between batches
            if i + batch_size < len(texts):
                time.sleep(1)
        
        # Create index
        emb_array = np.array(embeddings).astype('float32')
        faiss.normalize_L2(emb_array)
        
        self.index = faiss.IndexFlatIP(emb_array.shape[1])
        self.index.add(emb_array)
        self.metadata = metadata
        
        # Save
        os.makedirs("vector_store", exist_ok=True)
        faiss.write_index(self.index, "vector_store/index.bin")
        with open("vector_store/metadata.pkl", 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"✅ Created index: {successful}/{len(texts)} successful")
    
    def load(self):
        """Load index"""
        try:
            self.index = faiss.read_index("vector_store/index.bin")
            with open("vector_store/metadata.pkl", 'rb') as f:
                self.metadata = pickle.load(f)
            return True
        except:
            return False
    
    def search(self, query, k=3):
        """Simple search"""
        if not self.load():
            return []
        
        try:
            resp = requests.post(
                self.url,
                json={"model": self.model, "prompt": query},
                timeout=10
            )
            if resp.status_code != 200:
                return []
            
            query_emb = np.array([resp.json()["embedding"]]).astype('float32')
            faiss.normalize_L2(query_emb)
            
            scores, indices = self.index.search(query_emb, k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1 and idx < len(self.metadata):
                    result = self.metadata[idx].copy()
                    result['score'] = float(score)
                    results.append(result)
            
            return results
        except:
            return []
'''
        
        # Execute the utils code
        exec(utils_code, globals())
        
        print(f"\n🤖 Creating vector index...")
        
        texts = [chunk['content'] for chunk in all_chunks]
        metadata = all_chunks
        
        # Use SMALL batch size
        vector_store = SimpleVectorStore()
        vector_store.create_index(texts, metadata, batch_size=3)  # Very small batches
        
        # Test
        print(f"\n🔍 Testing...")
        results = vector_store.search("library hours", k=2)
        if results:
            print(f"✓ Found {len(results)} results")
            for r in results:
                print(f"  - Score: {r.get('score', 0):.3f}")
                print(f"    {r['content'][:80]}...")
        else:
            print("✗ No results found")
        
        print(f"\n🎉 INGESTION COMPLETE!")
        
    except Exception as e:
        print(f"\n❌ Vector store error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
