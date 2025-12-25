import logging
from typing import Dict
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Jewelry preference questions
JEWELRY_QUESTIONS = [
    {
        "id": "favorite_metal",
        "text": "Какой металл ты предпочитаешь для украшений? (золото: жёлтое, белое, розовое; серебро; платина; медь)",
        "category": "material"
    },
    {
        "id": "jewelry_type",
        "text": "Какие типы украшений тебе нравятся? (кольца, серьги, браслеты, колье/цепочки, подвески, броши)",
        "category": "type"
    },
    {
        "id": "stone_preference",
        "text": "Какие камни ты любишь? (бриллианты, изумруды, рубины, сапфиры, жемчуг, натуральные самоцветы, кубический цирконий, без камней)",
        "category": "stones"
    },
    {
        "id": "style_preference",
        "text": "Какой стиль украшений тебе нравится? (классический, минимализм, винтаж, современный/авангард, этнический, романтический, спортивный)",
        "category": "style"
    },
    {
        "id": "occasions",
        "text": "Для каких случаев ты выбираешь украшения? (ежедневные, вечерние, свадебные, деловые встречи, праздники)",
        "category": "occasions"
    },
    {
        "id": "design_features",
        "text": "Какие дизайн-элементы привлекают тебя? (простые геометричные формы, ажурные/резные, объёмные 3D, с эмалью, инкрустированные)",
        "category": "design"
    },
    {
        "id": "brand_attitude",
        "text": "Как ты относишься к брендам в ювелирной индустрии? (знаменитые дорогие бренды, малоизвестные дизайнеры, ручная работа/handmade, неважна марка)",
        "category": "brand"
    },
    {
        "id": "symbolic_meaning",
        "text": "Важно ли для тебя символическое значение украшений? (да, очень важно; важно, но не главное; не очень важно; вообще неважно)",
        "category": "meaning"
    },
    {
        "id": "budget_range",
        "text": "Какой бюджет ты обычно выделяешь на украшения? (до 5k, 5-15k, 15-50k, 50-100k, 100k+)",
        "category": "budget"
    },
    {
        "id": "statement_vs_subtle",
        "text": "Предпочитаешь ли ты яркие, заметные украшения или деликатные, утончённые? (яркие/заметные, смешанный стиль, деликатные/утончённые)",
        "category": "presence"
    },
]


@tool
def get_next_jewelry_question(current_index: int) -> Dict[str, str]:
    """Получить следующий вопрос для определения вкуса в ювелирных изделиях.

    Args:
        current_index: Индекс текущего вопроса (начиная с 0)

    Returns:
        Словарь с вопросом или сигнал завершения
    """
    try:
        if current_index >= len(JEWELRY_QUESTIONS):
            return {
                "status": "complete",
                "message": "Все вопросы о ювелирных украшениях заданы! Сейчас я проанализирую твой вкус."
            }

        question = JEWELRY_QUESTIONS[current_index]
        return {
            "status": "next_question",
            "question_id": question["id"],
            "question_text": question["text"],
            "category": question["category"],
            "index": current_index,
            "total": len(JEWELRY_QUESTIONS)
        }
    except Exception as e:
        logger.error(
            f"Error getting next jewelry question: {e}", exc_info=True)
        return {
            "status": "error",
            "message": "Ошибка при получении вопроса"
        }


