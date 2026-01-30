import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Model configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    ollama_model: str = "phi"
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout: int = 120
    
    # Vector store configuration
    faiss_index_path: str = "app/data/library_index.faiss"
    metadata_path: str = "app/data/metadata.pkl"
    
    # File paths
    pdfs_dir: str = "pdfs"
    max_upload_size: int = 50 * 1024 * 1024
    allowed_extensions: List[str] = [".pdf"]
    
    # Security
    secret_key: str = "your-secret-key-change-this-in-production-12345"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = "sqlite:///./app/data/library.db"
    
    # CORS configuration - ADD THIS
    allowed_origins: List[str] = ["*"]
    
    # Application settings
    max_context_chunks: int = 5
    chat_history_limit: int = 10
    query_log_retention_days: int = 90
    
    class Config:
        env_file = ".env"

settings = Settings()
