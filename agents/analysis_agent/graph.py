"""LangGraph analysis agent graph definition"""

from typing import List, Optional
from langgraph.graph import StateGraph, END
from .utils.state import AnalysisState
from .utils.nodes import (
    node_classify_modules,
    node_fetch_data,
    node_analyze_patterns,
    node_analyze_consultation_history,
    node_forecast_demand,
    node_identify_segments,
    node_generate_report,
)
from .routing import (
    route_after_fetch,
    route_to_next_module,
)


def create_analysis_graph(llm_provider=None, modules: Optional[List[str]] = None,):
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

    async def classify_modules_wrapper(state: AnalysisState):
        return await node_classify_modules(state, llm_provider)

    # Добавляем ноды
    workflow.add_node("classify_modules", classify_modules_wrapper)
    workflow.add_node("fetch_data", node_fetch_data)

    for node_name, node_func in MODULES.values():
        workflow.add_node(node_name, node_func)

    if llm_provider is not None:
        async def report_wrapper(state: AnalysisState):
            return await node_generate_report(state, llm_provider)
        workflow.add_node("generate_report", report_wrapper)
    else:
        async def dummy_report(state: AnalysisState):
            return state
        workflow.add_node("generate_report", dummy_report)

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
