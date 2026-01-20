import numpy as np
import time
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY

# Initialize Client
client = genai.Client(api_key=GEMINI_API_KEY)

# Use the recommended model for 768-dimensional embeddings
EMBEDDING_MODEL = "text-embedding-004"

def embed_text(text: str) -> np.ndarray:
    """
    Generate a 768-dim embedding vector for the given text using Gemini.
    """
    if not text or not text.strip():
        # Handle empty chunks gracefully to avoid API errors
        return np.zeros(768, dtype=np.float32)

    try:
        # Call the embed_content endpoint
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=768
            )
        )

        # Access the raw values from the response object
        embedding_values = response.embeddings[0].values

        return np.array(embedding_values, dtype=np.float32)

    except Exception as e:
        print(f"Error embedding text: {e}")
        # Retry logic could go here, for now re-raise or return zeros
        raise e
