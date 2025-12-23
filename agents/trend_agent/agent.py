from langgraph.graph import StateGraph, START, END
from .utils.state import TrendState
from .utils.nodes import (
    extraction_node, 
    analysis_node, 
    calculation_node, 
    reporting_node
)
# from utils.nodes import extraction_node, analysis_node, calculation_node, reporting_node
# from utils.state import TrendState
workflow = StateGraph(TrendState)

# Добавляем узлы
workflow.add_node("extract", extraction_node)
workflow.add_node("analyze", analysis_node)
workflow.add_node("calculate", calculation_node)
workflow.add_node("report", reporting_node)

# Связи (последовательные)
workflow.add_edge(START, "extract")
workflow.add_edge("extract", "analyze")
workflow.add_edge("analyze", "calculate")
workflow.add_edge("calculate", "report")
workflow.add_edge("report", END)

# Компиляция
graph = workflow.compile()
