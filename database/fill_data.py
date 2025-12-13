import asyncio
import random
from datetime import datetime, timedelta
from typing import List
from faker import Faker
from sqlalchemy import select, text

from database.session import async_session
from database.models import JewelryProduct, CustomerPreference, ConsultationRecord
from utils.logging import get_logger

logger = get_logger(__name__)
fake = Faker("ru_RU")


# Product data templates
CATEGORIES = ["rings", "necklaces", "bracelets", "earrings", "pendants"]
MATERIALS = ["gold", "silver", "platinum", "white_gold"]
STYLES = ["classic", "modern", "vintage", "minimalist", "luxury"]
SKIN_TONES = ["warm", "cool", "neutral"]
OCCASION_TYPES = ["everyday", "formal", "wedding", "gift"]

PRODUCT_TEMPLATES = {
    "rings": [
        "Кольцо с бриллиантом '{name}'",
        "Обручальное кольцо '{name}'",
        "Кольцо с изумрудом '{name}'",
        "Печатка '{name}'",
        "Помолвочное кольцо '{name}'"
    ],
    "necklaces": [
        "Колье '{name}'",
        "Цепочка '{name}'",
        "Ожерелье с подвеской '{name}'",
        "Чокер '{name}'"
    ],
    "bracelets": [
        "Браслет '{name}'",
        "Браслет-цепь '{name}'",
        "Жесткий браслет '{name}'",
        "Браслет с подвесками '{name}'"
    ],
    "earrings": [
        "Серьги-гвоздики '{name}'",
        "Серьги-капли '{name}'",
        "Серьги-кольца '{name}'",
        "Длинные серьги '{name}'"
    ],
    "pendants": [
        "Кулон '{name}'",
        "Подвеска '{name}'",
        "Религиозная подвеска '{name}'"
    ]
}

DESCRIPTIONS = {
    "classic": "Элегантное изделие в классическом стиле с изящными линиями и традиционным дизайном",
    "modern": "Современное украшение с лаконичными формами и актуальным дизайном",
    "vintage": "Винтажное изделие с налетом старины и утонченными деталями",
    "minimalist": "Минималистичное украшение с простыми линиями и сдержанным дизайном",
    "luxury": "Роскошное изделие премиум-класса с использованием драгоценных камней"
}

CONSULTATION_MESSAGES = [
    "Мне нужно кольцо для помолвки",
    "Ищу браслет в подарок жене",
    "Хочу что-то современное и необычное",
    "Нужны серьги на каждый день",
    "Подберите украшение на свадьбу",
    "Ищу золотое колье в классическом стиле",
    "Нужно что-то недорогое но красивое",
    "Хочу подарок девушке на день рождения",
    "Подберите украшение для делового стиля",
    "Ищу обручальные кольца"
]


def generate_product_name(category: str, style: str) -> str:
    """Generate product name based on category and style"""
    templates = PRODUCT_TEMPLATES[category]
    template = random.choice(templates)
    
    adjectives = ["Вечность", "Сияние", "Мечта", "Элегия", "Версаль", "Диамант", 
                  "Аврора", "Империал", "Венеция", "Фиренце", "Монако", "Прованс"]
    
    name = random.choice(adjectives)
    return template.format(name=name)


def generate_design_details(category: str, material: str, style: str) -> dict:
    """Generate design details JSON"""
    details = {
        "metal_purity": "585" if material in ["gold", "white_gold"] else "925",
        "style_notes": DESCRIPTIONS[style]
    }
    
    if category in ["rings", "earrings", "pendants"] and style in ["luxury", "classic"]:
        details.update({
            "stone_type": random.choice(["diamond", "emerald", "sapphire", "ruby"]),
            "stone_cut": random.choice(["round", "princess", "oval", "marquise"]),
            "stone_color": random.choice(["D", "E", "F", "G"]),
            "stone_clarity": random.choice(["VS1", "VS2", "SI1", "VVS1"])
        })
    
    return details


async def generate_products(count: int = 80) -> List[JewelryProduct]:
    """Generate jewelry products"""
    products = []
    
    for i in range(count):
        category = random.choice(CATEGORIES)
        material = random.choice(MATERIALS)
        style = random.choice(STYLES)
        
        name = generate_product_name(category, style)
        description = DESCRIPTIONS[style]
        
        # Price based on material and style
        base_price = 1000
        if material in ["platinum", "white_gold"]:
            base_price *= 2
        if style == "luxury":
            base_price *= 3
        
        price = base_price + random.randint(0, 50000)
        
        product = JewelryProduct(
            name=name,
            description=description,
            category=category,
            material=material,
            weight=round(random.uniform(2.0, 50.0), 2),
            price=price,
            design_details=generate_design_details(category, material, style),
            images=[f"{category}_{i+1}.jpg"],
            stock_count=random.randint(0, 20)
        )
        products.append(product)
    
    return products


