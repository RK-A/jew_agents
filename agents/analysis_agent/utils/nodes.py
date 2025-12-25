"""Node functions for LangGraph analysis agent"""

from typing import Dict, Any
from .state import AnalysisState
from .tools import (
    fetch_customer_preferences,
    fetch_consultation_records,
    analyze_style_patterns,
    analyze_material_patterns,
    analyze_budget_patterns,
    analyze_occasion_patterns,
    analyze_skin_tone_patterns,
    analyze_consultation_stats,
    forecast_demand,
    identify_customer_segments,
)


async def node_fetch_data(state: AnalysisState) -> Dict[str, Any]:
    """
    Node 2: загрузка данных из БД
    """
    try:
        # Fetch preferences
        raw_data = await fetch_customer_preferences()

        if not raw_data:
            return {
                "raw_data": [],
                "consultation_stats": [],
                "status": "no_data",
                "error_message": "No customer data available",
            }

        # Fetch consultation records
        consultation_records = await fetch_consultation_records()
        return {
            "raw_data": raw_data,
            "consultation_records": consultation_records,
            "status": "running",
            "total_customers": len(raw_data),
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Data fetch failed: {str(e)}",
        }


async def node_analyze_patterns(state: AnalysisState) -> Dict[str, Any]:
    """
    Node 3: анализ паттернов
    """

    try:
        if not state["raw_data"]:
            return {
                "patterns": {},
            }

        styles = analyze_style_patterns(state["raw_data"])
        materials = analyze_material_patterns(state["raw_data"])
        budgets = analyze_budget_patterns(state["raw_data"])
        occasions = analyze_occasion_patterns(state["raw_data"])
        skin_tones = analyze_skin_tone_patterns(state["raw_data"])

        # Merge all patterns
        patterns = {
            "popular_styles": styles["top_styles"],
            "popular_materials": materials["top_materials"],
            "average_budget": budgets["average_budget"],
            "budget_distribution": budgets["budget_distribution"],
            "skin_tone_distribution": skin_tones["skin_tone_distribution"],
            "popular_occasions": occasions["popular_occasions"],
            "total_analyzed": len(state["raw_data"]),
        }

        return {
            "patterns": patterns,
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Pattern analysis failed: {str(e)}",
        }


async def node_analyze_consultation_history(state: AnalysisState) -> Dict[str, Any]:
    """
    Node 4: анализ консультаций
    """
    try:
        if not state["consultation_records"]:
            return {
                "consultation_stats": {
                    "total_consultations": 0,
                    "agent_type_distribution": {},
                    "average_recommendations_per_consultation": 0,
                },
            }

        stats = analyze_consultation_stats(state["consultation_records"])

        return {
            "consultation_stats": stats,
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Consultation analysis failed: {str(e)}",
        }


async def node_forecast_demand(state: AnalysisState) -> Dict[str, Any]:
    """
    Node 5: прогноз спроса
    """

    try:
        if not state["patterns"]:
            return {
                "demand_forecast": {},
            }

        occasions = {"popular_occasions": state["patterns"].get(
            "popular_occasions", {})}

        forecast = forecast_demand(state["patterns"], occasions)

        return {
            "demand_forecast": forecast,
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Demand forecast failed: {str(e)}",
        }


async def node_identify_segments(state: AnalysisState) -> Dict[str, Any]:
    """
    Node 6: сегментация клиентов
    """

    try:
        if not state["raw_data"]:
            return {
                "customer_segments": [],
            }

        segments = identify_customer_segments(state["raw_data"])

        return {
            "customer_segments": segments,
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Segmentation failed: {str(e)}",
        }
