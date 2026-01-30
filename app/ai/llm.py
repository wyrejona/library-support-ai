import requests
import json
from typing import Optional

class OllamaClient:
    def __init__(self, model: str = "phi", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
    
    def generate_response(self, prompt: str, context: str = None) -> str:
        """Generate response using Ollama HTTP API"""
        
        # Build system prompt
        system_prompt = """You are a helpful assistant that answers questions based on provided documents.
        Always be accurate and cite sources when available.
        If the context doesn't contain relevant information, say so."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add context if provided
        if context:
            messages.append({
                "role": "system", 
                "content": f"Document context:\n{context}"
            })
        
        # Add user message
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 512,
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                return response.json()["message"]["content"]
            else:
                return f"Error: Ollama API returned status {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Make sure Ollama is running with 'ollama serve'"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def list_models(self):
        """List available Ollama models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
            return []
        except:
            return []
