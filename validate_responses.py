#!/usr/bin/env python3
"""
Validate API responses against expected answers
"""
import json
import requests
import re
from typing import Dict, List, Tuple

API_ENDPOINT = "http://41.89.240.119:8000/chat"

def test_query(query: str, expected_keywords: List[str], conversation_id: str = None) -> Dict:
    """Test a single query and check for keywords"""
    payload = {
        "message": query,
        "conversation_id": conversation_id or f"val_{hash(query) % 1000}"
    }
    
    try:
        response = requests.post(API_ENDPOINT, json=payload, timeout=10)
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}", "found_keywords": []}
        
        data = response.json()
        
        # Extract response text
        response_text = data.get('response', '').lower()
        found = data.get('found', False)
        sources = data.get('sources', [])
        
        # Check for keywords
        found_keywords = []
        for keyword in expected_keywords:
            if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', response_text):
                found_keywords.append(keyword)
        
        # Calculate accuracy score
        keyword_accuracy = len(found_keywords) / len(expected_keywords) if expected_keywords else 0
        
        return {
            "query": query,
            "response_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text,
            "found": found,
            "sources_count": len(sources),
            "expected_keywords": expected_keywords,
            "found_keywords": found_keywords,
            "keyword_accuracy": round(keyword_accuracy * 100, 1),
            "response_length": len(response_text),
            "status": "success"
        }
        
    except Exception as e:
        return {"error": str(e), "found_keywords": []}

def run_validation():
    """Run full validation"""
    print("🔍 VALIDATING LIBRARY AI RESPONSES")
    print("=" * 70)
    
    # Load expected answers
    try:
        with open('expected_answers.json', 'r') as f:
            expected = json.load(f)['expected_responses']
    except:
        print("❌ Could not load expected_answers.json")
        return
    
    results = []
    total_accuracy = 0
    queries_tested = 0
    
    for key, info in expected.items():
        print(f"\n📝 Testing: {info['query']}")
        print(f"   Expected keywords: {', '.join(info['expected_keywords'])}")
        
        result = test_query(
            info['query'], 
            info['expected_keywords'],
            f"val_{key}"
        )
        
        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
            continue
        
        print(f"   Response preview: {result['response_preview']}")
        print(f"   Found: {result['found']}")
        print(f"   Sources: {result['sources_count']}")
        print(f"   Keywords found: {', '.join(result['found_keywords']) or 'None'}")
        print(f"   Keyword accuracy: {result['keyword_accuracy']}%")
        
        if result['keyword_accuracy'] >= 70:
            print(f"   ✅ GOOD: High accuracy")
        elif result['keyword_accuracy'] >= 40:
            print(f"   ⚠️  FAIR: Moderate accuracy")
        else:
            print(f"   ❌ POOR: Low accuracy")
        
        results.append(result)
        if result['keyword_accuracy'] > 0:
            total_accuracy += result['keyword_accuracy']
            queries_tested += 1
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 VALIDATION SUMMARY")
    print(f"{'='*70}")
    
    if queries_tested > 0:
        avg_accuracy = total_accuracy / queries_tested
        print(f"Queries tested: {len(results)}")
        print(f"Average keyword accuracy: {avg_accuracy:.1f}%")
        
        # Count by accuracy level
        good = sum(1 for r in results if r.get('keyword_accuracy', 0) >= 70)
        fair = sum(1 for r in results if 40 <= r.get('keyword_accuracy', 0) < 70)
        poor = sum(1 for r in results if r.get('keyword_accuracy', 0) < 40)
        
        print(f"\nAccuracy breakdown:")
        print(f"  ✅ GOOD (≥70%): {good} queries")
        print(f"  ⚠️  FAIR (40-69%): {fair} queries")
        print(f"  ❌ POOR (<40%): {poor} queries")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if avg_accuracy < 50:
            print("  • Re-ingest PDF with better chunking")
            print("  • Check if PDF text extraction is working")
            print("  • Verify vector store has correct embeddings")
        elif avg_accuracy < 70:
            print("  • Improve query understanding in vector search")
            print("  • Add query expansion for better matching")
            print("  • Check embedding model quality")
        else:
            print("  • System is working well!")
            print("  • Consider adding more test cases")
        
        # Save detailed results
        with open('validation_results.json', 'w') as f:
            json.dump({
                "summary": {
                    "total_queries": len(results),
                    "average_accuracy": avg_accuracy,
                    "good_count": good,
                    "fair_count": fair,
                    "poor_count": poor
                },
                "detailed_results": results
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: validation_results.json")
    else:
        print("❌ No queries could be tested successfully")

if __name__ == "__main__":
    run_validation()
