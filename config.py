from pydantic_settings import BaseSettings
from typing import Literal, ClassVar, Optional


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # LLM Provider configuration
    llm_provider: Literal["openai", "gigachat"] = "openai"
    llm_model: str = "gpt-5-nano"
    llm_api_key: str
    llm_temperature: float = 0.7
    llm_base_url: Optional[str] = None
    
    # Database configuration
    postgres_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/jewelry"
    
    # Qdrant configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "jewelry_products"
    
    # Embeddings configuration
    embedding_provider: Literal["openai", "huggingface", "gigachat", "local"] = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_api_key: str = ""
    embedding_base_url: str = ""  # For local API: http://127.0.0.1:1234/v1
    
    # Embedding dimensions mapping
    EMBEDDING_DIMENSIONS: ClassVar[dict] = {
        # OpenAI
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
        # HuggingFace
        "intfloat/multilingual-e5-base": 768,
        "intfloat/multilingual-e5-small": 384,
        "intfloat/multilingual-e5-large": 1024,
        # GigaChat
        "gigachat-embeddings": 1024,
        # Local models (common ones)
        "text-embedding-snowflake-arctic-embed-m-v1.5": 768,
        "text-embedding-nomic-embed-text-v1.5": 768,
        "all-MiniLM-L6-v2": 384,
        "all-mpnet-base-v2": 768,
    }
    
    def get_embedding_dimension(self) -> int:
        """Get dimension for configured embedding model"""
        return self.EMBEDDING_DIMENSIONS.get(self.embedding_model, 1536)
    
    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Agent configuration
    agent_language: Literal["en", "ru", "auto"] = "ru"
    agent_custom_prompt_consultant: str = ""
    agent_custom_prompt_analysis: str = ""
    agent_custom_prompt_trend: str = ""
    
    # Data generation configuration
    auto_fill_data: bool = False
    default_products_count: int = 80
    default_users_count: int = 25
    default_consultations_count: int = 40
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

