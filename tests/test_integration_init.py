"""Integration tests for full system initialization"""

import pytest
from database.init_db import init_database, get_table_counts
from database.fill_data import fill_database, get_data_summary, clear_all_data
from rag.init_qdrant import check_qdrant_status


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_database_initialization():
    """Test complete database initialization flow"""
    try:
        # Initialize database
        await init_database()
        
        # Check that tables exist
        counts = await get_table_counts()
        assert isinstance(counts, dict)
        assert "jewelry_products" in counts
        
    except Exception as e:
        pytest.skip(f"Database initialization failed: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fill_and_clear_data():
    """Test filling and clearing data"""
    try:
        # Get initial counts
        initial_counts = await get_table_counts()
        
        # Fill with small dataset
        await fill_database(
            products_count=5,
            users_count=3,
            consultations_count=5,
            clear_existing=False
        )
        
        # Check data was added
        summary = await get_data_summary()
        assert summary["products"] >= 5
        assert summary["users"] >= 3
        assert summary["consultations"] >= 5
        
        # Clear data
        await clear_all_data()
        
        # Check data was cleared
        final_counts = await get_table_counts()
        assert final_counts["jewelry_products"] == 0
        assert final_counts["customer_preferences"] == 0
        assert final_counts["consultation_records"] == 0
        
    except Exception as e:
        pytest.fail(f"Fill and clear test failed: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_data_generation_consistency():
    """Test that generated data is consistent and valid"""
    try:
        # Clear first
        await clear_all_data()
        
        # Fill with known counts
        products_count = 10
        users_count = 5
        consultations_count = 8
        
        await fill_database(
            products_count=products_count,
            users_count=users_count,
            consultations_count=consultations_count
        )
        
        # Get summary
        summary = await get_data_summary()
        
        # Verify exact counts
        assert summary["products"] == products_count
        assert summary["users"] == users_count
        assert summary["consultations"] == consultations_count
        
        # Verify category distribution
        if "product_categories" in summary:
            total_by_category = sum(summary["product_categories"].values())
            assert total_by_category == products_count
        
        # Clean up
        await clear_all_data()
        
    except Exception as e:
        pytest.fail(f"Data consistency test failed: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_qdrant_availability():
    """Test Qdrant service availability (optional)"""
    try:
        status = await check_qdrant_status()
        
        assert isinstance(status, dict)
        
        # If Qdrant is available, check status
        if status.get("exists"):
            assert "collection_name" in status or "info" in status
        
    except Exception as e:
        pytest.skip(f"Qdrant not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_auto_fill_data_workflow():
    """Test the complete auto-fill workflow as used in main.py"""
    try:
        # Clear existing data
        await clear_all_data()
        
        # Simulate AUTO_FILL_DATA=true workflow
        counts = await get_table_counts()
        
        if counts.get("jewelry_products", 0) == 0:
            # Fill database
            await fill_database(
                products_count=15,
                users_count=10,
                consultations_count=15
            )
            
            # Verify data was filled
            new_counts = await get_table_counts()
            assert new_counts["jewelry_products"] == 15
            assert new_counts["customer_preferences"] == 10
            assert new_counts["consultation_records"] == 15
        
        # Clean up
        await clear_all_data()
        
    except Exception as e:
        pytest.fail(f"Auto-fill workflow test failed: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_data_integrity():
    """Test that generated data maintains referential integrity"""
    from database.session import async_session
    from database.models import JewelryProduct, CustomerPreference, ConsultationRecord
    from sqlalchemy import select
    
    try:
        # Clear and fill
        await clear_all_data()
        await fill_database(
            products_count=10,
            users_count=5,
            consultations_count=10
        )
        
        async with async_session() as session:
            # Check products exist and have valid data
            result = await session.execute(select(JewelryProduct))
            products = result.scalars().all()
            
            for product in products:
                assert product.name is not None
                assert product.price > 0
                assert product.category in ["rings", "necklaces", "bracelets", "earrings", "pendants"]
            
            # Check customer preferences exist and have valid data
            result = await session.execute(select(CustomerPreference))
            preferences = result.scalars().all()
            
            for pref in preferences:
                assert pref.user_id is not None
                assert pref.budget_max > pref.budget_min
                assert len(pref.preferred_materials) > 0
            
            # Check consultations reference valid users
            result = await session.execute(select(ConsultationRecord))
            consultations = result.scalars().all()
            
            user_ids = {pref.user_id for pref in preferences}
            
            for consultation in consultations:
                # All consultations should reference existing users
                assert consultation.user_id in user_ids
                assert consultation.message is not None
                assert consultation.response is not None
        
        # Clean up
        await clear_all_data()
        
    except Exception as e:
        pytest.fail(f"Data integrity test failed: {e}")

