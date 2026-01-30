import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Model configuration
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # Local embedding model
    OLLAMA_MODEL: str = "llama2"  # or "mistral", "neural-chat", etc.
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Vector store configuration
    FAISS_INDEX_PATH: str = "app/data/library_index.faiss"
    METADATA_PATH: str = "app/data/metadata.pkl"
    
    # File paths
    PDFS_DIR: str = "pdfs"
    
    # CORS configuration
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"

settings = Settings()
