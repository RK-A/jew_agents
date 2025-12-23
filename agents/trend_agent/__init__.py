import logging
from typing import Dict, Any, Optional
from .agent import graph  # Импорт графа

class TrendAgent:
    """
    Обертка (Adapter) для LangGraph версии TrendAgent.
    """
    def __init__(
        self, 
        llm_provider=None, 
        rag_service=None, 
        language="auto", 
        custom_system_prompt=None
    ):
        """
        Инициализация с заглушками для совместимости с Orchestrator.
        """
        self.logger = logging.getLogger(__name__)
        
        # Мы сохраняем RAG сервис, так как он может понадобиться в будущем,
        # хотя сейчас граф работает автономно.
        self.rag = rag_service 
        self.language = language
        
        # llm_provider и custom_system_prompt мы игнорируем,
        # так как настройки LLM и промпты жестко зашиты в nodes.py

    async def process(self, content: str) -> Dict[str, Any]:
        
        self.logger.info(f"Запуск TrendAgent для текста длиной {len(content)}")
        
        try:
            # 1. Запуск графа
            result = await graph.ainvoke({"content": content})
            
            # 2. Извлечение данных из результата графа
            raw_trends = result.get("trends", {})
            raw_keywords = result.get("extracted_keywords", {})
            full_report = result.get("report", "")
            
            # --- ПРЕОБРАЗОВАНИЕ ДАННЫХ (MAPPING) ---
            
            # 1. Превращаем словарь трендов в плоский список строк для фронта
            # Было: {"trending_styles": ["Минимализм"], "colors": ["Золото"]}
            # Станет: ["Стиль: Минимализм", "Цвет: Золото"]
            flattened_trends = []
            if isinstance(raw_trends, dict):
                for category, items in raw_trends.items():
                    if isinstance(items, list):
                        for item in items:
                            flattened_trends.append(f"{category}: {item}")
            elif isinstance(raw_trends, list):
                flattened_trends = raw_trends

            # 2. Превращаем ключевые слова в плоский список
            flattened_keywords = []
            if isinstance(raw_keywords, dict):
                 # Если структура { "styles": [{"keyword": "..."}] }
                for cat, kws in raw_keywords.items():
                    if isinstance(kws, list):
                        for k in kws:
                            if isinstance(k, dict) and "keyword" in k:
                                flattened_keywords.append(k["keyword"])
                            elif isinstance(k, str):
                                flattened_keywords.append(k)
            elif isinstance(raw_keywords, list):
                flattened_keywords = raw_keywords

            # 3. Формируем итоговый ответ строго по схеме TrendReportResponse
            response = {
                "status": "success",
                "agent": "trend_agent", # Важно для логов
                
                # Текст отчета кладем в insights
                "insights": full_report, 
                
                # Списки, которые мы сплющили
                "trends": flattened_trends,
                "keywords": flattened_keywords,
                
                # Остальное переносим как есть
                "trend_scores": result.get("trend_scores", {}),
                "recommendations": result.get("recommendations", []),
                
                # Поле mentioned_products можно заполнить из keywords, если нужно
                # "mentioned_products": flattened_keywords[:5] if flattened_keywords else []
            }
            
            return response

        except Exception as e:
            self.logger.error(f"Ошибка: {e}", exc_info=True)
            return {
                "status": "error",
                "agent": "trend_agent",
                "error": str(e),
                "insights": "Ошибка анализа."
            }
    
