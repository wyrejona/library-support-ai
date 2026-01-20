import requests
import json
import time

# The URL where your FastAPI server will run
API_URL = "http://127.0.0.1:8000/ask"

def test_api():
    print("🚀 Testing Library RAG API...")
    
    # 1. Define the payload (matches app.schemas.Query)
    payload = {
        "query": "What is the policy on late fees?" 
    }
    
    start_time = time.time()
    
    try:
        # 2. Send POST request
        response = requests.post(API_URL, json=payload)
        
        # 3. Check status
        if response.status_code == 200:
            data = response.json()
            duration = time.time() - start_time
            
            print(f"\n✅ Success! ({duration:.2f}s)")
            print("-" * 40)
            print(f"QUESTION: {payload['query']}")
            print(f"ANSWER:   {data.get('answer')}")
            print("-" * 40)
            
        else:
            print(f"\n❌ Error {response.status_code}:")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Refused.")
        print("   Make sure the Uvicorn server is running!")
        print("   Run: uvicorn app.main:app --reload")

if __name__ == "__main__":
    test_api()
