"""Tools for girlfriend agent"""

import aiohttp
import logging
from typing import Literal
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Free horoscope API (no auth required)
# Docs: https://ohmanda.com/api/horoscope/
HOROSCOPE_API_BASE_URL = "https://ohmanda.com/api/horoscope"


@tool
async def get_horoscope(
    sign: Literal[
        "aries", "taurus", "gemini", "cancer",
        "leo", "virgo", "libra", "scorpio",
        "sagittarius", "capricorn", "aquarius", "pisces"
    ],
    day: Literal["today", "tomorrow", "yesterday"] = "today"
) -> str:
    """Получить ежедневный гороскоп.
    
    Args:
        sign: Zodiac sign (aries, taurus, gemini, cancer, leo, virgo,
              libra, scorpio, sagittarius, capricorn, aquarius, pisces)
        day: Day to get horoscope for (today, tomorrow, yesterday)
    
    Returns:
        Текст гороскопа на день (источник: публичный API)
    """
    try:
        # ohmanda API currently serves a daily horoscope; "day" kept for compatibility with the agent/tool schema
        sign = (sign or "").strip().lower()
        if sign == "unknown" or not sign:
            return "Я не поняла знак зодиака. Напиши, пожалуйста, один из: aries, taurus, gemini, cancer, leo, virgo, libra, scorpio, sagittarius, capricorn, aquarius, pisces."

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{HOROSCOPE_API_BASE_URL}/{sign}/",
                headers={"Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=12),
            ) as response:
                if response.status != 200:
                    logger.error(f"Horoscope API returned status {response.status}")
                    return "Не получилось получить гороскоп прямо сейчас. Хочешь, я помогу сформулировать вопрос/настрой на день без астрологии?"

                data = await response.json()
                date = data.get("date") or ""
                horoscope = (data.get("horoscope") or "").strip()
                if not horoscope:
                    return "Я получила ответ от сервиса, но текст гороскопа пустой. Давай попробуем ещё раз через минуту."

                # Keep sign in English token; the agent can rephrase if user wants.
                return f"Гороскоп для {sign} ({date}, {day}):\n\n{horoscope}"
    
    except Exception as e:
        logger.error(f"Error fetching horoscope: {e}", exc_info=True)
        return "Ой, я не смогла достать гороскоп из сервиса. Давай попробуем ещё раз или поговорим о чём-то другом?"


@tool
async def detect_zodiac_sign(birthdate: str) -> str:
    """Определить знак зодиака по дате рождения.
    
    Args:
        birthdate: Date in format 'MM/DD' or 'YYYY-MM-DD'
    
    Returns:
        Название знака (eng token: aries/taurus/...) или "unknown"
    """
    try:
        # Parse date
        if '-' in birthdate:
            parts = birthdate.split('-')
            month = int(parts[1] if len(parts) == 3 else parts[0])
            day = int(parts[2] if len(parts) == 3 else parts[1])
        else:
            parts = birthdate.split('/')
            month = int(parts[0])
            day = int(parts[1])
        
        # Zodiac signs date ranges
        if (month == 3 and day >= 21) or (month == 4 and day <= 19):
            return "aries"
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            return "taurus"
        elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
            return "gemini"
        elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
            return "cancer"
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            return "leo"
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            return "virgo"
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
            return "libra"
        elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
            return "scorpio"
        elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
            return "sagittarius"
        elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
            return "capricorn"
        elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
            return "aquarius"
        else:  # Pisces
            return "pisces"
    
    except Exception as e:
        logger.error(f"Error detecting zodiac sign: {e}", exc_info=True)
        return "unknown"
