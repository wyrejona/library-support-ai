#!/usr/bin/env python3
import requests
import json

endpoint = "http://41.89.240.119:8000/chat"
queries = [
    "How many books can part-time lecturers borrow?",
    "What are the library opening hours?",
    "How do I access past exam papers?"
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    response = requests.post(endpoint, json={"message": query, "conversation_id": "raw_test"})
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data.get('response', 'No response')[:300]}...")
        print(f"Found: {data.get('found', False)}")
        if data.get('sources'):
            print(f"Sources: {len(data['sources'])}")
            for src in data['sources'][:2]:
                print(f"  - {src.get('content', '')[:100]}...")
    else:
        print(f"Error: {response.status_code}")
