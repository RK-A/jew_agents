import re
from typing import Dict, List, Any

# JEWELRY_KEYWORDS = {
#     "styles": ["классический", "современный", "винтажный", "минимализм", "роскошный", "бохо", "ар-деко", "геометрический"],
#     "materials": ["золото", "серебро", "платина", "белое золото", "розовое золото", "титан", "сталь"],
#     "gemstones": ["бриллиант", "рубин", "сапфир", "изумруд", "жемчуг", "топаз", "аметист", "опал"],
#     "categories": ["кольца", "ожерелья", "браслеты", "серьги", "подвески", "броши", "анклеты"],
#     "colors": ["золотой", "серебряный", "розовый", "желтый", "белый", "черный", "синий", "красный", "зеленый"],
#     "descriptors": ["элегантный", "смелый", "нежный", "массивный", "многослойный", "лаконичный"]
# }
JEWELRY_KEYWORDS = {
    "styles": [
        "классич", "современ", "винтаж", "минимализм", "роскош", 
        "бохо", "ар-деко", "геометр"
    ],
    "materials": [
        "золот", "серебр", "платин", "бел", "розов", "титан", "стал"
    ],
    "gemstones": [
        "бриллиант", "рубин", "сапфир", "изумруд", "жемчуг", 
        "топаз", "аметист", "опал"
    ],
    "categories": [
        "кольц", "колец",    # Кольца
        "ожерел",            # Ожерелья
        "браслет",           # Браслеты
        "серьг", "сереж",    # Серьги
        "подвеск", "кулон",  # Подвески
        "брош",              # Броши
        "анклет"             # Анклеты
    ],
    "colors": [
        "золот", "серебр", "розов", "желт", "бел", "черн", 
        "син", "красн", "зелен"
    ],
    "descriptors": [
        "элегантн", "смел", "нежн", "массивн", "многослойн", "лаконичн"
    ]
}
# Полный словарь перевода корней в нормальные слова
KEYWORD_MAPPING = {
    # Стили
    "классич": "Классический",
    "современ": "Современный",
    "винтаж": "Винтажный",
    "минимализм": "Минимализм",
    "роскош": "Роскошный",
    "бохо": "Бохо",
    "ар-деко": "Ар-деко",
    "геометр": "Геометрический",
    
    # Материалы
    "золот": "Золото",
    "серебр": "Серебро",
    "платин": "Платина",
    "бел": "Белое золото", # Или просто "Белый металл"
    "розов": "Розовое золото",
    "титан": "Титан",
    "стал": "Сталь",
    
    # Камни
    "бриллиант": "Бриллиант",
    "рубин": "Рубин",
    "сапфир": "Сапфир",
    "изумруд": "Изумруд",
    "жемчуг": "Жемчуг",
    "топаз": "Топаз",
    "аметист": "Аметист",
    "опал": "Опал",
    
    # Категории (уже были)
    "кольц": "Кольца", "колец": "Кольца",
    "ожерел": "Ожерелья",
    "браслет": "Браслеты",
    "серьг": "Серьги", "сереж": "Серьги",
    "подвеск": "Подвески", "кулон": "Подвески",
    "брош": "Броши",
    "анклет": "Анклеты",
    
    # Цвета
    "желт": "Желтый",
    "черн": "Черный",
    "син": "Синий",
    "красн": "Красный",
    "зелен": "Зеленый",
    # золот, серебр, бел, розов уже есть выше (совпадают с материалами)
    
    # Описания
    "элегантн": "Элегантный",
    "смел": "Смелый",
    "нежн": "Нежный",
    "массивн": "Массивный",
    "многослойн": "Многослойный",
    "лаконичн": "Лаконичный"
}

def extract_keywords_tool(content: str) -> Dict[str, List[Dict[str, Any]]]:
    content_lower = content.lower()
    extracted = {}
    
    for category, keywords in JEWELRY_KEYWORDS.items():
        found = []
        for root_keyword in keywords:
            pattern = re.escape(root_keyword)
            matches = re.findall(pattern, content_lower)
            
            if matches:
                # ВОТ ТУТ МАГИЯ:
                # Превращаем корень "золот" в красивое "Золото" перед сохранением
                pretty_name = KEYWORD_MAPPING.get(root_keyword, root_keyword.capitalize())
                
                # Проверяем, не добавляли ли мы уже это красивое слово (для синонимов)
                # Например, "кольц" и "колец" оба дадут "Кольца". Надо сложить их.
                existing_item = next((item for item in found if item["keyword"] == pretty_name), None)
                
                if existing_item:
                    existing_item["count"] += len(matches)
                else:
                    found.append({"keyword": pretty_name, "count": len(matches)})
        
        if found:
            found.sort(key=lambda x: x["count"], reverse=True)
            extracted[category] = found
            
    return extracted


