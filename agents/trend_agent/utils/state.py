from typing import TypedDict, List, Dict, Any

class TrendState(TypedDict):
    """Состояние, которое передается между узлами графа"""
    content: str               # Входной текст
    extracted_keywords: Dict[str, Any]
    trends: Dict[str, Any]
    trend_scores: Dict[str, float]
    emerging_trends: List[str]
    recommendations: List[Dict[str, str]]
    report: str                # Финальный результат
