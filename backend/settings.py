from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # App Config
    APP_TITLE: str = "RFQ Deep Agent – Conversational Build"
    
    # Paths (Relative to project root)
    DATA_DIR: str = "data"
    EXPORT_DIR: str = "exports"
    CHUNK_INDEX_FILE: str = "chunk_index.json"
    
    # LLM Configuration
    LLM_PROVIDER: str = "groq"
    LLM_API_KEY: str
    LLM_MODEL_NAME: str = "openai/gpt-oss-20b"
    LLM_TEMPERATURE: float = 0.4
    LLM_MAX_TOKENS: int = 1200

    # Conflict/Secondary LLM (Optional)
    CONFLICT_LLM_PROVIDER: str | None = None
    CONFLICT_LLM_API_KEY: str | None = None
    CONFLICT_LLM_MODEL: str | None = None
    CONFLICT_LLM_TEMPERATURE: float = 0.4
    
    # Embedding Configuration
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Retriever Configuration
    RETRIEVER_TOP_K: int = 5

    # API Configuration
    CORS_ORIGINS: List[str] = ["*"]
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
