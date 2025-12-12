"""Agent orchestrator for managing all AI agents in the system"""

import logging
from typing import Dict, Any, Optional, List

from agents.consultant_agent import ConsultantAgent
from agents.analysis_agent import AnalysisAgent
from agents.trend_agent import TrendAgent
from llm.base import LLMProvider
from rag.qdrant_service import QdrantService


logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrator for managing and coordinating all AI agents"""
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        rag_service: Optional[QdrantService] = None
    ):
        """
        Initialize agent orchestrator
        
        Args:
            llm_provider: LLM provider for all agents
            rag_service: Optional RAG service for product search
        """
        self.llm_provider = llm_provider
        self.rag_service = rag_service
        
        # Initialize all agents
        self.consultant_agent = ConsultantAgent(
            llm_provider=llm_provider,
            rag_service=rag_service
        )
        
        self.analysis_agent = AnalysisAgent(
            llm_provider=llm_provider,
            rag_service=None  # Analysis agent doesn't need RAG
        )
        
        self.trend_agent = TrendAgent(
            llm_provider=llm_provider,
            rag_service=rag_service  # Trend agent may update product scores
        )
        
        logger.info("Agent orchestrator initialized with all agents")
    
    async def handle_user_consultation(
        self,
        user_id: str,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Handle user consultation request via ConsultantAgent
        
        Args:
            user_id: User identifier
            message: User message/query
            conversation_history: Optional conversation history
        
        Returns:
            Dict with consultation results
        """
        try:
            logger.info(f"Handling consultation for user {user_id}")
            
            result = await self.consultant_agent.process(
                user_id=user_id,
                message=message,
                conversation_history=conversation_history
            )
            
            return {
                "status": "success",
                "agent": "consultant",
                "result": result
            }
        
        except Exception as e:
            logger.error(f"Error in user consultation: {e}", exc_info=True)
            return {
                "status": "error",
                "agent": "consultant",
                "error": str(e)
            }
    
    async def run_customer_analysis(self) -> Dict[str, Any]:
        """
        Run customer analysis via AnalysisAgent
        
        Returns:
            Dict with analysis results
        """
        try:
            logger.info("Running customer analysis")
            
            result = await self.analysis_agent.process()
            
            return {
                "status": "success",
                "agent": "analysis",
                "result": result
            }
        
        except Exception as e:
            logger.error(f"Error in customer analysis: {e}", exc_info=True)
            return {
                "status": "error",
                "agent": "analysis",
                "error": str(e)
            }
    
    async def run_trend_analysis(self, content: str) -> Dict[str, Any]:
        """
        Run trend analysis via TrendAgent
        
        Args:
            content: Fashion journal content to analyze
        
        Returns:
            Dict with trend analysis results
        """
        try:
            logger.info(f"Running trend analysis on {len(content)} characters")
            
            result = await self.trend_agent.process(content)
            
            # Update product trend scores if available
            if result.get("status") == "success" and self.rag_service:
                trend_scores = result.get("trend_scores", {})
                if trend_scores:
                    await self._update_product_trend_scores(trend_scores)
            
            return {
                "status": "success",
                "agent": "trend",
                "result": result
            }
        
        except Exception as e:
            logger.error(f"Error in trend analysis: {e}", exc_info=True)
            return {
                "status": "error",
                "agent": "trend",
                "error": str(e)
            }
    
    async def _update_product_trend_scores(
        self,
        category_scores: Dict[str, float]
    ) -> int:
        """
        Update trend scores in Qdrant based on category scores
        
        Args:
            category_scores: Dict mapping category to trend score
        
        Returns:
            Number of products updated
        """
        try:
            # This is a simplified implementation
            # In production, you'd query products by category and update individually
            
            logger.info(f"Updating trend scores for {len(category_scores)} categories")
            
            # For now, just log the scores
            # Actual implementation would query Qdrant and update products
            for category, score in category_scores.items():
                logger.info(f"Category {category} trend score: {score}")
            
            return len(category_scores)
        
        except Exception as e:
            logger.error(f"Error updating trend scores: {e}", exc_info=True)
            return 0
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status of all agents
        
        Returns:
            Dict with agent status information
        """
        return {
            "consultant_agent": {
                "name": "ConsultantAgent",
                "status": "active",
                "has_rag": self.consultant_agent.rag is not None
            },
            "analysis_agent": {
                "name": "AnalysisAgent",
                "status": "active",
                "has_rag": False
            },
            "trend_agent": {
                "name": "TrendAgent",
                "status": "active",
                "has_rag": self.trend_agent.rag is not None
            },
            "llm_provider": type(self.llm_provider).__name__,
            "rag_service_available": self.rag_service is not None
        }
    
    async def handle_multi_agent_task(
        self,
        task_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Handle tasks that may require multiple agents
        
        Args:
            task_type: Type of task (consultation, analysis, trend, hybrid)
            **kwargs: Task-specific parameters
        
        Returns:
            Dict with task results
        """
        try:
            if task_type == "consultation":
                return await self.handle_user_consultation(
                    user_id=kwargs.get("user_id"),
                    message=kwargs.get("message"),
                    conversation_history=kwargs.get("conversation_history")
                )
            
            elif task_type == "analysis":
                return await self.run_customer_analysis()
            
            elif task_type == "trend":
                return await self.run_trend_analysis(
                    content=kwargs.get("content", "")
                )
            
            elif task_type == "hybrid":
                # Run multiple agents for comprehensive analysis
                results = {}
                
                # Run trend analysis if content provided
                if kwargs.get("content"):
                    results["trend_analysis"] = await self.run_trend_analysis(
                        kwargs["content"]
                    )
                
                # Run customer analysis
                results["customer_analysis"] = await self.run_customer_analysis()
                
                return {
                    "status": "success",
                    "task_type": "hybrid",
                    "results": results
                }
            
            else:
                return {
                    "status": "error",
                    "error": f"Unknown task type: {task_type}"
                }
        
        except Exception as e:
            logger.error(f"Error in multi-agent task: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

