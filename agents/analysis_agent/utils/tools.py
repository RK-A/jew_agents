"""Tools for analysis agent graph"""

import json
from typing import List, Dict, Any, Optional, cast
from collections import Counter
from database.models import CustomerPreference
from database.session import async_session_factory
from database.repositories import (
    CustomerPreferenceRepository,
    ConsultationRecordRepository
)

KEYWORDS_PATTERNS = {
    "patterns": ["style", "стиль", "budget", "бюджет", "material", "материал",
                 "preference", "предпочтение", "popular", "популярный", "trend", "тренд"],
    "consultations": ["consultation", "консультация", "advice", "совет", "recommend",
                      "рекомендация", "agent", "агент", "help", "помощь"],
    "forecast": ["forecast", "прогноз", "predict", "предсказать", "demand", "спрос",
                 "future", "будущее", "next", "следующий", "trend", "тренд"],
    "segments": ["segment", "сегмент", "customer", "клиент", "group", "группа",
                 "category", "категория", "tier", "уровень"],
    "report": ["report", "отчёт", "summary", "резюме", "analysis", "анализ",
               "complete", "полный", "comprehensive", "comprehensive", "overview", "обзор"],
}


async def fetch_customer_preferences() -> List[Dict[str, Any]]:
    """
    Загружает все предпочтения клиентов из БД

    Returns:
        List[Dict]: Список предпочтений клиентов
    """
    try:
        async with async_session_factory() as session:
            repo = CustomerPreferenceRepository(session)
            preferences: List[CustomerPreference] = await repo.get_all()
            return [
                {
                    "user_id": p.user_id,
                    "style_preference": p.style_preference,
                    "budget_min": cast(Optional[float], p.budget_min),
                    "budget_max": cast(Optional[float], p.budget_max),
                    "preferred_materials": p.preferred_materials or [],
                    "skin_tone": p.skin_tone,
                    "occasion_types": p.occasion_types or [],
                }
                for p in preferences
            ]
    except Exception as e:
        return []


async def fetch_consultation_records(limit: int = 500) -> List[Dict[str, Any]]:
    """
    Загружает записи консультаций из БД

    Args:
        limit: Максимум записей для загрузки (по умолчанию 500)

    Returns:
        List[Dict]: Список записей консультаций
    """
    try:
        async with async_session_factory() as session:
            repo = ConsultationRecordRepository(session)
            records = await repo.get_all(limit=limit)

            return [
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "agent_type": r.agent_type,
                    "message": r.message,
                    "response": r.response,
                    "recommendations": r.recommendations or [],
                    "created_at": r.created_at.isoformat() if r.created_at is not None else None,
                }
                for r in records
            ]
    except Exception as e:
        return []