async def generate_customer_preferences(count: int = 25) -> List[CustomerPreference]:
    """Generate customer preferences"""
    preferences = []
    
    for i in range(count):
        budget_min = random.choice([5000, 10000, 20000, 30000, 50000])
        budget_max = budget_min + random.randint(20000, 100000)
        
        pref = CustomerPreference(
            user_id=f"user_{i+1:03d}",
            style_preference=random.choice(STYLES),
            budget_min=budget_min,
            budget_max=budget_max,
            preferred_materials=random.sample(MATERIALS, k=random.randint(1, 3)),
            skin_tone=random.choice(SKIN_TONES),
            occasion_types=random.sample(OCCASION_TYPES, k=random.randint(1, 3)),
            consultation_history=[]
        )
        preferences.append(pref)
    
    return preferences


async def generate_consultations(
    count: int = 40,
    user_ids: List[str] = None
) -> List[ConsultationRecord]:
    """Generate consultation records"""
    if not user_ids:
        user_ids = [f"user_{i+1:03d}" for i in range(25)]
    
    consultations = []
    
    for i in range(count):
        user_id = random.choice(user_ids)
        message = random.choice(CONSULTATION_MESSAGES)
        
        # Generate realistic response
        response = (
            f"Спасибо за обращение! Я подобрал для вас несколько вариантов, "
            f"которые соответствуют вашим предпочтениям. "
            f"Все изделия представлены в нашем каталоге."
        )
        
        # Random product recommendations (would be real IDs in production)
        recommendations = [f"prod_{random.randint(1, 80):03d}" for _ in range(random.randint(2, 5))]
        
        # Random timestamp in last 30 days
        days_ago = random.randint(0, 30)
        created_at = datetime.utcnow() - timedelta(days=days_ago, 
                                                    hours=random.randint(0, 23),
                                                    minutes=random.randint(0, 59))
        
        consultation = ConsultationRecord(
            user_id=user_id,
            agent_type="consultant",
            message=message,
            response=response,
            recommendations=recommendations,
            preference_updates={"last_consultation": created_at.isoformat()},
            created_at=created_at
        )
        consultations.append(consultation)
    
    return consultations


async def clear_all_data():
    """Clear all data from database tables"""
    logger.info("Clearing all data from database...")
    
    async with async_session() as session:
        # Delete in correct order due to foreign keys
        await session.execute(text("DELETE FROM consultation_records"))
        await session.execute(text("DELETE FROM customer_preferences"))
        await session.execute(text("DELETE FROM jewelry_products"))
        await session.commit()
    
    logger.info("All data cleared successfully")


async def fill_database(
    products_count: int = 80,
    users_count: int = 25,
    consultations_count: int = 40,
    clear_existing: bool = False
):
    """Fill database with generated test data"""
    
    if clear_existing:
        await clear_all_data()
    
    logger.info("Generating test data...")
    
    # Generate products
    logger.info(f"Generating {products_count} products...")
    products = await generate_products(products_count)
    
    async with async_session() as session:
        session.add_all(products)
        await session.commit()
        logger.info(f"Added {len(products)} products to database")
    
    # Generate customer preferences
    logger.info(f"Generating {users_count} customer preferences...")
    preferences = await generate_customer_preferences(users_count)
    
    async with async_session() as session:
        session.add_all(preferences)
        await session.commit()
        logger.info(f"Added {len(preferences)} customer preferences to database")
    
    # Get user IDs for consultations
    user_ids = [pref.user_id for pref in preferences]
    
    # Generate consultations
    logger.info(f"Generating {consultations_count} consultation records...")
    consultations = await generate_consultations(consultations_count, user_ids)
    
    async with async_session() as session:
        session.add_all(consultations)
        await session.commit()
        logger.info(f"Added {len(consultations)} consultation records to database")
    
    logger.info("Database filled successfully!")
    logger.info(f"Summary: {len(products)} products, {len(preferences)} users, {len(consultations)} consultations")


async def get_data_summary():
    """Get summary of data in database"""
    async with async_session() as session:
        # Count products
        result = await session.execute(select(JewelryProduct))
        products = result.scalars().all()
        
        # Count preferences
        result = await session.execute(select(CustomerPreference))
        preferences = result.scalars().all()
        
        # Count consultations
        result = await session.execute(select(ConsultationRecord))
        consultations = result.scalars().all()
        
        summary = {
            "products": len(products),
            "users": len(preferences),
            "consultations": len(consultations)
        }
        
        if products:
            summary["product_categories"] = {}
            for product in products:
                category = product.category
                summary["product_categories"][category] = summary["product_categories"].get(category, 0) + 1
        
        return summary


if __name__ == "__main__":
    # Example usage
    async def main():
        await fill_database(
            products_count=80,
            users_count=25,
            consultations_count=40,
            clear_existing=False
        )
        
        summary = await get_data_summary()
        logger.info(f"Data summary: {summary}")
    
    asyncio.run(main())

