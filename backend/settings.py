from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # App Config
    APP_TITLE: str = "RFQ Deep Agent – Conversational Build"

    # Auth Configuration
    APP_USER: str = "admin"
    APP_PASSWORD: str = "admin"
    APP_ROLE: str = "Admin"
    APP_NAME: str = "Rahul"

    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Paths (Relative to project root)
    # Legacy paths removed (DATA_DIR, CHUNK_INDEX_FILE, EXPORT_DIR)


    
    # LLM Configuration
    LLM_PROVIDER: str
    LLM_API_KEY: str
    LLM_MODEL_NAME: str
    LLM_TEMPERATURE: float = 0.4

    # Conflict/Secondary LLM (Optional)
    CONFLICT_LLM_PROVIDER: str | None = None
    CONFLICT_LLM_API_KEY: str | None = None
    CONFLICT_LLM_MODEL: str | None = None
    CONFLICT_LLM_TEMPERATURE: float = 0.4
    
    # Embedding Configuration
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Retriever Configuration
    RETRIEVER_TOP_K: int = 5

    # Postgres Configuration
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5434"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "rahul5757"
    POSTGRES_DB: str = "documents_db"

    # API Configuration
    CORS_ORIGINS: List[str] = ["*"]
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