def analyze_style_patterns(preferences: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Анализирует паттерны в предпочтениях стилей

    Args:
        preferences: Список предпочтений клиентов

    Returns:
        Dict: Словарь со статистикой стилей
    """
    styles = [p["style_preference"] for p in preferences
              if p.get("style_preference")]
    style_counts = Counter(styles)

    return {
        "top_styles": dict(style_counts.most_common(5)),
        "total_with_style": len(styles),
    }


def analyze_material_patterns(preferences: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Анализирует паттерны в предпочтениях материалов

    Args:
        preferences: Список предпочтений клиентов

    Returns:
        Dict: Словарь со статистикой материалов
    """
    all_materials = []
    for p in preferences:
        all_materials.extend(p.get("preferred_materials", []))

    material_counts = Counter(all_materials)

    return {
        "top_materials": dict(material_counts.most_common(5)),
        "total_material_mentions": len(all_materials),
    }


def analyze_budget_patterns(preferences: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Анализирует распределение бюджетов клиентов

    Args:
        preferences: Список предпочтений клиентов

    Returns:
        Dict: Статистика по бюджетам
    """
    budgets = [p["budget_max"] for p in preferences if p.get("budget_max")]

    if not budgets:
        return {
            "average_budget": 0,
            "budget_distribution": {
                "under_20k": 0,
                "20k_50k": 0,
                "50k_100k": 0,
                "over_100k": 0,
            },
            "total_with_budget": 0,
        }

    avg_budget = sum(budgets) / len(budgets)

    return {
        "average_budget": round(avg_budget, 2),
        "budget_distribution": {
            "under_20k": sum(1 for b in budgets if b < 20000),
            "20k_50k": sum(1 for b in budgets if 20000 <= b < 50000),
            "50k_100k": sum(1 for b in budgets if 50000 <= b < 100000),
            "over_100k": sum(1 for b in budgets if b >= 100000),
        },
        "total_with_budget": len(budgets),
    }


def analyze_occasion_patterns(preferences: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Анализирует, для каких случаев ищут украшения

    Args:
        preferences: Список предпочтений клиентов

    Returns:
        Dict: Статистика по случаям
    """
    all_occasions = []
    for p in preferences:
        all_occasions.extend(p.get("occasion_types", []))

    occasion_counts = Counter(all_occasions)

    return {
        "popular_occasions": dict(occasion_counts.most_common()),
        "total_occasion_mentions": len(all_occasions),
    }


def analyze_skin_tone_patterns(preferences: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Анализирует распределение типов кожи

    Args:
        preferences: Список предпочтений клиентов

    Returns:
        Dict: Распределение типов кожи
    """
    skin_tones = [p["skin_tone"] for p in preferences if p.get("skin_tone")]
    skin_tone_counts = Counter(skin_tones)

    return {
        "skin_tone_distribution": dict(skin_tone_counts),
        "total_with_skin_tone": len(skin_tones),
    }


def analyze_consultation_stats(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Анализирует статистику консультаций

    Args:
        records: Список консультаций

    Returns:
        Dict: Статистика консультаций
    """
    if not records:
        return {
            "total_consultations": 0,
            "agent_type_distribution": {},
            "average_recommendations_per_consultation": 0,
        }

    agent_types = [r["agent_type"] for r in records]
    agent_counts = Counter(agent_types)

    total_recommendations = sum(
        len(r.get("recommendations", [])) for r in records
    )

    avg_recommendations = (
        total_recommendations / len(records) if records else 0
    )

    return {
        "total_consultations": len(records),
        "agent_type_distribution": dict(agent_counts),
        "average_recommendations_per_consultation": round(avg_recommendations, 2),
    }


def forecast_demand(
    patterns: Dict[str, Any],
    occasions: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Прогнозирует спрос на категории товаров

    Формула: score = 50 + (количество случаев / 10)

    Args:
        patterns: Выявленные паттерны
        occasions: Анализ случаев использования

    Returns:
        Dict: Прогноз спроса по категориям
    """

    categories = [
        "rings", "necklaces", "bracelets", "earrings", "pendants"
    ]

    occasion_sum = sum(occasions.get("popular_occasions", {}).values()) or 1

    forecast = {}
    for category in categories:
        base_score = 50
        occasion_boost = (occasion_sum / 10)
        total_score = round(base_score + occasion_boost, 2)

        forecast[category] = {
            "demand_score": min(total_score, 100),
            "recommended_stock": "high" if total_score > 60 else "medium",
            "priority": "high" if total_score > 70 else "medium",
        }

    return forecast


def identify_customer_segments(
    preferences: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Сегментирует клиентов по разным критериям

    Args:
        preferences: Список предпочтений клиентов

    Returns:
        List[Dict]: Список сегментов с характеристиками
    """

    segments = []

    # Luxury segment (≥100k)
    luxury = [
        p for p in preferences
        if p.get("budget_max") and p["budget_max"] >= 100000
    ]

    if luxury:
        segments.append({
            "name": "Luxury Buyers",
            "size": len(luxury),
            "characteristics": {
                "avg_budget": round(
                    sum(p["budget_max"] for p in luxury) / len(luxury), 2
                ),
                "popular_styles": Counter(
                    p["style_preference"] for p in luxury
                    if p.get("style_preference")
                ).most_common(3),
            },
        })

    # Mid-range segment (20k-100k)
    mid_range = [
        p for p in preferences
        if p.get("budget_max") and 20000 <= p["budget_max"] < 100000
    ]

    if mid_range:
        segments.append({
            "name": "Mid-Range Buyers",
            "size": len(mid_range),
            "characteristics": {
                "avg_budget": round(
                    sum(p["budget_max"] for p in mid_range) / len(mid_range), 2
                ),
                "popular_styles": Counter(
                    p["style_preference"] for p in mid_range
                    if p.get("style_preference")
                ).most_common(3),
            },
        })

    # Budget segment (<20k)
    budget = [
        p for p in preferences
        if p.get("budget_max") and p["budget_max"] < 20000
    ]

    if budget:
        segments.append({
            "name": "Budget Conscious",
            "size": len(budget),
            "characteristics": {
                "avg_budget": round(
                    sum(p["budget_max"] for p in budget) / len(budget), 2
                ),
                "popular_styles": Counter(
                    p["style_preference"] for p in budget
                    if p.get("style_preference")
                ).most_common(3),
            },
        })

    return segments


def classify_rule_based(query: str) -> List[str]:
    """
    Простая классификация на основе ключевых слов.

    Args:
        query: Пользовательский запрос (на любом языке)

    Returns:
        List[str] с выбранными модулями
    """

    query_lower = query.lower()
    scores = {
        "patterns": 0,
        "consultations": 0,
        "forecast": 0,
        "segments": 0,
        "report": 0,
    }

    # Считаем совпадения
    for module, keywords in KEYWORDS_PATTERNS.items():
        for keyword in keywords:
            if keyword in query_lower:
                scores[module] += 1

    # Выбираем модули с положительным скором
    selected = [m for m, score in scores.items() if score > 0]

    # Если ничего не выбрано → берём паттерны (базовый модуль)
    if not selected:
        selected = ["patterns"]

    return selected


async def classify_with_llm(llm_provider, query: str) -> List[str]:
    """
    Используем LLM для умного выбора модулей.

    Более точно, чем правила, но медленнее.

    Args:
        query: Пользовательский запрос

    Returns:
        List[str] с выбранными модулями
    """
    if llm_provider is None:
        return classify_rule_based(query)

    prompt = f"""
You are a helpful assistant that analyzes customer requests for a jewelry analysis system.

Based on the user's request, determine which analysis modules are needed:

"patterns": Analysis of customer styles, budgets, materials, preferences

"consultations": Statistics about customer consultations and advice

"forecast": Demand forecast for jewelry categories

"segments": Customer segmentation by budget and preferences

"report": Comprehensive analytical report (requires all other modules)

USER REQUEST:
"{query}"

TASK:

Analyze the request carefully

Select ONLY necessary modules (not all)

Return JSON array with module names in lowercase

IMPORTANT RULES:

If user wants "report" or "full analysis" or "complete analysis" → include all modules: ["patterns", "consultations", "forecast", "segments", "report"]

If user mentions "forecast" → also add "patterns" (forecast depends on patterns)

If user mentions "segments" → also add "patterns" (segments depend on patterns)

If no specific request → default to ["patterns"]

Return ONLY JSON, no other text

RESPONSE FORMAT:
{{"modules": ["module1", "module2", ...]}}
"""

    try:
        response = await llm_provider.generate(
            prompt=prompt,
            temperature=0.2,
        )

        # Парсим JSON
        try:
            result = json.loads(response)
            modules = result.get("modules", ["patterns"])
        except json.JSONDecodeError:
            return classify_rule_based(query)

        # Валидируем
        valid_modules = [m for m in modules if m in KEYWORDS_PATTERNS]

        if not valid_modules:
            return classify_rule_based(query)

        return valid_modules

    except Exception as e:
        return classify_rule_based(query)
