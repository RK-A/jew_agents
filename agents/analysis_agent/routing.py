from .utils.state import AnalysisState


def route_after_fetch(state: AnalysisState) -> str:
    """После fetch определяем какой модуль первый"""
    modules = state.get("modules", ["patterns"])

    if "patterns" in modules:
        return "analyze_patterns"
    if "consultations" in modules:
        return "analyze_consultations"
    if "forecast" in modules:
        return "analyze_forecast"
    if "segments" in modules:
        return "analyze_segments"
    return "generate_report"


def route_to_next_module(current_module: str):
    """Фабрика функций маршрутизации между модулями"""

    def router(state: AnalysisState) -> str:
        modules = state.get("modules", [])

        # Порядок модулей
        order = ["patterns", "consultations", "forecast", "segments"]

        try:
            current_idx = order.index(current_module)

            # Ищем следующий модуль в списке
            for i in range(current_idx + 1, len(order)):
                if order[i] in modules:
                    return f"analyze_{order[i]}"

            # Если нет следующих → идём на отчёт
            return "generate_report"

        except ValueError:
            return "generate_report"

    return router
