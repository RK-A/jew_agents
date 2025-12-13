"""Pytest configuration and fixtures"""

import pytest
import asyncio
from typing import AsyncGenerator

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_test_database():
    """Setup test database (session scope)"""
    from database.init_db import create_tables, check_connection
    from database.init_db import drop_tables
    
    # Check connection
    connected = await check_connection()
    if not connected:
        pytest.skip("Database not available")
    
    await drop_tables()
    await create_tables()
    
    yield
    
    # Cleanup after all tests (optional)
    # await drop_tables()


@pytest.fixture
async def clean_test_data():
    """Clean test data after each test"""
    yield
    
    # Cleanup test data created during test
    from database.session import async_session
    
    async with async_session() as session:
        # Delete test records
        await session.execute("DELETE FROM consultation_records WHERE user_id LIKE 'test_%'")
        await session.execute("DELETE FROM customer_preferences WHERE user_id LIKE 'test_%'")
        await session.execute("DELETE FROM jewelry_products WHERE name LIKE 'Test%'")
        await session.commit()


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    return {
        "message": "Test response from LLM",
        "recommendations": ["prod_1", "prod_2", "prod_3"],
        "questions": ["What is your budget?", "What style do you prefer?"]
    }


@pytest.fixture
def sample_product_data():
    """Sample product data for testing"""
    return {
        "name": "Test Diamond Ring",
        "description": "Beautiful diamond ring for testing",
        "category": "rings",
        "material": "gold",
        "weight": 5.5,
        "price": 50000,
        "design_details": {
            "metal_purity": "585",
            "stone_type": "diamond"
        },
        "images": ["test_ring.jpg"],
        "stock_count": 10
    }


@pytest.fixture
def sample_customer_preference():
    """Sample customer preference for testing"""
    return {
        "user_id": "test_user_001",
        "style_preference": "modern",
        "budget_min": 20000,
        "budget_max": 80000,
        "preferred_materials": ["gold", "platinum"],
        "skin_tone": "warm",
        "occasion_types": ["wedding", "formal"],
        "consultation_history": []
    }


@pytest.fixture
def sample_consultation():
    """Sample consultation data for testing"""
    return {
        "user_id": "test_user_001",
        "agent_type": "consultant",
        "message": "I need a ring for engagement",
        "response": "Here are some recommendations...",
        "recommendations": ["prod_1", "prod_2"],
        "preference_updates": {"occasion_types": ["wedding"]}
    }

