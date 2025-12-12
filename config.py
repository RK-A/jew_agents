from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # LLM Provider configuration
    llm_provider: Literal["openai", "gigachat"] = "openai"
    llm_model: str = "gpt-4"
    llm_api_key: str
    llm_temperature: float = 0.7
    
    # Database configuration
    postgres_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/jewelry"
    
    # Qdrant configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "jewelry_products"
    
    # Embeddings configuration
    embedding_model: str = "text-embedding-3-small"
    embedding_api_key: str
    
    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Data generation configuration
    auto_fill_data: bool = False
    default_products_count: int = 80
    default_users_count: int = 25
    default_consultations_count: int = 40
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

