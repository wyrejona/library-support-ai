import re
from typing import List

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Splits text into chunks of approximately `chunk_size` characters,
    respecting sentence boundaries where possible.
    
    Args:
        text: The full string text from the PDF.
        chunk_size: Target size of each chunk in characters.
        overlap: Number of characters to overlap between chunks to preserve context.
    
    Returns:
        List[str]: A list of text chunks.
    """
    if not text:
        return []

    # 1. Split text into "sentences" or logical units using regex.
    # We split by newlines or punctuation followed by space.
    # This keeps sentences intact better than arbitrary slicing.
    sentence_endings = r'(?<=[.?!])\s+|(?<=\n)\s+'
    sentences = re.split(sentence_endings, text)
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_len = len(sentence)
        
        # If adding this sentence exceeds chunk_size, store the current chunk
        if current_length + sentence_len > chunk_size and current_chunk:
            # Join the current list of sentences into one string
            chunk_str = "".join(current_chunk).strip()
            chunks.append(chunk_str)
            
            # Start new chunk with overlap
            # We keep the last few sentences that fit within 'overlap' size
            overlap_buffer = []
            overlap_len = 0
            for s in reversed(current_chunk):
                if overlap_len + len(s) <= overlap:
                    overlap_buffer.insert(0, s)
                    overlap_len += len(s)
                else:
                    break
            
            current_chunk = overlap_buffer
            current_length = overlap_len

        current_chunk.append(sentence)
        current_length += sentence_len

    # Add the last remaining chunk
    if current_chunk:
        chunks.append("".join(current_chunk).strip())

    return chunks

if __name__ == "__main__":
    # Quick test if you run this file directly
    sample_text = "This is sentence one. This is sentence two. " * 50
    result = chunk_text(sample_text, chunk_size=100, overlap=20)
    print(f"Created {len(result)} chunks.")
    print(f"First chunk: {result[0]}")
    print(f"Second chunk: {result[1]}")
