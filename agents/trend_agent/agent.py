from langgraph.graph import StateGraph, START, END
from .utils.state import TrendState
from .utils.nodes import (
    extraction_node, 
    calculation_node, 
)
import logging
from typing import Dict, Any, List

import json
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)




class TrendAgent(BaseAgent):
    """Agent for analyzing fashion trends from journals and articles using LangGraph"""
    
    DEFAULT_SYSTEM_PROMPT = """Ты эксперт-аналитик моды. Отвечай только в формате JSON."""
    
    
    def __init__(self, llm_provider, rag_service=None, language: str = "auto", custom_system_prompt: str = None):
        super().__init__(llm_provider, rag_service, language, custom_system_prompt)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow for trend analysis process"""
        workflow = StateGraph(TrendState)

        # Добавляем узлы
        workflow.add_node("extract", extraction_node)
        workflow.add_node("analyze", self._analysis_node)
        workflow.add_node("calculate", calculation_node)
        workflow.add_node("report", self._reporting_node)

        # Связи (последовательные)
        workflow.add_edge(START, "extract")
        workflow.add_edge("extract", "analyze")
        workflow.add_edge("analyze", "calculate")
        workflow.add_edge("calculate", "report")
        workflow.add_edge("report", END)
        
        return workflow.compile()
    
    async def process(self, content: str) -> Dict[str, Any]:
        """
        Process trend analysis from fashion journal content using LangGraph workflow
        
        Args:
            content: Fashion journal article or content text
        
        Returns:
            Dict with trends, keywords, and recommendations
        """
        try:
            self.logger.info(f"Starting trend analysis on {len(content)} characters of content...")
            
            # Initialize state
            initial_state: TrendState = {
                "content": content,
                "extracted_keywords": {},
                "trends": {},
                "trend_scores": {},
                "emerging_trends": [],
                "recommendations": [],
                "report": ""
            }
            
            # Run graph
            final_state = await self.graph.ainvoke(initial_state)
            
            # Return result
            if final_state.get("error"):
                return {
                    "status": "error",
                    "message": final_state["error"]
                }
            
            return {
                "status": "success",
                "extracted_keywords": final_state["extracted_keywords"],
                "trends": final_state["trends"],
                "trend_scores": final_state["trend_scores"],
                "emerging_trends": final_state["emerging_trends"],
                "recommendations": final_state["recommendations"],
                "report": final_state["report"],
                "content_length": len(content)
            }
        
        except Exception as e:
            self.logger.error(f"Error in trend analysis: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _analysis_node(self, state: TrendState):
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
        

        response = await self.llm.generate(
            prompt=prompt,
            context=self.DEFAULT_SYSTEM_PROMPT
        )
        # print(response)
        # 2. Улучшенная очистка JSON (как в оригинале + защита от markdown)
        txt = response
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

    async def _reporting_node(self, state: TrendState):
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
        
        response = await self.llm.generate(
            prompt=prompt
            )
        return {"report": response}