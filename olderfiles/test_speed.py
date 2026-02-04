#!/usr/bin/env python3
"""
Test response times
"""
import time
import requests
import json

def test_ollama_speed():
    print("Testing Ollama response speed...")
    
    # Test 1: Simple prompt
    print("\n1. Simple prompt test:")
    start = time.time()
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi",
                "prompt": "Hello, how are you?",
                "stream": False,
                "options": {"num_predict": 50}
            },
            timeout=10
        )
        elapsed = time.time() - start
        if response.status_code == 200:
            print(f"   ✅ Response in {elapsed:.2f}s")
            print(f"   Response: {response.json()['response'][:50]}...")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Chat endpoint
    print("\n2. Chat endpoint test:")
    start = time.time()
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "phi",
                "messages": [{"role": "user", "content": "What is AI?"}],
                "stream": False,
                "options": {"num_predict": 100}
            },
            timeout=15
        )
        elapsed = time.time() - start
        if response.status_code == 200:
            print(f"   ✅ Response in {elapsed:.2f}s")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 3: Model loading time
    print("\n3. Model availability check:")
    start = time.time()
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        elapsed = time.time() - start
        print(f"   ✅ Model list in {elapsed:.2f}s")
        models = response.json().get('models', [])
        print(f"   Available models: {[m['model'] for m in models]}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def check_system():
    print("\n=== System Check ===")
    
    # CPU info
    import os
    cpu_count = os.cpu_count()
    print(f"CPU cores: {cpu_count}")
    
    # Memory info
    import psutil
    memory = psutil.virtual_memory()
    print(f"Memory: {memory.available / 1024 / 1024:.0f}MB available")
    
    # Disk speed
    print(f"Disk: {psutil.disk_usage('/').free / 1024 / 1024 / 1024:.1f}GB free")

if __name__ == "__main__":
    check_system()
    test_ollama_speed()
