from typing import Literal

from llm.base import LLMProvider
from llm.openai_provider import OpenAIProvider
from llm.gigachat_provider import GigaChatProvider
from utils.logging import get_logger


logger = get_logger(__name__)


def create_llm_provider(
    provider: Literal["openai", "gigachat"],
    api_key: str,
    model: str,
    temperature: float = 0.7,
    embedding_model: str = "text-embedding-3-small",
    **kwargs
) -> LLMProvider:
    """
    Factory function to create LLM provider instance
    
    Args:
        provider: Provider type ("openai" or "gigachat")
        api_key: API key for the provider
        model: Model name to use
        temperature: Temperature for generation
        embedding_model: Embedding model name
        **kwargs: Additional provider-specific arguments
    
    Returns:
        LLMProvider instance
    
    Raises:
        ValueError: If provider is not supported
    """
    
    if provider == "openai":
        logger.info(f"Creating OpenAI provider with model: {model}")
        return OpenAIProvider(
            api_key=api_key,
            model=model,
            temperature=temperature,
            embedding_model=embedding_model,
            **kwargs
        )
    
    elif provider == "gigachat":
        logger.info(f"Creating GigaChat provider with model: {model}")
        return GigaChatProvider(
            api_key=api_key,
            model=model,
            temperature=temperature,
            **kwargs
        )
    
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: 'openai', 'gigachat'"
        )


def create_llm_provider_from_config(config) -> LLMProvider:
    """
    Create LLM provider from config object
    
    Args:
        config: Configuration object with llm settings
    
    Returns:
        LLMProvider instance
    """
    
    return create_llm_provider(
        provider=config.llm_provider,
        api_key=config.llm_api_key,
        model=config.llm_model,
        temperature=config.llm_temperature,
        embedding_model=config.embedding_model
    )

