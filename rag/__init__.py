"""RAG (Retrieval-Augmented Generation) system for jewelry products"""

from rag.embeddings import (
    EmbeddingProvider,
    OpenAIEmbeddingProvider,
    GigaChatEmbeddingProvider,
    HuggingFaceEmbeddingProvider,
    create_embedding_provider,
)
from rag.qdrant_service import QdrantService
from rag.retrieval import RAGRetriever


__all__ = [
    "EmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "GigaChatEmbeddingProvider",
    "HuggingFaceEmbeddingProvider",
    "create_embedding_provider",
    "QdrantService",
    "RAGRetriever",
]

