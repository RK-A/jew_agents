"""Embeddings service for generating text embeddings using various models"""

import logging
from abc import ABC, abstractmethod
from typing import List
import httpx
from openai import AsyncOpenAI


logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Return embedding dimension size"""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embeddings provider"""
    
    DIMENSION_MAP = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)
        self.dimension = self.DIMENSION_MAP.get(model, 1536)
        logger.info(f"Initialized OpenAI embeddings with model: {model}")
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {e}", exc_info=True)
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error generating OpenAI batch embeddings: {e}", exc_info=True)
            raise
    
    def get_dimension(self) -> int:
        return self.dimension


class GigaChatEmbeddingProvider(EmbeddingProvider):
    """GigaChat embeddings provider"""
    
    def __init__(self, api_key: str, model: str = "Embeddings"):
        self.api_key = api_key
        self.model = model
        self.dimension = 1024
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self._access_token = None
        logger.info(f"Initialized GigaChat embeddings with model: {model}")
    
    async def _get_access_token(self) -> str:
        """Get OAuth access token for GigaChat API"""
        if self._access_token:
            return self._access_token
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "RqUID": "request_id",
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                self._access_token = response.json()["access_token"]
                return self._access_token
            except Exception as e:
                logger.error(f"Error getting GigaChat access token: {e}", exc_info=True)
                raise
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        return (await self.embed_batch([text]))[0]
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        access_token = await self._get_access_token()
        
        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "input": texts,
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                return [item["embedding"] for item in data["data"]]
            except Exception as e:
                logger.error(f"Error generating GigaChat batch embeddings: {e}", exc_info=True)
                raise
    
    def get_dimension(self) -> int:
        return self.dimension


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """HuggingFace embeddings provider (for local models)"""
    
    def __init__(self, model_name: str = "intfloat/multilingual-e5-base"):
        self.model_name = model_name
        self.dimension = 768
        self._model = None
        self._tokenizer = None
        logger.info(f"Initialized HuggingFace embeddings with model: {model_name}")
    
    async def _load_model(self):
        """Lazy load the model and tokenizer"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded HuggingFace model: {self.model_name}")
            except ImportError:
                logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
                raise
            except Exception as e:
                logger.error(f"Error loading HuggingFace model: {e}", exc_info=True)
                raise
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        await self._load_model()
        try:
            embedding = self._model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating HuggingFace embedding: {e}", exc_info=True)
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        await self._load_model()
        try:
            embeddings = self._model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating HuggingFace batch embeddings: {e}", exc_info=True)
            raise
    
    def get_dimension(self) -> int:
        return self.dimension


def create_embedding_provider(
    model: str,
    api_key: str = None
) -> EmbeddingProvider:
    """Factory function to create appropriate embedding provider"""
    
    if model.startswith("text-embedding"):
        if not api_key:
            raise ValueError("OpenAI embeddings require api_key")
        return OpenAIEmbeddingProvider(api_key=api_key, model=model)
    
    elif model.lower() == "gigachat" or model == "Embeddings":
        if not api_key:
            raise ValueError("GigaChat embeddings require api_key")
        return GigaChatEmbeddingProvider(api_key=api_key, model=model)
    
    else:
        return HuggingFaceEmbeddingProvider(model_name=model)

