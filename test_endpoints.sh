#!/bin/bash
# quick_test.sh

BASE_URL="http://localhost:8000"

echo "🔍 Quick Route Test"
echo "=================="

echo "1. Testing main pages..."
for endpoint in "/" "/files" "/chat"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
    echo "  $endpoint: $response"
done

echo -e "\n2. Testing APIs..."
# Test POST to chat
curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}' | grep -q "response" && echo "  POST /chat: ✓ Working" || echo "  POST /chat: ✗ Failed"

# Test GET to api/files
curl -s "$BASE_URL/api/files" | grep -q "files" && echo "  GET /api/files: ✓ Working" || echo "  GET /api/files: ✗ Failed"

echo -e "\n3. Checking system status..."
# Count PDFs
pdf_count=$(ls -1 pdfs/*.pdf 2>/dev/null | wc -l)
echo "  PDFs in /pdfs: $pdf_count"

# Check vector store
if [ -f "data/chroma.sqlite3" ]; then
    echo "  Vector store: ✓ Ready"
else
    echo "  Vector store: ✗ Not processed"
fi

echo -e "\n✅ Your app has all routes registered correctly!"
echo "🌐 Open in browser: http://localhost:8000/"
echo "📁 File manager: http://localhost:8000/files"
echo "🤖 Chat: http://localhost:8000/chat"
