"""Tests for data generation"""

import pytest
from database.fill_data import (
    generate_products,
    generate_customer_preferences,
    generate_consultations,
    get_data_summary
)


@pytest.mark.asyncio
async def test_generate_products():
    """Test product generation"""
    products = await generate_products(count=10)
    
    assert len(products) == 10
    
    for product in products:
        assert product.name is not None
        assert product.category in ["rings", "necklaces", "bracelets", "earrings", "pendants"]
        assert product.material in ["gold", "silver", "platinum", "white_gold"]
        assert product.price > 0
        assert product.weight > 0
        assert isinstance(product.design_details, dict)
        assert isinstance(product.images, list)
        assert product.stock_count >= 0


@pytest.mark.asyncio
async def test_generate_customer_preferences():
    """Test customer preferences generation"""
    preferences = await generate_customer_preferences(count=5)
    
    assert len(preferences) == 5
    
    for pref in preferences:
        assert pref.user_id.startswith("user_")
        assert pref.style_preference in ["classic", "modern", "vintage", "minimalist", "luxury"]
        assert pref.budget_min > 0
        assert pref.budget_max > pref.budget_min
        assert len(pref.preferred_materials) > 0
        assert pref.skin_tone in ["warm", "cool", "neutral"]
        assert len(pref.occasion_types) > 0
        assert isinstance(pref.consultation_history, list)


@pytest.mark.asyncio
async def test_generate_consultations():
    """Test consultation generation"""
    user_ids = ["user_001", "user_002", "user_003"]
    consultations = await generate_consultations(count=10, user_ids=user_ids)
    
    assert len(consultations) == 10
    
    for consultation in consultations:
        assert consultation.user_id in user_ids
        assert consultation.agent_type == "consultant"
        assert consultation.message is not None
        assert consultation.response is not None
        assert len(consultation.recommendations) > 0
        assert isinstance(consultation.preference_updates, dict)
        assert consultation.created_at is not None


@pytest.mark.asyncio
async def test_product_name_generation():
    """Test product name generation is unique and realistic"""
    products = await generate_products(count=20)
    names = [p.name for p in products]
    
    # Check that names are generated
    assert all(name for name in names)
    
    # Check some diversity (at least 15 unique names out of 20)
    unique_names = set(names)
    assert len(unique_names) >= 15


@pytest.mark.asyncio
async def test_product_price_ranges():
    """Test that product prices are reasonable"""
    products = await generate_products(count=50)
    
    prices = [p.price for p in products]
    
    # All prices should be positive
    assert all(price > 0 for price in prices)
    
    # Prices should be in reasonable range (1000 to 150000)
    assert min(prices) >= 1000
    assert max(prices) <= 150000
    
    # Should have some variety
    assert len(set(prices)) > 30  # At least 30 different prices out of 50

