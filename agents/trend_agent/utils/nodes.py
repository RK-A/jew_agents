import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import TrendState
from .tools import extract_keywords_tool, calculate_metrics_tool


def extraction_node(state: TrendState):
    print("--- [1/4] Extracting Keywords ---")
    keywords = extract_keywords_tool(state["content"])
    return {"extracted_keywords": keywords}


def calculation_node(state: TrendState):
    print("--- [3/4] Calculating Metrics ---")
    scores, emerging, recs = calculate_metrics_tool(state["trends"], state["extracted_keywords"])
    return {
        "trend_scores": scores,
        "emerging_trends": emerging,
        "recommendations": recs
    }

