import requests
import json
from typing import Optional

class OllamaClient:
    def __init__(self, model: str = "phi:latest", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
    
    def generate_response(self, prompt: str, context: str = None) -> str:
        """Generate response using Ollama HTTP API with RAG-specific instructions"""
        
        # Rigorous system prompt to prevent hallucinations
        system_prompt = (
            "You are a smart University of Embu Library Support AI. Your goal is to provide accurate "
            "information based ONLY on the provided document context. \n\n"
            "RULES:\n"
            "1. Do NOT list 'Sources' or 'References' at the end of your answer.\n"
            "2. If the answer is not in the context, say you don't know.\n"
            "3. Be precise and concise and move straight to the answer.\n"
            "4. Do not use outside knowledge.\n"
            "5. Do not repeat a sentence or a word."
            
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            messages.append({
                "role": "user", 
                "content": f"Use these library documents to answer my question:\n\n{context}\n\nQuestion: {prompt}"
            })
        else:
            messages.append({"role": "user", "content": prompt})
        
        try:
            # Increased timeout to 300s to handle the OptiPlex CPU load during inference
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,    # Lower temperature = more factual/less creative
                        "num_ctx": 4096,       # Standard context window
                        "num_predict": 512,    # Limit output length to save time
                        "top_p": 0.9,
                    },
                    "keep_alive": "5m"         # Keep model in RAM for 5 mins for faster follow-up
                },
                timeout=300 
            )
            
            if response.status_code == 200:
                return response.json()["message"]["content"]
            else:
                return f"Error: Ollama API returned status {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "Error: The request timed out. The system is working hard to process your documents—try a shorter question."
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Run 'ollama serve' in your terminal."
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
