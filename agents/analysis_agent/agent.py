import asyncio
from datetime import datetime
from typing import Dict, Any

from agents.base_agent import BaseAgent
from langgraph.graph import StateGraph, START, END

from .utils.state import AnalysisState
from agents.analysis_agent.utils.tools import (
    classify_rule_based,
    classify_with_llm
)

from .utils.nodes import (
    node_fetch_data,
    node_analyze_patterns,
    node_analyze_consultation_history,
    node_forecast_demand,
    node_identify_segments,
)

from .routing import (
    route_after_fetch,
    route_to_next_module,
)


class AnalysisAgent(BaseAgent):
    """
    Агент анализа для ювелирного магазина.
    """

    def __init__(self, llm_provider, rag_service=None, language: str = "auto", custom_system_prompt: str = None):
        super().__init__(llm_provider, rag_service, language, custom_system_prompt)
        self.graph = self._build_graph()

    def _build_graph(self):
        """
        Граф с условным роутером.
        """
        MODULE_ORDER = ["patterns", "consultations", "forecast", "segments"]

        MODULES = {
            "patterns": ("analyze_patterns", node_analyze_patterns),
            "consultations": ("analyze_consultations", node_analyze_consultation_history),
            "forecast": ("analyze_forecast", node_forecast_demand),
            "segments": ("analyze_segments", node_identify_segments),
        }
        workflow = StateGraph(AnalysisState)

        # Добавляем ноды
        workflow.add_node("classify_modules", self._node_classify_modules)
        workflow.add_node("fetch_data", node_fetch_data)

        for node_name, node_func in MODULES.values():
            workflow.add_node(node_name, node_func)

        workflow.add_node("generate_report", self._node_generate_report)
        workflow.set_entry_point("classify_modules")

        workflow.add_edge("classify_modules", "fetch_data")

        node_names: dict = {node: node for node, _ in MODULES.values()}
        node_names["generate_report"] = "generate_report"

        workflow.add_conditional_edges(
            "fetch_data",
            route_after_fetch,
            node_names
        )

        for i, module in enumerate(MODULE_ORDER):
            node_name = MODULES[module][0]

            # Определяем возможные следующие узлы
            # = все модули после текущего + report
            next_nodes = {}
            for next_module in MODULE_ORDER[i + 1:]:
                next_node = MODULES[next_module][0]
                next_nodes[next_node] = next_node

            next_nodes["generate_report"] = "generate_report"

            # Добавляем условный переход
            workflow.add_conditional_edges(
                node_name,
                route_to_next_module(module),
                next_nodes
            )

        workflow.add_edge("generate_report", END)

        return workflow.compile()

    async def run(self, query) -> Dict[str, Any]:
        """
        Выполняет анализ и возвращает структурированный результат.

        Args:
            query: Пользовательский запрос

        Returns:
            Dict с результатами анализа
        """
        try:
            graph = self._build_graph()

            # Создаём начальное состояние
            initial_state: AnalysisState = {
                "language": self.language,
                "status": "started",
                "error_message": None,
                "data": query,
                "modules": [],
                "raw_data": [],
                "consultation_records": [],
                "patterns": {},
                "consultation_stats": {},
                "demand_forecast": {},
                "customer_segments": [],
                "report": None,
                "total_customers": 0,
            }

            # Запускаем граф
            final_state = await asyncio.wait_for(
                graph.ainvoke(initial_state),
                timeout=600
            )

            # Форматируем результат
            result = self._format_output(final_state)

            return result

        except Exception as e:
            return {
                "status": "error",
                "total_customers": 0,
                "error": str(e),
            }

    async def process(self) -> Dict[str, Any]:
        """
        Process customer analysis using LangGraph workflow

        Returns:
            Dict with analysis results, trends, and recommendations
        """
        try:
            self.logger.info("Starting customer analysis...")

            # Initialize state
            initial_state: AnalysisState = {
                "consultation_records": [],
                "patterns": {},
                "consultation_stats": {},
                "demand_forecast": {},
                "customer_segments": [],
                "report": "",
                "step": "start",
                "language": self.language,
                "status": "started",
                "error_message": None,
                "data": "",
                "modules": [],
                "raw_data": [],
                "total_customers": 0,
            }

            # Run graph
            final_state = await self.graph.ainvoke(initial_state)

            # Return result
            if final_state.get("error"):
                return {
                    "status": "error",
                    "message": final_state["error"]
                }

            return {
                "status": "success",
                "report": final_state["report"],
                "patterns": final_state["patterns"],
                "consultation_stats": final_state["consultation_stats"],
                "demand_forecast": final_state["demand_forecast"],
                "customer_segments": final_state["customer_segments"],
                "total_customers": final_state['total_customers'],
            }

        except Exception as e:
            self.logger.error(
                f"Error in customer analysis: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }

    def _format_output(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Форматирует состояние графа в выходной результат.

        Args:
            state: Финальное состояние из графа
            modules: Список выбранных модулей

        Returns:
            Dict с результатами
        """
        result: Dict[str, Any] = {
            "status": state.get("status", "error"),
            "total_customers": state.get("total_customers", 0),
        }

        if state["modules"] is None:
            return result

        # Добавляем только запрошенные модули
        if "patterns" in state["modules"]:
            result["patterns"] = state.get("patterns", {})

        if "consultations" in state["modules"]:
            result["consultation_stats"] = state.get("consultation_stats", {})

        if "forecast" in state["modules"]:
            result["demand_forecast"] = state.get("demand_forecast", {})

        if "segments" in state["modules"]:
            result["customer_segments"] = state.get("customer_segments", [])

        result["report"] = state.get("report", "")

        # Добавляем ошибку если есть
        if state.get("error_message"):
            result["error"] = state["error_message"]

        return result

    async def _node_generate_report(self, state: AnalysisState) -> Dict[str, Any]:
        """
        Node 7: генерация отчета LLM
        """

        try:

            # Build report prompt
            prompt = f"""
    Вы являетесь рыночным аналитиком, специализирующимся на розничной торговле ювелирными изделиями. Проанализируйте приведенные ниже данные и составьте подробный бизнес-отчет.

    СТРУКТУРА КЛИЕНТОВ:
    - Популярные стили: {state["patterns"].get('popular_styles', {}) if state["patterns"] else None}
    - Популярные материалы: {state["patterns"].get('popular_materials', {}) if state["patterns"] else None}
    - Средний бюджет: ₽{state["patterns"].get('average_budget', 0) if state["patterns"] else ""}
    - Распределение бюджета: {state["patterns"].get('budget_distribution', {}) if state["patterns"] else None}
    - Популярные случаи: {state["patterns"].get('popular_occasions', {}) if state["patterns"] else None}
    СТАТИСТИКА КОНСУЛЬТАЦИЙ:
    - Общее количество консультаций: {state["consultation_stats"].get('total_consultations', 0) if state["consultation_stats"] else 0}
    - Распространение агентов: {state["consultation_stats"].get('agent_type_distribution', {}) if state["consultation_stats"] else None}
    - Средние рекомендации: {state["consultation_stats"].get('average_recommendations_per_consultation', 0) if state["consultation_stats"] else None}

    ПРОГНОЗ СПРОСА:
    {state["demand_forecast"]}

    ПОТРЕБИТЕЛЬСКИЕ СЕГМЕНТЫ:
    {state["customer_segments"]}

    ЗАДАЧА:
    Подготовьте всеобъемлющий отчет о бизнес-анализе, который включает в себя:
    1. Ключевые рыночные данные
    2. Практические рекомендации по:
    - Оптимизации запасов
    - Маркетинговым стратегиям
    - Разработке продукта
    - Ценовым стратегиям
    3. Наиболее эффективные сегменты клиентов
    4. Области рисков и возможности

    Оформите отчет понятным, профессиональным деловым языком.
    """

            # Generate report via LLM
            try:
                report = await self.llm.generate(
                    prompt=prompt,
                    temperature=0.3,
                )

                return {
                    "report": report,
                    "status": "success",
                }
            except Exception as e:
                return {
                    "report": "LLM report generation failed.",
                    "status": "error",
                    "error_message": f"Report generation warning: {str(e)}",
                }

        except Exception as e:
            return {
                "report": "Analysis completed. LLM report generation failed.",
                "status": "success",
                "error_message": f"Report generation warning: {str(e)}",
            }

    async def _node_classify_modules(
        self,
        state: AnalysisState
    ) -> Dict[str, Any]:
        """
        Node 1: классификация модулей
        """
        try:
            # Если modules уже есть в input → используем их
            if state.get("modules"):
                return {
                    "modules": state["modules"],
                    "status": "running"
                }

            prompt = f"""
            Вы - полезный помощник, который анализирует запросы клиентов на систему анализа ювелирных изделий.

На основе запроса пользователя определите, какие модули анализа необходимы:

"шаблоны": анализ стилей клиентов, бюджетов, материалов, предпочтений

"консультации": Статистика о консультациях и рекомендациях клиентов.

"прогноз": Прогноз спроса на ювелирные изделия различных категорий

"сегменты": Сегментация покупателей по бюджету и предпочтениям

"отчет": Подробный аналитический отчет (требуются все остальные модули)

ЗАПРОС ПОЛЬЗОВАТЕЛЯ:
"{state["data"]}"

задача:

Внимательно проанализируйте запрос

Выберите ТОЛЬКО необходимые модули (не все)

Верните массив JSON с именами модулей в нижнем регистре

ВАЖНЫЕ ПРАВИЛА:

Если пользователь хочет "отчет" или "полный анализ", или "завершенный анализ" → включить все модули: ["шаблоны", "консультации", "прогноз", "сегменты", "отчет"]

Если пользователь упоминает "прогноз" → также добавить "шаблоны" (прогноз зависит от шаблонов).

Если пользователь упоминает "сегменты" → также добавьте "шаблоны" (сегменты зависят от шаблонов)

Если нет конкретного запроса → по умолчанию используется ["шаблоны"]

Возвращает ТОЛЬКО JSON, никакого другого текста

ФОРМАТ ОТВЕТА:
{{"modules": ["module1", "module2", ...]}}
"""
            modules = await self.llm.generate(
                prompt=prompt
            )

            return {
                "modules": modules,
                "status": "running"
            }

        except Exception as e:
            return {
                "modules": ["patterns"],  # Fallback
                "status": "error",
                "error": str(e)
            }
