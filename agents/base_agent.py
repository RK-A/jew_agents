"""Base agent class for all AI agents in the system"""

import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime

from llm.base import LLMProvider
from database.session import async_session_factory
from database.repositories import ConsultationRecordRepository
from rag.qdrant_service import QdrantService


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all AI agents"""
    
    LANGUAGE_INSTRUCTIONS = {
        "en": "Respond in English.",
        "ru": "Отвечай на русском языке.",
        "auto": "Respond in the same language as the user's message."
    }
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        rag_service: Optional[QdrantService] = None,
        language: str = "auto",
        custom_system_prompt: Optional[str] = None
    ):
        """
        Initialize base agent
        
        Args:
            llm_provider: LLM provider for text generation
            rag_service: Optional RAG service for product search
            language: Communication language (en, ru, auto)
            custom_system_prompt: Optional custom system prompt override
        """
        self.llm = llm_provider
        self.rag = rag_service
        self.language = language
        self.custom_system_prompt = custom_system_prompt
        self.logger = logging.getLogger(self.__class__.__name__)
        self.agent_type = self.__class__.__name__.replace("Agent", "").lower()
    
    def get_system_prompt(self, default_prompt: str) -> str:
        """
        Get system prompt with language instruction
        
        Args:
            default_prompt: Default system prompt for this agent
        
        Returns:
            Complete system prompt with language instruction
        """
        if self.custom_system_prompt:
            base_prompt = self.custom_system_prompt
        else:
            base_prompt = default_prompt
        
        language_instruction = self.LANGUAGE_INSTRUCTIONS.get(self.language, self.LANGUAGE_INSTRUCTIONS["auto"])
        
        return f"{base_prompt}\n\nLanguage Instruction: {language_instruction}"
    
    @abstractmethod
    async def process(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Process agent task - must be implemented by subclasses
        
        Returns:
            Dict with processing results
        """
        pass
    
    async def log_interaction(
        self,
        user_id: str,
        agent_type: str,
        input_msg: str,
        output_msg: str,
        recommendations: Optional[list] = None,
        preference_updates: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store interaction record in PostgreSQL
        
        Args:
            user_id: User identifier
            agent_type: Type of agent (consultant, analysis, trend)
            input_msg: User input message
            output_msg: Agent response message
            recommendations: Optional list of recommended product IDs
            preference_updates: Optional dict of preference updates
        
        Returns:
            True if logged successfully
        """
        try:
            async with async_session_factory() as session:
                repo = ConsultationRecordRepository(session)
                
                record_data = {
                    "id": str(uuid.uuid4()),  # Generate unique ID
                    "user_id": user_id,
                    "agent_type": agent_type,
                    "message": input_msg,
                    "response": output_msg,
                    "recommendations": recommendations or [],
                    "preference_updates": preference_updates or {},
                    "created_at": datetime.utcnow()
                }
                
                await repo.create(record_data)
                await session.commit()
                
                self.logger.info(
                    f"Logged interaction for user {user_id}, agent: {agent_type}",
                    extra={
                        "user_id": user_id,
                        "agent_type": agent_type,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                return True
        
        except Exception as e:
            self.logger.error(
                f"Error logging interaction for user {user_id}: {e}",
                exc_info=True
            )
            return False
    
    async def _build_context_string(
        self,
        user_profile: Optional[Dict[str, Any]] = None,
        products: Optional[list] = None,
        additional_context: Optional[str] = None
    ) -> str:
        """
        Build formatted context string for LLM prompt
        
        Args:
            user_profile: User preferences and profile
            products: List of products
            additional_context: Any additional context text
        
        Returns:
            Formatted context string
        """
        context_parts = []
        
        if user_profile:
            context_parts.append("=== User Profile ===")
            if user_profile.get("style_preference"):
                context_parts.append(f"Style: {user_profile['style_preference']}")
            
            budget_min = user_profile.get("budget_min")
            budget_max = user_profile.get("budget_max")
            if budget_min or budget_max:
                context_parts.append(f"Budget: {budget_min or 0}₽ - {budget_max or 'unlimited'}₽")
            
            materials = user_profile.get("preferred_materials", [])
            if materials:
                context_parts.append(f"Preferred materials: {', '.join(materials)}")
            
            if user_profile.get("skin_tone"):
                context_parts.append(f"Skin tone: {user_profile['skin_tone']}")
            
            occasions = user_profile.get("occasion_types", [])
            if occasions:
                context_parts.append(f"Occasions: {', '.join(occasions)}")
            
            context_parts.append("")
        
        if products:
            context_parts.append("=== Available Products ===")
            for idx, product in enumerate(products[:10], 1):
                name = product.get("name", "Unknown")
                price = product.get("price", 0)
                material = product.get("material", "")
                category = product.get("category", "")
                context_parts.append(
                    f"{idx}. {name} - {price}₽ ({material}, {category})"
                )
            context_parts.append("")
        
        if additional_context:
            context_parts.append("=== Additional Context ===")
            context_parts.append(additional_context)
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _extract_product_ids(self, products: list) -> list:
        """Extract product IDs from product list"""
        return [
            str(p.get("product_id") or p.get("id"))
            for p in products
            if p.get("product_id") or p.get("id")
        ]

