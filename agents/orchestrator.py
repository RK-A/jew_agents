"""Agent orchestrator for managing all AI agents in the system using LangGraph"""

import logging
import json
from typing import Dict, Any, Optional, List

from langgraph.graph import StateGraph, END

from agents.consultant import ConsultantAgent
from agents.analysis_agent import AnalysisAgent
from agents.trend_agent import TrendAgent
from agents.girlfriend.agent import GirlfriendAgent
from agents.taste.agent import TasteAgent
from agents.graph_states import OrchestratorState
from llm.base import LLMProvider
from rag.qdrant_service import QdrantService


logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrator for managing and coordinating all AI agents using LangGraph"""

    def __init__(
        self,
        llm_provider: LLMProvider,
        rag_service: Optional[QdrantService] = None,
        language: str = "auto",
        custom_prompts: Optional[Dict[str, str]] = None
    ):
        """
        Initialize agent orchestrator

        Args:
            llm_provider: LLM provider for all agents
            rag_service: Optional RAG service for product search
            language: Communication language for all agents (en, ru, auto)
            custom_prompts: Optional dict with custom prompts for each agent type
        """
        self.llm_provider = llm_provider
        self.rag_service = rag_service
        self.language = language
        self.custom_prompts = custom_prompts or {}

        # Initialize all agents with language and custom prompts
        self.consultant_agent = ConsultantAgent(
            llm_provider=llm_provider,
            rag_service=rag_service,
            language=language,
            custom_system_prompt=self.custom_prompts.get("consultant")
        )

        self.analysis_agent = AnalysisAgent(
            llm_provider=llm_provider,
            language=language
        )

        self.trend_agent = TrendAgent(
            llm_provider=llm_provider,
            rag_service=rag_service,  # Trend agent may update product scores
            language=language,
            custom_system_prompt=self.custom_prompts.get("trend")
        )

        self.girlfriend_agent = GirlfriendAgent(
            llm_provider=llm_provider,
            language=language,
            custom_system_prompt=self.custom_prompts.get("girlfriend")
        )

        self.taste_agent = TasteAgent(
            llm_provider=llm_provider,
            language=language,
            custom_system_prompt=self.custom_prompts.get("taste")
        )

        # Build orchestrator graph
        self.graph = self._build_graph()

        logger.info(
            f"Agent orchestrator initialized with all agents (language: {language})")

    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow for orchestrator"""
        workflow = StateGraph(OrchestratorState)

        # Add nodes
        workflow.add_node("route_task", self._route_task_node)
        workflow.add_node("run_consultant", self._run_consultant_node)
        workflow.add_node("run_analysis", self._run_analysis_node)
        workflow.add_node("run_trend", self._run_trend_node)
        workflow.add_node("run_girlfriend", self._run_girlfriend_node)
        workflow.add_node("run_taste", self._run_taste_node)
        workflow.add_node("finalize_result", self._finalize_result_node)

        # Define conditional routing
        workflow.set_entry_point("route_task")

        def should_run_consultant(state: OrchestratorState) -> str:
            if "girlfriend" in state.get("agents_to_run", []):
                return "run_girlfriend"
            if "taste" in state.get("agents_to_run", []):
                return "run_taste"
            if "analysis" in state.get("agents_to_run", []):
                return "run_analysis"
            if "trend" in state.get("agents_to_run", []):
                return "run_trend"
            if "consultation" in state.get("agents_to_run", []):
                return "run_consultant"
            return "run_girlfriend"

        workflow.add_conditional_edges(
            "route_task",
            should_run_consultant,
            {
                "run_girlfriend": "run_girlfriend",
                "run_taste": "run_taste",
                "run_consultant": "run_consultant",
                "run_analysis": "run_analysis",
                "run_trend": "run_trend",
            }
        )

        # girlfriend and taste are terminal single-agent flows
        workflow.add_edge("run_girlfriend", "finalize_result")
        workflow.add_edge("run_taste", "finalize_result")
        workflow.add_edge("run_consultant", "finalize_result")
        workflow.add_edge("run_analysis", "finalize_result")
        workflow.add_edge("run_trend", "finalize_result")
        workflow.add_edge("finalize_result", END)

        return workflow.compile()

    async def handle_user_orchestrator(
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
                "agent": "consultation",
                "result": result
            }

        except Exception as e:
            logger.error(f"Error in user consultation: {e}", exc_info=True)
            return {
                "status": "error",
                "agent": "consultation",
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

    async def run_girlfriend_answer(
        self,
        user_id: str,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        zodiac_sign: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run girlfriend answer via GirlfriendAgent

        Returns:
            Dict with results
        """
        try:
            logger.info("Running answer girlfriend")

            result = await self.girlfriend_agent.process(user_id, message, conversation_history, zodiac_sign)

            return {
                "status": "success",
                "agent": "girlfriend",
                "result": result
            }

        except Exception as e:
            logger.error(f"Error in girlfriend: {e}", exc_info=True)
            return {
                "status": "error",
                "agent": "girlfriend",
                "error": str(e)
            }

    async def run_taste_detection(
        self,
        user_id: str,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        current_question_index: Optional[int] = None,
        answers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Run taste detection via TasteAgent

        Args:
            user_id: User identifier
            message: User message
            conversation_history: Optional conversation history
            current_question_index: Current question index in the taste detection flow
            answers: Dictionary of answers so far

        Returns:
            Dict with taste detection results
        """
        try:
            logger.info(f"Running taste detection for user {user_id}")

            result = await self.taste_agent.process(
                user_id=user_id,
                message=message,
                conversation_history=conversation_history,
                current_question_index=current_question_index,
                answers=answers
            )

            return {
                "status": "success",
                "agent": "taste",
                "result": result
            }

        except Exception as e:
            logger.error(f"Error in taste detection: {e}", exc_info=True)
            return {
                "status": "error",
                "agent": "taste",
                "error": str(e)
            }

    async def _route_task_node(self, state: OrchestratorState) -> OrchestratorState:
        """Node: Route task to appropriate agents"""
        try:
            task_type = state["task_type"]
            agents_to_run = []

            if task_type == "consultation":
                agents_to_run = ["consultation"]
            elif task_type == "girlfriend":
                agents_to_run = ["girlfriend"]
            elif task_type == "taste":
                agents_to_run = ["taste"]
            elif task_type == "analysis":
                agents_to_run = ["analysis"]
            elif task_type == "trend":
                agents_to_run = ["trend"]

            state["agents_to_run"] = agents_to_run
            state["completed_agents"] = []
            state["step"] = "routed"
            state["status"] = "processing"
        except Exception as e:
            logger.error(f"Error routing task: {e}", exc_info=True)
            state["error"] = str(e)
            state["status"] = "error"
        return state

    async def _run_girlfriend_node(self, state: OrchestratorState) -> OrchestratorState:
        """Node: Run GirlfriendAgent"""
        try:
            result = await self.girlfriend_agent.process(
                user_id=state["user_id"] or "anonymous",
                message=state.get("message") or "",
                conversation_history=state.get("conversation_history"),
            )
            state["girlfriend_result"] = result
            state["completed_agents"] = state.get(
                "completed_agents", []) + ["girlfriend"]
            state["step"] = "girlfriend_completed"
        except Exception as e:
            logger.error(f"Error running girlfriend: {e}", exc_info=True)
            state["error"] = str(e)
        return state

    async def _run_consultant_node(self, state: OrchestratorState) -> OrchestratorState:
        """Node: Run ConsultantAgent"""
        try:
            result = await self.consultant_agent.process(
                user_id=state["user_id"],
                message=state["message"],
                conversation_history=state.get("conversation_history")
            )
            state["consultant_result"] = result
            state["completed_agents"] = state.get(
                "completed_agents", []) + ["consultation"]
            state["step"] = "consultant_completed"
        except Exception as e:
            logger.error(f"Error running consultant: {e}", exc_info=True)
            state["error"] = str(e)
        return state

    async def _run_analysis_node(self, state: OrchestratorState) -> OrchestratorState:
        """Node: Run AnalysisAgent"""
        try:
            result = await self.analysis_agent.process()
            state["analysis_result"] = result
            state["completed_agents"] = state.get(
                "completed_agents", []) + ["analysis"]
            state["step"] = "analysis_completed"
        except Exception as e:
            logger.error(f"Error running analysis: {e}", exc_info=True)
            state["error"] = str(e)
        return state

    async def _run_trend_node(self, state: OrchestratorState) -> OrchestratorState:
        """Node: Run TrendAgent"""
        try:
            result = await self.trend_agent.process(state.get("messages", ""))

            # Update product trend scores if available
            if result.get("status") == "success" and self.rag_service:
                trend_scores = result.get("trend_scores", {})
                if trend_scores:
                    await self._update_product_trend_scores(trend_scores)

            state["trend_result"] = result
            state["completed_agents"] = state.get(
                "completed_agents", []) + ["trend"]
            state["step"] = "trend_completed"
        except Exception as e:
            logger.error(f"Error running trend: {e}", exc_info=True)
            state["error"] = str(e)
        return state

    async def _run_taste_node(self, state: OrchestratorState) -> OrchestratorState:
        """Node: Run TasteAgent"""
        try:
            result = await self.taste_agent.process(
                user_id=state["user_id"] or "anonymous",
                message=state.get("message") or "",
                conversation_history=state.get("conversation_history"),
                current_question_index=state.get("current_question_index"),
                answers=state.get("answers")
            )
            state["taste_result"] = result
            state["completed_agents"] = state.get(
                "completed_agents", []) + ["taste"]
            state["step"] = "taste_completed"
        except Exception as e:
            logger.error(f"Error running taste: {e}", exc_info=True)
            state["error"] = str(e)
        return state

    async def _finalize_result_node(self, state: OrchestratorState) -> OrchestratorState:
        """Node: Finalize and format results"""
        try:
            final_result = {}

            if state.get("girlfriend_result"):
                final_result["girlfriend"] = state["girlfriend_result"]

            if state.get("consultant_result"):
                final_result["consultation"] = state["consultant_result"]

            if state.get("taste_result"):
                final_result["taste"] = state["taste_result"]

            if state.get("analysis_result"):
                final_result["analysis"] = state["analysis_result"]

            if state.get("trend_result"):
                final_result["trend"] = state["trend_result"]

            state["final_result"] = final_result
            state["status"] = "success" if not state.get("error") else "error"
            state["step"] = "finalized"
        except Exception as e:
            logger.error(f"Error finalizing result: {e}", exc_info=True)
            state["error"] = str(e)
            state["status"] = "error"
        return state

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

            logger.info(
                f"Updating trend scores for {len(category_scores)} categories")

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
            "girlfriend_agent": {
                "name": "GirlfriendAgent",
                "status": "active",
                "has_rag": False
            },
            "taste_agent": {
                "name": "TasteAgent",
                "status": "active",
                "has_rag": False
            },
            "llm_provider": type(self.llm_provider).__name__,
            "rag_service_available": self.rag_service is not None
        }

    async def get_task_type(self, message, conversation_history) -> str:
        """
        Использует LLM для определения типа задачи по сообщению пользователя.
        """
        if self.llm_provider is None:
            return "girlfriend"
        context = ""
        if conversation_history:
            recent = conversation_history[-2:]
            for msg in recent:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                context += f"{role}: {content}\n"
        user_prompt = f"""Ты — интеллектуальный маршрутизатор для ИИ-ассистента ювелирного магазина.
        Твоя задача — проанализировать сообщение пользователя и историю диалога, чтобы выбрать наиболее подходящего агента.

        ДОСТУПНЫЕ АГЕНТЫ:
        1. "consultation": Вопросы о конкретных товарах, материалах (золото, серебро, пробы), характеристиках, весе, размерах, наличии, доставке или цене. Фактические вопросы.
        2. "girlfriend": Запросы совета по стилю ("подойдет ли мне?", "с чем носить?"), просьба высказать мнение, эмоциональное общение, поддержка выбора подарка, "подружка".
        3. "taste": Запросы на определение стиля пользователя, получение овета на вопрос, выявление предпочтений, диагностика вкуса.
        4. "trend": Анализ статей, модных журналов, вопросы о моде, трендах, что сейчас популярно, новинки сезона.
        5. "analysis": Запросы отчетов, статистики продаж, аналитика данных (административные запросы).

        ФОРМАТ ОТВЕТА:
        Верни ТОЛЬКО валидный JSON объект без markdown форматирования:
        {{
            "task_type": "consultation" | "girlfriend" | "taste" | "trend" | "analysis",
            "confidence": <число от 0.0 до 1.0>,
            "reasoning": "<краткое объяснение на русском>"
        }}

        ПРАВИЛА:
        - Если пользователь просто здоровается ("привет", "начать"), выбирай "taste" с низкой уверенностью (0.3).
        - Если пользователь отвечает на вопрос о вкусе, выбирай "taste".
        - Если запрос неясен, выбирай "girlfriend".
        - Если запрос смешанный, выбирай агента, который лучше подходит под *основную* цель вопроса.
        
        Контекст диалога:\n{context}\n\nСообщение пользователя: {message}
        """
        try:
            # Вызов LLM (используйте ваш метод генерации)
            response = await self.llm_provider.generate(
                prompt=user_prompt,
                temperature=0.2,
            )

            clean_response = response.replace("``````", "").strip()
            data = json.loads(clean_response)

            task_type = data.get("task_type", "girlfriend")
            confidence = data.get("confidence", 0.3)
            reasoning = data.get("reasoning", "")

            logger.info(
                f"Router decision: {task_type}) ({confidence:.2f}) -> {reasoning}")

            return task_type

        except Exception as e:
            logger.error(f"Routing error: {e}. Defaulting to 'girlfriend'.")
            return "girlfriend"

    async def handle_user_message(
        self,
        user_id: str,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        explicit_task_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Определяет task_type по сообщению и запускает граф.
        explicit_task_type позволяет принудительно выбрать агента.
        """
        try:
            if explicit_task_type:
                task_type = explicit_task_type
            else:
                task_type = await self.get_task_type(message, conversation_history)

            result = await self.handle_multi_agent_task(
                task_type=task_type,
                user_id=user_id,
                message=message,
                conversation_history=conversation_history
            )

            return result

        except Exception as e:
            logger.error(f"Error in handle_user_message: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "routed_task_type": None,
                "routing_confidence": 0.0
            }

    async def handle_multi_agent_task(
        self,
        task_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Handle tasks that may require multiple agents using LangGraph workflow

        Args:
            task_type: Type of task ("consultation" | "girlfriend" | "taste" | "trend" | "analysis")
            **kwargs: Task-specific parameters

        Returns:
            Dict with task results
        """
        try:
            # Initialize state
            initial_state: OrchestratorState = {
                "task_type": task_type,
                "user_id": kwargs.get("user_id"),
                "message": kwargs.get("message"),
                "content": kwargs.get("content"),
                "conversation_history": kwargs.get("conversation_history"),
                "consultant_result": None,
                "analysis_result": None,
                "trend_result": None,
                "taste_result": None,
                "girlfriend_result": None,
                "current_question_index": kwargs.get("current_question_index"),
                "answers": kwargs.get("answers"),
                "status": "pending",
                "final_result": {},
                "error": None,
                "agents_to_run": [],
                "completed_agents": [],
                "step": "start"
            }

            # Run graph
            final_state = await self.graph.ainvoke(initial_state)

            # Return result
            return {
                "status": final_state["status"],
                "task_type": final_state["task_type"],
                "result": final_state["final_result"],
                "error": final_state.get("error"),
                "completed_agents": final_state.get("completed_agents", [])
            }

        except Exception as e:
            logger.error(f"Error in multi-agent task: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
