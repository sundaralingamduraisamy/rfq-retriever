from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    # App Config
    APP_TITLE: str
    APP_USER: str
    APP_PASSWORD: str
    APP_ROLE: str
    APP_NAME: str
    HOST: str
    PORT: int
    
    # LLM Configuration
    LLM_PROVIDER: str
    LLM_API_KEY: str
    LLM_MODEL_NAME: str
    LLM_TEMPERATURE: float
    HUGGINGFACE_TOKEN: Optional[str] = None

    # Conflict/Secondary LLM (Optional)
    CONFLICT_LLM_PROVIDER: Optional[str] = None
    CONFLICT_LLM_API_KEY: Optional[str] = None
    CONFLICT_LLM_MODEL: Optional[str] = None
    CONFLICT_LLM_TEMPERATURE: Optional[float] = None
    
    # Embedding Configuration
    EMBEDDING_MODEL_NAME: str
    
    # Image Model Configuration
    IMAGE_MODEL_NAME: str
    IMAGE_MODEL_FALLBACK: str
    
    # Retriever Configuration
    RETRIEVER_TOP_K: int

    # Postgres Configuration
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # API Configuration
    CORS_ORIGINS: List[str]
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
