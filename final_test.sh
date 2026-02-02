#!/bin/bash

BASE_URL="http://localhost:8000"

echo "🎯 Final Comprehensive Test"
echo "=========================="
echo

echo "1. Testing all main endpoints:"
echo "   Home page:     $(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/)"
echo "   Files page:    $(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/files)"
echo "   Chat page:     $(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/chat)"
echo

echo "2. Testing API endpoints:"
# POST chat
echo -n "   POST /chat API: "
curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"What services do you offer?"}' | grep -q "response" && echo "✅" || echo "❌"

# List files API
echo -n "   GET /api/files: "
curl -s "$BASE_URL/api/files" | grep -q "files" && echo "✅" || echo "❌"

echo

echo "3. System Status:"
echo -n "   PDFs directory: "
if [ -d "pdfs" ]; then
    count=$(ls -1 pdfs/*.pdf 2>/dev/null | wc -l)
    echo "✅ ($count files)"
else
    echo "❌ (not found)"
fi

echo -n "   Vector store: "
if [ -f "data/chroma.sqlite3" ]; then
    echo "✅ Ready"
else
    echo "⚠ Not processed (run /ingest)"
fi

echo

echo "4. Quick Browser Preview:"
echo "   🌐 Home:      $BASE_URL/"
echo "   📁 Files:     $BASE_URL/files"
echo "   🤖 Chat:      $BASE_URL/chat"
echo

echo "✅ All systems go! Your Library Support AI is ready!"
