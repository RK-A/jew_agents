"""Factory for creating LangChain embedding instances"""

import logging
from typing import Optional
from langchain_core.embeddings import Embeddings


logger = logging.getLogger(__name__)


def _import_openai_embeddings():
    """Lazy import OpenAI embeddings"""
    try:
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings
    except ImportError:
        try:
            from langchain.embeddings import OpenAIEmbeddings
            return OpenAIEmbeddings
        except ImportError:
            raise ImportError(
                "OpenAI embeddings not available. Install with: pip install langchain-openai"
            )


def _import_huggingface_embeddings():
    """Lazy import HuggingFace embeddings"""
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings
    except ImportError:
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            return HuggingFaceEmbeddings
        except ImportError:
            raise ImportError(
                "HuggingFace embeddings not available. Install with: pip install langchain-huggingface sentence-transformers"
            )


def _import_local_api_embeddings():
    """Import local API embeddings (always available)"""
    from rag.local_api_embeddings import LocalAPIEmbeddings
    return LocalAPIEmbeddings


def create_langchain_embeddings(
    provider: str,
    model: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs
) -> Embeddings:
    """Factory function to create LangChain embedding instances
    
    Args:
        provider: Embedding provider ("openai", "huggingface", "gigachat", "local")
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
        OpenAIEmbeddings = _import_openai_embeddings()
        return OpenAIEmbeddings(
            model=model,
            openai_api_key=api_key,
            **kwargs
        )
    
    elif provider == "huggingface":
        logger.info(f"Creating HuggingFace embeddings with model: {model}")
        HuggingFaceEmbeddings = _import_huggingface_embeddings()
        return HuggingFaceEmbeddings(
            model_name=model,
            **kwargs
        )
    
    elif provider == "gigachat":
        if not api_key:
            raise ValueError("GigaChat embeddings require api_key")
        
        logger.info(f"Creating GigaChat embeddings with model: {model}")
        # GigaChat doesn't have official LangChain integration yet
        # Using custom wrapper
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
        LocalAPIEmbeddings = _import_local_api_embeddings()
        return LocalAPIEmbeddings(
            base_url=base_url,
            model=model,
            **kwargs
        )
    
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")


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

