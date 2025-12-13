"""Custom LangChain wrapper for GigaChat embeddings"""

import logging
from typing import List
import httpx
from langchain_core.embeddings import Embeddings


logger = logging.getLogger(__name__)


class GigaChatLangChainEmbeddings(Embeddings):
    """LangChain-compatible wrapper for GigaChat embeddings API"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "Embeddings",
        base_url: str = "https://gigachat.devices.sberbank.ru/api/v1"
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._access_token = None
        logger.info(f"Initialized GigaChat LangChain embeddings with model: {model}")
    
    async def _get_access_token(self) -> str:
        """Get OAuth access token for GigaChat API"""
        if self._access_token:
            return self._access_token
        
        async with httpx.AsyncClient(verify=False) as client:
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
    
    async def _embed_documents_async(self, texts: List[str]) -> List[List[float]]:
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
                logger.error(f"Error generating GigaChat embeddings: {e}", exc_info=True)
                raise
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Sync method - not recommended, use aembed_documents instead"""
        import asyncio
        return asyncio.run(self._embed_documents_async(texts))
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Async method for embedding multiple documents"""
        return await self._embed_documents_async(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """Sync method for embedding a query - not recommended"""
        import asyncio
        return asyncio.run(self.aembed_query(text))
    
    async def aembed_query(self, text: str) -> List[float]:
        """Async method for embedding a single query"""
        results = await self._embed_documents_async([text])
        return results[0] if results else []

