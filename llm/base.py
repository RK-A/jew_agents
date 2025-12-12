from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate text response from LLM
        
        Args:
            prompt: User prompt or instruction
            context: Optional context information (user profile, products, etc.)
            temperature: Optional temperature override
        
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    async def generate_with_tools(
        self, 
        prompt: str, 
        tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate response with tool/function calling capability
        
        Args:
            prompt: User prompt or instruction
            tools: List of available tools/functions
            context: Optional context information
        
        Returns:
            Dict with response and tool calls
        """
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for text
        
        Args:
            text: Text to embed
        
        Returns:
            List of float embeddings
        """
        pass

