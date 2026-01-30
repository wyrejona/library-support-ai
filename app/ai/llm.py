import ollama
from typing import List, Dict, Any
from app.config import settings

class OllamaClient:
    def __init__(self):
        self.model = settings.OLLAMA_MODEL
        self.base_url = settings.OLLAMA_BASE_URL
    
    def generate_response(self, prompt: str, context: str = None, 
                         history: List[Dict[str, str]] = None) -> str:
        """Generate response using Ollama"""
        
        # Build system prompt with context
        system_prompt = """You are a helpful assistant that answers questions based on the provided context. 
        If the context doesn't contain relevant information, say so. 
        Always cite your sources in the format [Source: filename.pdf, Page: X]."""
        
        if context:
            system_prompt += f"\n\nContext from documents:\n{context}"
        
        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current user prompt
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': 0.3,
                    'num_predict': 512,
                }
            )
            return response['message']['content']
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def list_models(self) -> List[str]:
        """List available Ollama models"""
        try:
            models = ollama.list()
            return [model['model'] for model in models.get('models', [])]
        except:
            return []

# Global instance
ollama_client = OllamaClient()
