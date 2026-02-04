#!/bin/bash
echo "🩺 DIAGNOSING RESPONSE ACCURACY"
echo "=" * 70

# 1. Check vector store exists
echo "1. Checking vector store..."
if [ -f "vector_store/index.bin" ]; then
    echo "   ✅ Vector store exists ($(du -h vector_store/index.bin | cut -f1))"
else
    echo "   ❌ No vector store found"
fi

# 2. Check extracted chunks
echo "2. Checking extracted chunks..."
if [ -f "data/extracted_chunks.json" ]; then
    chunk_count=$(jq '. | length' data/extracted_chunks.json 2>/dev/null || echo "0")
    echo "   ✅ Extracted chunks: $chunk_count"
    
    # Check for specific content
    echo "   Searching for key terms..."
    for term in "part-time lecturer" "opening hour" "past exam" "plagiarism"; do
        count=$(jq -r --arg term "$term" '[.[] | select(.content | ascii_downcase | contains($term))] | length' data/extracted_chunks.json 2>/dev/null || echo "0")
        echo "     '$term': $count chunks"
    done
else
    echo "   ❌ No extracted chunks found"
fi

# 3. Test a simple query
echo "3. Testing simple query..."
response=$(curl -s -X POST http://41.89.240.119:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "conversation_id": "diagnostic"}')
  
found=$(echo "$response" | jq -r '.found // false' 2>/dev/null || echo "error")
echo "   API response 'found' flag: $found"

# 4. Check Ollama embedding model
echo "4. Checking embedding model..."
timeout 5 curl -s http://localhost:11434/api/tags > /dev/null && \
  echo "   ✅ Ollama is running" || \
  echo "   ⚠️  Ollama may not be running"

echo -e "\n💡 If accuracy is low:"
echo "   • Run: python ingest.py (to re-ingest)"
echo "   • Check: python check_extracted_content.py"
echo "   • Validate: python validate_responses.py"
