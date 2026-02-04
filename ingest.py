#!/usr/bin/env python3
"""
Optimized PDF ingestion script for Library Support AI.
"""
import os
import PyPDF2
import re
import shutil
import hashlib
import sys
import logging
import json
from pathlib import Path

# Ensure we can import app.config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.config import config
    from app.utils import VectorStore
    logger = logging.getLogger(__name__)
except ImportError as e:
    print(f"Error importing config/utils: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)

def clean_text(text: str) -> str:
    """Clean extracted text"""
    if not text:
        return ""
    
    # Basic cleaning
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'-\s+', '', text)  # Fix hyphenated words
    return text.strip()

def extract_sections(text: str) -> dict:
    """Extract sections from library document"""
    sections = {}
    current_section = "Introduction"
    current_content = []
    
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect section headers (case insensitive)
        if re.match(r'^SECTION\s+\d+:', line, re.IGNORECASE):
            # Save previous section
            if current_content:
                sections[current_section] = ' '.join(current_content)
            
            # Start new section
            current_section = line
            current_content = []
        else:
            current_content.append(line)
    
    # Save the last section
    if current_content:
        sections[current_section] = ' '.join(current_content)
    
    return sections

def create_chunks(text: str, source: str) -> list:
    """Create chunks from text"""
    chunks = []
    
    # Extract sections
    sections = extract_sections(text)
    
    for section_title, section_content in sections.items():
        if not section_content:
            continue
            
        # If section is short, keep as single chunk
        if len(section_content) <= config.chunk_size:
            chunk_id = hashlib.md5(f"{source}_{section_title}".encode()).hexdigest()[:8]
            chunks.append({
                'content': f"{section_title}\n\n{section_content}",
                'source': source,
                'section': section_title,
                'chunk_id': chunk_id
            })
        else:
            # Split long sections
            words = section_content.split()
            for i in range(0, len(words), config.chunk_size - config.chunk_overlap):
                chunk_words = words[i:i + config.chunk_size]
                if not chunk_words:
                    continue
                    
                chunk_text = ' '.join(chunk_words)
                chunk_id = hashlib.md5(f"{source}_{section_title}_{i}".encode()).hexdigest()[:8]
                
                chunks.append({
                    'content': f"{section_title}\n\n{chunk_text}",
                    'source': source,
                    'section': section_title,
                    'chunk_id': chunk_id
                })
    
    return chunks

def main():
    print("=" * 50)
    print("📚 Library AI Ingestion")
    print(f"⚡ Using embedding model: {config.embedding_model}")
    print(f"📁 PDFs directory: {config.pdfs_dir}")
    print(f"💾 Vector store: {config.vector_store_path}")
    print("=" * 50)

    # 1. Clean old data
    if config.vector_store_path.exists():
        print("🗑️  Cleaning old vector store...")
        shutil.rmtree(config.vector_store_path)
    config.vector_store_path.mkdir(parents=True, exist_ok=True)

    # 2. Check PDFs
    if not config.pdfs_dir.exists():
        print("❌ No 'pdfs' directory found.")
        return
        
    pdf_files = [f for f in os.listdir(config.pdfs_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print("❌ No PDFs found.")
        return

    all_chunks = []

    # 3. Process Files
    for filename in pdf_files:
        print(f"📄 Processing: {filename}")
        try:
            file_path = config.pdfs_dir / filename
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                full_text = ""
                
                for page_num, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        full_text += clean_text(page_text) + "\n\n"
                
                if not full_text.strip():
                    print(f"   ⚠️  No text extracted from {filename}")
                    continue
                
                chunks = create_chunks(full_text, filename)
                all_chunks.extend(chunks)
                print(f"   ✅ Created {len(chunks)} chunks")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")

    # 4. Create vector store
    if all_chunks:
        try:
            print(f"🤖 Creating embeddings for {len(all_chunks)} chunks...")
            
            # Initialize vector store
            vector_store = VectorStore()
            
            # Extract content for embedding
            chunk_contents = [c['content'] for c in all_chunks]
            
            # Create index
            vector_store.create_index(chunk_contents, all_chunks)
            
            print("🎉 Ingestion Complete!")
            print(f"   Total chunks: {len(all_chunks)}")
            print(f"   Embedding model used: {config.embedding_model}")
            
            # Count MyLOFT mentions
            myloft_count = sum(1 for c in all_chunks if 'myloft' in c['content'].lower())
            print(f"   MyLOFT mentions: {myloft_count} chunks")
            
            # Test the vector store
            print(f"\n🧪 Testing vector store...")
            test_results = vector_store.search("What is MyLOFT?", k=2)
            if test_results:
                print(f"   ✅ Test search found {len(test_results)} results")
                for i, result in enumerate(test_results):
                    print(f"     Result {i+1}: Score={result['score']:.4f}")
            else:
                print(f"   ⚠️  Test search found no results")
            
        except Exception as e:
            print(f"❌ Indexing Failed: {e}")
            print(f"💡 Install required packages:")
            print(f"   pip install langchain-ollama")
    else:
        print("❌ No chunks created. Check PDF extraction.")

if __name__ == "__main__":
    main()
