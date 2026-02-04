#!/usr/bin/env python3
"""
Test script to verify procedure questions get complete answers
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_procedure_question(question):
    """Test a procedure question for completeness"""
    print(f"\n{'='*60}")
    print(f"Testing: {question}")
    print('='*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": question},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {response.status_code}")
            print(f"Success: {data.get('success', False)}")
            print(f"Complete: {data.get('answer_complete', 'N/A')}")
            print(f"Response length: {len(data.get('response', ''))} chars")
            print(f"\nResponse:\n{data.get('response', 'No response')}")
            print(f"\n{'='*60}")
            
            # Check for cutoff indicators
            response_text = data.get('response', '')
            cutoff_indicators = ['include:', 'steps:', 'process:', 'such as:', 'including:']
            
            for indicator in cutoff_indicators:
                if response_text.strip().endswith(indicator):
                    print(f"⚠️ WARNING: Response ends with '{indicator}' - may be incomplete!")
            
            if len(response_text) < 100 and 'how' in question.lower():
                print("⚠️ WARNING: Short response for 'how' question!")
            
            return data
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Exception: {e}")
    
    return None

def main():
    """Test various procedure questions"""
    test_questions = [
        "How do I access past exam papers?",
        "What are the steps to download the MyLOFT app?",
        "How do I renew my library books?",
        "What is the complete process for reporting a lost book?",
        "How do undergraduate students borrow books from the library?",
        "What are all the steps to login to MyLOFT?",
        "How can I access e-resources from the library?",
        "What is the complete procedure for joining the library?",
    ]
    
    print("🚀 Testing Procedure Question Completeness")
    print("Make sure the server is running on http://localhost:8000")
    
    results = []
    for question in test_questions:
        result = test_procedure_question(question)
        results.append({
            "question": question,
            "complete": result.get('answer_complete', False) if result else False,
            "length": len(result.get('response', '')) if result else 0
        })
    
    # Summary
    print("\n📊 SUMMARY OF PROCEDURE QUESTION TESTS:")
    print('='*60)
    
    complete_count = sum(1 for r in results if r['complete'])
    avg_length = sum(r['length'] for r in results) / len(results) if results else 0
    
    print(f"Total questions: {len(results)}")
    print(f"Complete answers: {complete_count}/{len(results)}")
    print(f"Average response length: {avg_length:.0f} characters")
    
    print("\n📋 Individual Results:")
    for r in results:
        status = "✅" if r['complete'] else "❌"
        print(f"{status} {r['question'][:50]}... ({r['length']} chars)")

if __name__ == "__main__":
    main()
