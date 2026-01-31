#!/usr/bin/env python3
"""
Pre-load model to avoid cold starts
"""
import requests
import time

print("Pre-loading Ollama model...")

# Warm up the model with a simple request
try:
    start = time.time()
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "phi",
            "prompt": "ping",
            "stream": False,
            "options": {"num_predict": 10}
        },
        timeout=30
    )
    elapsed = time.time() - start
    
    if response.status_code == 200:
        print(f"✅ Model loaded in {elapsed:.2f}s")
        print(f"   First response: {response.json()['response']}")
    else:
        print(f"❌ Error: {response.status_code}")
        
except Exception as e:
    print(f"❌ Failed to pre-load: {e}")
    print("Make sure Ollama is running: ollama serve")
