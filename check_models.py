from google import genai
from app.config import GEMINI_API_KEY

def list_available_models():
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    print("🔍 Checking available models for your API key...")
    try:
        # List all models
        pager = client.models.list()
        
        found_any = False
        for model in pager:
            # Filter for models that support content generation
            if "generateContent" in model.supported_actions:
                print(f"✅ Available: {model.name}") # e.g. models/gemini-1.5-flash-001
                found_any = True
        
        if not found_any:
            print("❌ No models found that support generateContent.")
            
    except Exception as e:
        print(f"❌ Error listing models: {e}")

if __name__ == "__main__":
    list_available_models()
