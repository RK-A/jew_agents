"""Custom LangChain wrapper for local embedding API (LM Studio, etc.)"""

import logging
from typing import List
import httpx
from langchain_core.embeddings import Embeddings


logger = logging.getLogger(__name__)


class LocalAPIEmbeddings(Embeddings):
    """LangChain-compatible wrapper for local embedding API (OpenAI-compatible)
    
    Supports:
    - LM Studio (http://localhost:1234)
    - LocalAI
    - Text Generation WebUI with embeddings
    - Any OpenAI-compatible local API
    """
    
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:1234/v1",
        model: str = "text-embedding-snowflake-arctic-embed-m-v1.5",
        timeout: float = 60.0,
        **kwargs
    ):
        """Initialize local API embeddings
        
        Args:
            base_url: Base URL of local API (e.g., http://127.0.0.1:1234/v1)
            model: Model name loaded in local API
            timeout: Request timeout in seconds
            **kwargs: Additional parameters
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.embeddings_url = f"{self.base_url}/embeddings"
        
        logger.info(f"Initialized Local API embeddings: {self.base_url}, model: {model}")
    
    async def _embed_documents_async(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.embeddings_url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": self.model,
                        "input": texts,
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                
                # OpenAI-compatible format: {"data": [{"embedding": [...]}, ...]}
                embeddings = [item["embedding"] for item in data["data"]]
                
                logger.debug(f"Generated {len(embeddings)} embeddings via local API")
                return embeddings
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error from local API: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error to local API: {e}")
                # If we were connecting to localhost inside a Docker container, try host.docker.internal as a fallback.
                if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
                    fallback_base = self.base_url.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal")
                    fallback_url = f"{fallback_base}/embeddings" if not fallback_base.endswith('/embeddings') else fallback_base
                    logger.warning(f"Retrying embeddings request using fallback URL: {fallback_url}")
                    try:
                        response = await client.post(
                            fallback_url,
                            headers={"Content-Type": "application/json"},
                            json={"model": self.model, "input": texts},
                            timeout=self.timeout
                        )
                        response.raise_for_status()
                        data = response.json()
                        embeddings = [item["embedding"] for item in data["data"]]
                        logger.debug(f"Generated {len(embeddings)} embeddings via local API (fallback)")
                        return embeddings
                    except Exception as e2:
                        logger.error(f"Request error to local API using fallback: {e2}")
                        raise ConnectionError(
                            f"Failed to connect to local embedding API at {self.embeddings_url} and fallback {fallback_url}. "
                            f"Make sure the server is running and the model is loaded."
                        )
                raise ConnectionError(
                    f"Failed to connect to local embedding API at {self.embeddings_url}. "
                    f"Make sure the server is running and the model is loaded."
                )
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}", exc_info=True)
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


def test_local_api_connection(base_url: str = "http://127.0.0.1:1234/v1", model: str = None) -> dict:
    """Test connection to local embedding API
    
    Args:
        base_url: Base URL of local API
        model: Model name (optional)
        
    Returns:
        Dict with test results
    """
    import asyncio
    
    async def _test():
        try:
            embeddings = LocalAPIEmbeddings(base_url=base_url, model=model or "default")
            
            # Test with simple text
            test_text = "Hello, world!"
            embedding = await embeddings.aembed_query(test_text)
            
            return {
                "status": "success",
                "base_url": base_url,
                "model": model or "default",
                "embedding_dimension": len(embedding),
                "sample_embedding": embedding[:5],  # First 5 values
                "message": "Connection successful!"
            }
        except Exception as e:
            return {
                "status": "error",
                "base_url": base_url,
                "model": model,
                "error": str(e),
                "message": "Connection failed. Make sure local API is running."
            }
    
    return asyncio.run(_test())

