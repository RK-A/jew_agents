"""State definition for LangGraph analysis agent"""

from datetime import datetime
from typing import List, Dict, Any, Optional, TypedDict, Literal


class AnalysisState(TypedDict):
    """Состояние для графа"""
    status: Literal["started", "running", "success", "no_data", "error"]
    error_message: Optional[str]

    data: str
    modules: list[str]
    raw_data: List[Dict[str, Any]]
    consultation_records: List[Dict[str, Any]]
    patterns: Dict[str, Any]
    consultation_stats: Dict[str, Any]
    demand_forecast: Dict[str, Any]
    customer_segments: List[Dict[str, Any]]
    report: Optional[str]

    total_customers: int
    generated_at: Optional[str]
    language: str


def make_initial_state(data="", language: str = "auto") -> AnalysisState:
    return {
        "language": language,
        "status": "started",
        "error_message": None,
        "data": data,
        "modules": [],
        "raw_data": [],
        "consultation_records": [],
        "patterns": {},
        "consultation_stats": {},
        "demand_forecast": {},
        "customer_segments": [],
        "report": None,
        "total_customers": 0,
        "generated_at": datetime.utcnow().isoformat(),
    }