def calculate_metrics_tool(trends: Dict[str, Any], extracted_keywords: Dict[str, Any] = None) -> tuple:
    """
    Объединяет логику _calculate_trend_scores, _identify_emerging_trends 
    и _generate_recommendations из старого класса.
    """
    # 1. Scores (как в _calculate_trend_scores)
    scores = {}
    target_categories = [
        "Кольца", "Ожерелья", "Браслеты", "Серьги", 
        "Подвески", "Броши", "Анклеты"
    ]  
    trending_styles = trends.get("trending_styles", [])
    popular_materials = trends.get("popular_materials", [])
    
    category_counts = {}
    print(extracted_keywords)
    if extracted_keywords:
        for item in extracted_keywords.get("categories", []):
            category_counts[item["keyword"]] = item["count"]
    # 1. Считаем сумму упоминаний
    total_mentions = sum(category_counts.get(cat, 0) for cat in target_categories)
    
    # Защита от деления на ноль (если вообще ничего не нашли)
    if total_mentions == 0:
        # Всем даем заглушку, раз данных нет
        for cat in target_categories:
            scores[cat] = 0.1
    else:
        for category in target_categories:
            count = category_counts.get(category, 0)
            
            if count == 0:
                scores[category] = 0.0 # Честный ноль, если про них не говорили
            else:
                # 2. Считаем долю (Share of Voice)
                share = count / total_mentions 
                
                # Теперь у нас честное распределение. Сумма всех scores будет равна 1.0.
                # Пример: Кольца=0.2, Браслеты=0.5
                scores[category] = round(share, 2)

    # 2. Emerging Trends (как в _identify_emerging_trends)
    emerging = []
    for style in trending_styles[:3]:
        for material in popular_materials[:2]:
            emerging.append(f"{material} в стиле {style}")
    emerging = emerging[:5] # Limit

        # 3. Recommendations (Умная генерация)
    recommendations = []
    
    # А. Управление запасами (Закупки)
    # Если есть явные лидеры по стилям -> Закупаем
    if trending_styles:
        top_style = trending_styles[0]
        recommendations.append({
            "type": "закупки", 
            "priority": "высокий", 
            "action": f"Обеспечить наличие бестселлеров в стиле '{top_style}' во всех категориях."
        })
        
        # Если есть еще стили -> Расширяем ассортимент
        if len(trending_styles) > 1:
             recommendations.append({
                "type": "ассортимент", 
                "priority": "средний", 
                "action": f"Добавить тестовые партии для стилей: {', '.join(trending_styles[1:3])}."
            })

    # Б. Производство / Материалы
    if popular_materials:
        top_material = popular_materials[0]
        recommendations.append({
            "type": "производство", 
            "priority": "высокий", 
            "action": f"Фокус на коллекциях из материала '{top_material}'."
        })

    # В. Инновации (из Emerging)
    # Берем то, что мы нагенерили на шаге 2
    if emerging:
        recommendations.append({
            "type": "дизайн-инновации", 
            "priority": "низкий", # Рискованно, но интересно
            "action": f"Разработать капсульную коллекцию: {emerging[0]}." 
        })
        
    # Г. Маркетинг и PR
    designers = trends.get("mentioned_designers", [])
    if designers:
        # Если упомянуты бренды, можно использовать это в рекламе (аккуратно)
        recommendations.append({
            "type": "маркетинг",
            "priority": "средний",
            "action": f"В промо-материалах делать отсылки к эстетике бренда {designers[0]}."
        })
    
    # Д. Сезонность (если есть в JSON)
    forecast = trends.get("seasonal_forecast", "")
    if forecast and len(forecast) > 5:
         recommendations.append({
            "type": "стратегия",
            "priority": "высокий",
            "action": f"Учесть сезонный фактор: {forecast[:50]}..." 
        })

        
    return scores, emerging, recommendations