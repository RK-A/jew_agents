import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
# from trend_agent.utils.state import TrendState
# from trend_agent.utils.tools import extract_keywords_tool, calculate_metrics_tool
import os
from .state import TrendState
from .tools import extract_keywords_tool, calculate_metrics_tool
base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1")
api_key = os.getenv("OPENAI_API_KEY", "lm-studio")


llm = ChatOpenAI(
    base_url=base_url,
    api_key=api_key,
    model="lmstudio-community/Qwen3-4B-Instruct-2507-GGUF",  # Имя для логов
    temperature=0.7,               # Qwen любит температуру чуть выше 0 для креатива
)
# Инициализация модели (API ключ подтянется из env)
# llm = ChatOpenAI(model="gpt-4o", temperature=0)

def extraction_node(state: TrendState):
    print("--- [1/4] Extracting Keywords ---")
    keywords = extract_keywords_tool(state["content"])
    return {"extracted_keywords": keywords}


def analysis_node(state: TrendState):
    print("--- [2/4] Analyzing Trends (LLM) ---")
    content = state["content"]
    keywords = state["extracted_keywords"]
    
    # 1. Используем ПОЛНЫЙ промпт из оригинального trend_agent.py
    prompt = f"""Проанализируй текст о моде и извлеки ювелирные тренды.
    
    Найденные ключевые слова:
    {json.dumps(keywords, indent=2, ensure_ascii=False)}
    
    Текст:
    {content[:2000]}...
    
    Определи:
    1. Топ-5 модных стилей
    2. Популярные материалы
    3. Трендовые цвета
    4. Упомянутые дизайнеры/бренды
    5. Сезонный прогноз
    
    Верни ТОЛЬКО JSON на русском языке:
    {{
        "trending_styles": ["стиль1", ...],
        "popular_materials": ["материал1", ...],
        "trending_colors": ["цвет1", ...],
        "mentioned_designers": ["имя", ...],
        "seasonal_forecast": "описание сезона"
    }}

    JSON:"""
    
    response = llm.invoke([
        SystemMessage(content="Ты эксперт-аналитик моды. Отвечай только в формате JSON."), 
        HumanMessage(content=prompt)
    ])
    
    # 2. Улучшенная очистка JSON (как в оригинале + защита от markdown)
    txt = response.content.strip()
    # Удаляем ```json и ```
    if txt.startswith("```json"):
        txt = txt.split("```json").split("```").strip()[1]
    elif txt.startswith("```"):
        txt = txt.split("```")[6].split("```")[0].strip()
        
    try:
        trends = json.loads(txt)
    except Exception as e:
        print(f"JSON Parsing Error: {e}. Using fallback logic.")
        # Fallback логика из оригинала: берем топы из ключевых слов
        trends = {
            "trending_styles": [kw["keyword"] for kw in keywords.get("styles", [])[:5]],
            "popular_materials": [kw["keyword"] for kw in keywords.get("materials", [])[:5]],
            "trending_colors": [kw["keyword"] for kw in keywords.get("colors", [])[:3]],
            "mentioned_designers": [],
            "seasonal_forecast": "Unable to determine from LLM error"
        }
        
    return {"trends": trends}


def calculation_node(state: TrendState):
    print("--- [3/4] Calculating Metrics ---")
    scores, emerging, recs = calculate_metrics_tool(state["trends"], state["extracted_keywords"])
    return {
        "trend_scores": scores,
        "emerging_trends": emerging,
        "recommendations": recs
    }

def reporting_node(state: TrendState):
    print("--- [4/4] Writing Report ---")
    
    # Контекст как в оригинале _generate_trend_report
    context = f"""
    === Извлеченные ключевые слова ===
    {json.dumps(state['extracted_keywords'], indent=2, ensure_ascii=False)}
    
    === Выявленные тренды ===
    {json.dumps(state['trends'], indent=2, ensure_ascii=False)}
    
    === Новые перспективные направления ===
    {json.dumps(state['emerging_trends'], indent=2, ensure_ascii=False)}
    
    === Рекомендации ===
    {json.dumps(state['recommendations'], indent=2, ensure_ascii=False)}
    """
    
    prompt = f"""Ты — старший аналитик моды, специализирующийся на ювелирных изделиях и аксессуарах.
    На основе проведенного анализа сформируй подробный профессиональный отчет о трендах:
    {context}
    
    Отрывок из реальной статьи:
    {state['content'][:1000]}...
    
    ТРЕБОВАНИЯ К ОТЧЕТУ (Markdown):
    
    # 1. Резюме
    Кратко (3-4 предложения): главная идея сезона, ключевой драйвер продаж.
    
    # 2. Анализ Трендов (Таблица)
    Создай Markdown-таблицу с колонками: "Направление", "Ключевые элементы", "Статус" (Растущий/Пиковый/Угасающий).
    Опиши Стили, Материалы и Цвета.
    
    # 3. Товарная Матрица (Категории)
    Какие категории украшений (Кольца, Серьги...) сейчас лидируют по упоминаемости? Дай интерпретацию цифрам из Share of Voice.
    
    # 4. Action Plan (Рекомендации)
    Преврати JSON-рекомендации в связный текст. Раздели на:
    * 📦 Закупки (Что покупать прямо сейчас)
    * 🎨 Дизайн (Что разрабатывать)
    * 📢 Маркетинг (О чем говорить с клиентом)
    
    # 5. Инсайты
    Если в данных есть имена дизайнеров или сезонный прогноз, обязательно упомяни их как аргументы для авторитетности.
    
    Стиль письма: Деловой, лаконичный, без воды. Используй жирный шрифт для акцентов.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"report": response.content}

