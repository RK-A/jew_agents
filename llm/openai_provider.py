from typing import Optional, Dict, Any, List
import httpx
import json

from llm.base import LLMProvider
from utils.logging import get_logger


logger = get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI API provider implementation"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        embedding_model: str = "text-embedding-3-small",
        timeout: float = 60.0,
        max_retries: int = 3,
        base_url: str = "https://api.openai.com/v1"
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.embedding_model = embedding_model
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_url = base_url
        
        headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers=headers
        )

    async def _post_with_fallback(self, path: str, payload: dict) -> httpx.Response:
        """Post payload to base_url + path; on connect failure, retry using host.docker.internal fallback once."""
        tried_fallback = False
        url = f"{self.base_url.rstrip('/')}{path}"
        for _ in range(2):
            try:
                response = await self.client.post(url, json=payload)
                response.raise_for_status()
                return response
            except httpx.RequestError as e:
                logger.error(f"Request error to OpenAI/Local API at {url}: {e}")
                if (not tried_fallback) and ("localhost" in self.base_url or "127.0.0.1" in self.base_url):
                    fallback_base = self.base_url.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal")
                    url = f"{fallback_base.rstrip('/')}{path}"
                    tried_fallback = True
                    logger.warning(f"Retrying request using fallback base URL: {fallback_base}")
                    continue
                raise
    
    async def generate(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate text response using OpenAI Chat API"""
        
        messages = []
        
        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
            messages.append({
                "role": "system",
                "content": f"Context information:\n{context_str}"
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature
        }
        
        for attempt in range(self.max_retries):
            try:
                response = await self._post_with_fallback("/chat/completions", payload)
                response.raise_for_status()
                data = response.json()
                
                # Debug logging
                logger.debug(f"API response keys: {list(data.keys())}")
                
                # Handle different response formats
                if "choices" in data and len(data["choices"]) > 0:
                    # Standard OpenAI format
                    result = data["choices"][0]["message"]["content"]
                elif "content" in data:
                    # Some local APIs return direct content
                    result = data["content"]
                elif "response" in data:
                    # Alternative format
                    result = data["response"]
                elif "message" in data:
                    # Another alternative
                    result = data["message"]
                else:
                    # Unknown format - log and raise error
                    logger.error(f"Unexpected API response format. Keys: {list(data.keys())}, Data: {data}")
                    raise ValueError(
                        f"Unexpected API response format. Expected 'choices' field but got: {list(data.keys())}"
                    )
                
                logger.info(f"OpenAI generate successful (attempt {attempt + 1})")
                return result
                
            except httpx.HTTPError as e:
                logger.error(f"OpenAI API error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                continue
            except KeyError as e:
                logger.error(f"Missing expected field in API response: {e}")
                logger.error(f"Response data: {data if 'data' in locals() else 'No data'}")
                if attempt == self.max_retries - 1:
                    raise ValueError(f"Invalid API response format: missing {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error in OpenAI generate: {e}")
                if attempt == self.max_retries - 1:
                    raise
                continue
    
    async def generate_with_tools(
        self, 
        prompt: str, 
        tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate response with tool calling using OpenAI function calling"""
        
        messages = []
        
        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
            messages.append({
                "role": "system",
                "content": f"Context information:\n{context_str}"
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "temperature": self.temperature
        }
        
        for attempt in range(self.max_retries):
            try:
                response = await self._post_with_fallback("/chat/completions", payload)
                response.raise_for_status()
                data = response.json()
                
                # Handle different response formats
                if "choices" in data and len(data["choices"]) > 0:
                    message = data["choices"][0]["message"]
                    result = {
                        "content": message.get("content", ""),
                        "tool_calls": message.get("tool_calls", [])
                    }
                else:
                    # Fallback for non-OpenAI compatible APIs
                    logger.warning("API does not support tool calls format, returning simple content")
                    content = data.get("content", data.get("response", data.get("message", "")))
                    result = {
                        "content": content,
                        "tool_calls": []
                    }
                
                logger.info(f"OpenAI generate_with_tools successful (attempt {attempt + 1})")
                return result
                
            except httpx.HTTPError as e:
                logger.error(f"OpenAI API error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                continue
            except KeyError as e:
                logger.error(f"Missing expected field in API response: {e}")
                logger.error(f"Response data: {data if 'data' in locals() else 'No data'}")
                if attempt == self.max_retries - 1:
                    # Return fallback result
                    return {"content": "Error: API format mismatch", "tool_calls": []}
                continue
            except Exception as e:
                logger.error(f"Unexpected error in OpenAI generate_with_tools: {e}")
                if attempt == self.max_retries - 1:
                    raise
                continue
    
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings using OpenAI embeddings API"""
        
        payload = {
            "model": self.embedding_model,
            "input": text
        }
        
        for attempt in range(self.max_retries):
            try:
                response = await self._post_with_fallback("/embeddings", payload)
                response.raise_for_status()
                data = response.json()
                
                embedding = data["data"][0]["embedding"]
                logger.debug(f"OpenAI embed successful (attempt {attempt + 1})")
                return embedding
                
            except httpx.HTTPError as e:
                logger.error(f"OpenAI API error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                continue
            except Exception as e:
                logger.error(f"Unexpected error in OpenAI embed: {e}")
                raise
    
    async def close(self) -> None:
        """Close HTTP client"""
        await self.client.aclose()

