import asyncio
from typing import Dict, Any

from .utils.state import make_initial_state
from .graph import create_analysis_graph


class AnalysisAgent:
    """
    Агент анализа для ювелирного магазина.
    """

    def __init__(
        self,
        llm_provider=None,
        language: str = "auto",
    ):
        """
        Инициализация агента.

        Args:
            llm_provider: LLM провайдер (OpenAI, Claude, etc.)
            language: Язык результатов (auto, en, ru)
        """
        self.llm_provider = llm_provider
        self.language = language

    async def run(self, query) -> Dict[str, Any]:
        """
        Выполняет анализ и возвращает структурированный результат.

        Args:
            query: Пользовательский запрос

        Returns:
            Dict с результатами анализа
        """
        try:
            graph = create_analysis_graph(
                llm_provider=self.llm_provider,
            )

            # Создаём начальное состояние
            initial_state = make_initial_state(
                data=query, language=self.language)

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
            "generated_at": state.get("generated_at"),
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
