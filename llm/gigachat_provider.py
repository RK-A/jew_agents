from typing import Optional, Dict, Any, List
import httpx
import json
import time
import uuid

from llm.base import LLMProvider
from utils.logging import get_logger


logger = get_logger(__name__)


class GigaChatProvider(LLMProvider):
    """GigaChat API provider implementation"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "GigaChat",
        temperature: float = 0.7,
        timeout: float = 60.0,
        max_retries: int = 3,
        scope: str = "GIGACHAT_API_PERS"
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries
        self.scope = scope
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0
        
        self.client = httpx.AsyncClient(
            timeout=timeout,
            verify=False  # GigaChat may require SSL verification bypass
        )
    
    async def _get_access_token(self) -> str:
        """Get OAuth access token for GigaChat API"""
        
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        try:
            response = await self.client.post(
                "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
                headers={
                    "Authorization": f"Basic {self.api_key}",
                    "RqUID": str(uuid.uuid4()),
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={"scope": self.scope}
            )
            response.raise_for_status()
            data = response.json()
            
            self.access_token = data["access_token"]
            expires_in = data.get("expires_at", 1800000) / 1000  # Convert ms to seconds
            self.token_expires_at = time.time() + expires_in - 60  # 1 minute buffer
            
            logger.info("GigaChat access token obtained")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Failed to get GigaChat access token: {e}")
            raise
    
    async def generate(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate text response using GigaChat API"""
        
        token = await self._get_access_token()
        
        messages = []
        
        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
            messages.append({
                "role": "system",
                "content": f"Контекстная информация:\n{context_str}"
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
                response = await self.client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                result = data["choices"][0]["message"]["content"]
                logger.info(f"GigaChat generate successful (attempt {attempt + 1})")
                return result
                
            except httpx.HTTPError as e:
                logger.error(f"GigaChat API error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                token = await self._get_access_token()
                continue
            except Exception as e:
                logger.error(f"Unexpected error in GigaChat generate: {e}")
                raise
    
    async def generate_with_tools(
        self, 
        prompt: str, 
        tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate response with tool calling using GigaChat function calling"""
        
        token = await self._get_access_token()
        
        messages = []
        
        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
            messages.append({
                "role": "system",
                "content": f"Контекстная информация:\n{context_str}"
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": self.model,
            "messages": messages,
            "functions": tools,  # GigaChat uses "functions" instead of "tools"
            "temperature": self.temperature
        }
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                message = data["choices"][0]["message"]
                
                result = {
                    "content": message.get("content", ""),
                    "tool_calls": message.get("function_call", [])
                }
                
                logger.info(f"GigaChat generate_with_tools successful (attempt {attempt + 1})")
                return result
                
            except httpx.HTTPError as e:
                logger.error(f"GigaChat API error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                token = await self._get_access_token()
                continue
            except Exception as e:
                logger.error(f"Unexpected error in GigaChat generate_with_tools: {e}")
                raise
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings using GigaChat embeddings API
        Note: GigaChat embeddings API may differ from OpenAI's format
        """
        
        token = await self._get_access_token()
        
        payload = {
            "model": "Embeddings",  # GigaChat embeddings model
            "input": text
        }
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                embedding = data["data"][0]["embedding"]
                logger.debug(f"GigaChat embed successful (attempt {attempt + 1})")
                return embedding
                
            except httpx.HTTPError as e:
                logger.error(f"GigaChat API error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                token = await self._get_access_token()
                continue
            except Exception as e:
                logger.error(f"Unexpected error in GigaChat embed: {e}")
                raise
    
    async def close(self) -> None:
        """Close HTTP client"""
        await self.client.aclose()

