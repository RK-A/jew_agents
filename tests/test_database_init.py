"""Tests for database initialization"""

import pytest
import asyncio
from database.init_db import (
    check_connection,
    create_tables,
    get_table_counts
)
from database.session import async_session
from database.models import JewelryProduct, CustomerPreference, ConsultationRecord


@pytest.mark.asyncio
async def test_database_connection():
    """Test database connection"""
    connected = await check_connection()
    assert connected is True


@pytest.mark.asyncio
async def test_create_tables():
    """Test table creation"""
    try:
        await create_tables()
        # If no exception, tables were created or already exist
        assert True
    except Exception as e:
        pytest.fail(f"Failed to create tables: {e}")


@pytest.mark.asyncio
async def test_get_table_counts():
    """Test getting table counts"""
    counts = await get_table_counts()
    
    assert isinstance(counts, dict)
    assert "jewelry_products" in counts
    assert "customer_preferences" in counts
    assert "consultation_records" in counts
    
    # All counts should be non-negative
    for count in counts.values():
        assert count >= 0


@pytest.mark.asyncio
async def test_jewelry_product_model():
    """Test JewelryProduct model"""
    async with async_session() as session:
        # Create a test product
        product = JewelryProduct(
            name="Test Ring",
            description="Test ring for unit testing",
            category="rings",
            material="gold",
            weight=5.5,
            price=10000,
            design_details={"test": True},
            images=["test.jpg"],
            stock_count=1
        )
        
        session.add(product)
        await session.commit()
        
        # Verify it was created
        assert product.id is not None
        assert product.name == "Test Ring"
        assert product.category == "rings"
        
        # Clean up
        await session.delete(product)
        await session.commit()


@pytest.mark.asyncio
async def test_customer_preference_model():
    """Test CustomerPreference model"""
    async with async_session() as session:
        # Create a test preference
        pref = CustomerPreference(
            user_id="test_user_001",
            style_preference="modern",
            budget_min=10000,
            budget_max=50000,
            preferred_materials=["gold", "silver"],
            skin_tone="warm",
            occasion_types=["everyday"],
            consultation_history=[]
        )
        
        session.add(pref)
        await session.commit()
        
        # Verify it was created
        assert pref.user_id == "test_user_001"
        assert pref.style_preference == "modern"
        assert "gold" in pref.preferred_materials
        
        # Clean up
        await session.delete(pref)
        await session.commit()


@pytest.mark.asyncio
async def test_consultation_record_model():
    """Test ConsultationRecord model"""
    async with async_session() as session:
        # Create a test consultation
        consultation = ConsultationRecord(
            user_id="test_user_001",
            agent_type="consultant",
            message="Test message",
            response="Test response",
            recommendations=["prod_1", "prod_2"],
            preference_updates={"test": "value"}
        )
        
        session.add(consultation)
        await session.commit()
        
        # Verify it was created
        assert consultation.id is not None
        assert consultation.user_id == "test_user_001"
        assert consultation.agent_type == "consultant"
        assert len(consultation.recommendations) == 2
        
        # Clean up
        await session.delete(consultation)
        await session.commit()

