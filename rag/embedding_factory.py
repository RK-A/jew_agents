"""Simplified factory for creating LangChain embedding instances"""

import logging
from typing import Optional
from langchain_core.embeddings import Embeddings


logger = logging.getLogger(__name__)


def create_langchain_embeddings(
    provider: str,
    model: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs
) -> Embeddings:
    """Factory function to create LangChain embedding instances
    
    Supported providers:
    - openai: OpenAI embeddings (requires api_key)
    - gigachat: GigaChat embeddings (requires api_key)
    - local: Local API embeddings compatible with OpenAI API (requires base_url)
    
    Args:
        provider: Embedding provider ("openai", "gigachat", "local")
        model: Model name/identifier
        api_key: API key for provider (required for OpenAI, GigaChat)
        base_url: Base URL for local API or custom OpenAI endpoint
        **kwargs: Additional provider-specific parameters
        
    Returns:
        LangChain Embeddings instance
        
    Raises:
        ValueError: If provider is unknown or required parameters are missing
    """
    
    if provider == "openai":
        if not api_key:
            raise ValueError("OpenAI embeddings require api_key")
        
        logger.info(f"Creating OpenAI embeddings with model: {model}")
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError:
            raise ImportError(
                "OpenAI embeddings not available. Install: pip install langchain-openai"
            )
        
        return OpenAIEmbeddings(
            model=model,
            openai_api_key=api_key,
            **kwargs
        )
    
    elif provider == "gigachat":
        if not api_key:
            raise ValueError("GigaChat embeddings require api_key")
        
        logger.info(f"Creating GigaChat embeddings with model: {model}")
        from rag.gigachat_embeddings import GigaChatLangChainEmbeddings
        return GigaChatLangChainEmbeddings(
            api_key=api_key,
            model=model,
            **kwargs
        )
    
    elif provider == "local":
        if not base_url:
            raise ValueError("Local API embeddings require base_url (e.g., http://127.0.0.1:1234/v1)")
        
        logger.info(f"Creating Local API embeddings: {base_url}, model: {model}")
        from rag.local_api_embeddings import LocalAPIEmbeddings
        return LocalAPIEmbeddings(
            base_url=base_url,
            model=model,
            **kwargs
        )
    
    else:
        raise ValueError(
            f"Unknown embedding provider: {provider}. "
            f"Supported: openai, gigachat, local"
        )


def create_embeddings_from_config(config) -> Embeddings:
    """Create embeddings from Settings config object
    
    Args:
        config: Settings instance with embedding configuration
        
    Returns:
        LangChain Embeddings instance
    """
    # Get base_url from config if available
    base_url = getattr(config, 'embedding_base_url', None) or getattr(config, 'llm_base_url', None)
    
    return create_langchain_embeddings(
        provider=config.embedding_provider,
        model=config.embedding_model,
        api_key=config.embedding_api_key,
        base_url=base_url
    )