@tool
async def analyze_jewelry_profile(answers: Dict[str, str]) -> Dict[str, any]:
    """Проанализировать ответы пользователя и составить профиль предпочтений в ювелирных украшениях.

    Args:
        answers: Словарь с ответами пользователя (question_id -> answer_text)

    Returns:
        Профиль предпочтений с выявленным стилем и рекомендациями
    """
    try:
        jewelry_profile = {
            "metal_preferences": [],
            "stone_preferences": [],
            "style_category": "",
            "design_preferences": [],
            "occasions_fit": [],
            "jewelry_types": [],
            "overall_style": "",
            "personality_traits": [],
            "recommended_pieces": [],
            "brand_recommendation": "",
            "summary": ""
        }

        # Анализируем металлы
        if "favorite_metal" in answers:
            metal = answers["favorite_metal"].lower()
            jewelry_profile["metal_preferences"].append(
                answers["favorite_metal"])

            if any(word in metal for word in ["жёлтое", "жёлтый"]):
                jewelry_profile["personality_traits"].append(
                    "Классичность, традиционность")
            elif any(word in metal for word in ["белое", "белый", "серебро", "платин"]):
                jewelry_profile["personality_traits"].append(
                    "Современность, свежесть")
            elif any(word in metal for word in ["розовое", "розовый"]):
                jewelry_profile["personality_traits"].append(
                    "Романтичность, женственность")
            elif any(word in metal for word in ["медь"]):
                jewelry_profile["personality_traits"].append(
                    "Оригинальность, альтернативность")

        # Анализируем типы украшений
        if "jewelry_type" in answers:
            jewelry_type = answers["jewelry_type"].lower()
            jewelry_profile["jewelry_types"].append(answers["jewelry_type"])

            if any(word in jewelry_type for word in ["кольца", "кольцо"]):
                jewelry_profile["design_preferences"].append(
                    "Фокус на ручных украшениях")
            if any(word in jewelry_type for word in ["серьги"]):
                jewelry_profile["design_preferences"].append(
                    "Внимание к лицу и чертам")
            if any(word in jewelry_type for word in ["браслет"]):
                jewelry_profile["design_preferences"].append(
                    "Динамичный стиль")
            if any(word in jewelry_type for word in ["колье", "цепочка"]):
                jewelry_profile["design_preferences"].append(
                    "Фокус на верхней части туловища")

        # Анализируем камни
        if "stone_preference" in answers:
            stone = answers["stone_preference"].lower()
            jewelry_profile["stone_preferences"].append(
                answers["stone_preference"])

            if any(word in stone for word in ["бриллиант", "алмаз"]):
                jewelry_profile["personality_traits"].append(
                    "Элегантность, люксовость")
            elif any(word in stone for word in ["жемчуг"]):
                jewelry_profile["personality_traits"].append(
                    "Утончённость, аристократичность")
            elif any(word in stone for word in ["изумруд", "рубин", "сапфир"]):
                jewelry_profile["personality_traits"].append(
                    "Смелость, яркость характера")
            elif any(word in stone for word in ["самоцвет", "натуральн"]):
                jewelry_profile["personality_traits"].append(
                    "Эко-сознание, натуральность")
            elif any(word in stone for word in ["без камн", "гладкие"]):
                jewelry_profile["personality_traits"].append(
                    "Минимализм, простота")

        # Анализируем стиль
        if "style_preference" in answers:
            style = answers["style_preference"].lower()

            if any(word in style for word in ["классическ"]):
                jewelry_profile["style_category"] = "Классический"
                jewelry_profile["personality_traits"].append(
                    "Консервативность, проверенность")
            elif any(word in style for word in ["минимализм"]):
                jewelry_profile["style_category"] = "Минимализм"
                jewelry_profile["personality_traits"].append(
                    "Лаконичность, функциональность")
            elif any(word in style for word in ["винтаж"]):
                jewelry_profile["style_category"] = "Винтаж"
                jewelry_profile["personality_traits"].append(
                    "Ностальгия, история")
            elif any(word in style for word in ["современн", "авангард"]):
                jewelry_profile["style_category"] = "Современный"
                jewelry_profile["personality_traits"].append(
                    "Прогрессивность, инновативность")
            elif any(word in style for word in ["этническ"]):
                jewelry_profile["style_category"] = "Этнический"
                jewelry_profile["personality_traits"].append(
                    "Культурность, многогранность")
            elif any(word in style for word in ["романтич"]):
                jewelry_profile["style_category"] = "Романтический"
                jewelry_profile["personality_traits"].append(
                    "Чувственность, нежность")

        # Анализируем случаи использования
        if "occasions" in answers:
            occasions = answers["occasions"].lower()
            jewelry_profile["occasions_fit"].append(answers["occasions"])

            if any(word in occasions for word in ["ежедневн"]):
                jewelry_profile["personality_traits"].append("Практичность")
            if any(word in occasions for word in ["вечерн", "праздник"]):
                jewelry_profile["personality_traits"].append(
                    "Любовь к роскоши")

        # Анализируем дизайн-элементы
        if "design_features" in answers:
            design = answers["design_features"].lower()
            jewelry_profile["design_preferences"].append(
                answers["design_features"])

            if any(word in design for word in ["ажур", "резн"]):
                jewelry_profile["personality_traits"].append(
                    "Кропотливость, внимание к деталям")
            elif any(word in design for word in ["объём", "3d"]):
                jewelry_profile["personality_traits"].append(
                    "Смелость в экспрессии")
            elif any(word in design for word in ["эмаль"]):
                jewelry_profile["personality_traits"].append(
                    "Цветолюбие, юность")

        # Анализируем отношение к брендам
        if "brand_attitude" in answers:
            brand = answers["brand_attitude"].lower()

            if any(word in brand for word in ["дорог", "бренд", "известн"]):
                jewelry_profile["brand_recommendation"] = "Люкс бренды (Cartier, Van Cleef & Arpels, Harry Winston)"
            elif any(word in brand for word in ["дизайнер", "малоизвестн"]):
                jewelry_profile["brand_recommendation"] = "Независимые дизайнеры и бутик-бренды"
            elif any(word in brand for word in ["handmade", "ручн"]):
                jewelry_profile["brand_recommendation"] = "Handmade мастера и авторские украшения"
            else:
                jewelry_profile["brand_recommendation"] = "Любые мастера с интересными работами"

        # Анализируем бюджет
        if "budget_range" in answers:
            budget = answers["budget_range"].lower()

            if any(word in budget for word in ["до 5k", "5к"]):
                jewelry_profile["personality_traits"].append(
                    "Экономность, осторожность")
            elif any(word in budget for word in ["50k", "100k", "100+"]):
                jewelry_profile["personality_traits"].append(
                    "Платёжеспособность, люксовость")

        # Анализируем выраженность украшений
        if "statement_vs_subtle" in answers:
            statement = answers["statement_vs_subtle"].lower()

            if any(word in statement for word in ["яркие", "заметн", "statement"]):
                jewelry_profile["overall_style"] = "Выраженный, привлекающий внимание"
                jewelry_profile["personality_traits"].append(
                    "Уверенность, экстравертность")
            elif any(word in statement for word in ["смешанн", "оба"]):
                jewelry_profile["overall_style"] = "Гибридный, адаптивный"
                jewelry_profile["personality_traits"].append(
                    "Гибкость, адаптивность")
            else:
                jewelry_profile["overall_style"] = "Деликатный, утончённый"
                jewelry_profile["personality_traits"].append(
                    "Скромность, тонкий вкус")

        # Генерируем рекомендации
        traits_str = ", ".join(jewelry_profile["personality_traits"]).lower()

        if "люксовост" in traits_str or "элегантност" in traits_str:
            jewelry_profile["recommended_pieces"].append(
                "Классические кольца с бриллиантами")
            jewelry_profile["recommended_pieces"].append("Жемчужные колье")

        if "минимализм" in traits_str or "лаконичност" in traits_str:
            jewelry_profile["recommended_pieces"].append(
                "Геометричные украшения")
            jewelry_profile["recommended_pieces"].append(
                "Минималистичные серьги-гвоздики")

        if "романтичност" in traits_str or "нежност" in traits_str:
            jewelry_profile["recommended_pieces"].append(
                "Нежные подвески с сердечками")
            jewelry_profile["recommended_pieces"].append("Ажурные браслеты")

        if "альтернативност" in traits_str or "оригинальност" in traits_str:
            jewelry_profile["recommended_pieces"].append(
                "Авторские украшения от независимых дизайнеров")
            jewelry_profile["recommended_pieces"].append(
                "Украшения из необычных материалов")

        if "традиционност" in traits_str or "классичност" in traits_str:
            jewelry_profile["recommended_pieces"].append("Классические обручи")
            jewelry_profile["recommended_pieces"].append("Строгие цепочки")

        # Удаляем дубликаты
        jewelry_profile["personality_traits"] = list(
            set(jewelry_profile["personality_traits"]))
        jewelry_profile["recommended_pieces"] = list(
            set(jewelry_profile["recommended_pieces"]))

        # Составляем резюме
        summary_parts = []
        if jewelry_profile["metal_preferences"]:
            summary_parts.append(
                f"Металл: {jewelry_profile['metal_preferences'][0]}")
        if jewelry_profile["style_category"]:
            summary_parts.append(f"Стиль: {jewelry_profile['style_category']}")
        if jewelry_profile["overall_style"]:
            summary_parts.append(
                f"Выраженность: {jewelry_profile['overall_style']}")

        if summary_parts:
            jewelry_profile["summary"] = " | ".join(summary_parts)

        logger.info(
            f"Jewelry profile analyzed: {len(jewelry_profile['personality_traits'])} traits detected")

        return jewelry_profile

    except Exception as e:
        logger.error(f"Error analyzing jewelry profile: {e}", exc_info=True)
        return {
            "status": "error",
            "message": "Ошибка при анализе предпочтений"
        }
