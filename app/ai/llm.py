import time
import random
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY

# Initialize the Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# Use the stable model string
LLM_MODEL = "gemini-2.0-flash-exp"

# SYSTEM PROMPT
SYSTEM_PROMPT = """
You are an expert academic library assistant.
Answer the user's question using ONLY the provided context.

GUIDELINES:
1. If the context contains specific examples (e.g., citation formats, referencing styles), YOU MUST INCLUDE THEM in your answer.
2. Use Markdown formatting to make the answer readable (e.g., use **bold** for rules and `code blocks` or > blockquotes for citation examples).
3. If the answer is not found in the context, strictly say: "I could not find this information in the library materials."
4. Do not hallucinate or make up citation rules not present in the text.
"""

def ask_llm(context: str, question: str, retries: int = 5) -> str:
    """
    Generates an answer using Gemini with automatic retry for rate limits AND server overload.
    """
    user_message = f"Context:\n{context}\n\nQuestion:\n{question}"
    
    # Exponential backoff loop
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=LLM_MODEL,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.2,
                    max_output_tokens=1500
                )
            )
            return response.text.strip()

        except Exception as e:
            error_str = str(e)
            
            # CHECK FOR BOTH RATE LIMITS (429) AND OVERLOAD (503)
            if ("429" in error_str or 
                "RESOURCE_EXHAUSTED" in error_str or 
                "503" in error_str or 
                "UNAVAILABLE" in error_str):
                
                # Wait longer for 503s to let the server recover
                wait_time = (2 ** attempt) + random.uniform(1, 4) 
                print(f"⚠️ Gemini busy (Error {error_str[:3]}...). Retrying in {wait_time:.2f}s...")
                time.sleep(wait_time)
            else:
                # If it's a real error (like 400 Bad Request), fail immediately
                print(f"❌ Gemini Error: {e}")
                return "I'm sorry, I encountered an error while processing your request."

    # If we run out of retries
    return "I'm sorry, the AI service is currently very busy. Please try again in a minute."
