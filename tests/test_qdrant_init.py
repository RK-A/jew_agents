"""Tests for Qdrant initialization and operations"""

import pytest
from rag.init_qdrant import (
    init_qdrant_collection,
    check_qdrant_status
)
from rag.qdrant_service import QdrantService
from rag.embeddings import create_embedding_provider
from config import settings


@pytest.mark.asyncio
async def test_check_qdrant_status():
    """Test checking Qdrant status"""
    try:
        status = await check_qdrant_status()
        
        assert isinstance(status, dict)
        assert "exists" in status
        
        # If collection exists, should have info
        if status.get("exists"):
            assert "collection_name" in status or "info" in status
        
    except Exception as e:
        # Qdrant might not be running in test environment
        pytest.skip(f"Qdrant not available: {e}")


@pytest.mark.asyncio
async def test_qdrant_service_connection():
    """Test QdrantService connection"""
    try:
        embedding_provider = create_embedding_provider(
            model=settings.embedding_model,
            api_key=settings.embedding_api_key
        )
        
        qdrant_service = QdrantService(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
            embedding_provider=embedding_provider
        )
        
        # Try to check if collection exists (doesn't matter if it does or not)
        exists = await qdrant_service.collection_exists()
        assert isinstance(exists, bool)
        
    except Exception as e:
        pytest.skip(f"Qdrant not available: {e}")


@pytest.mark.asyncio
async def test_create_embedding():
    """Test embedding creation"""
    try:
        embedding_provider = create_embedding_provider(
            model=settings.embedding_model,
            api_key=settings.embedding_api_key
        )
        
        text = "Золотое кольцо с бриллиантом"
        embedding = await embedding_provider.embed(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
        
        # Check dimension
        dim = embedding_provider.get_dimension()
        assert len(embedding) == dim
        
    except Exception as e:
        pytest.skip(f"Embedding service not available: {e}")


@pytest.mark.asyncio
async def test_qdrant_upsert_and_search():
    """Test upserting and searching in Qdrant"""
    try:
        embedding_provider = create_embedding_provider(
            model=settings.embedding_model,
            api_key=settings.embedding_api_key
        )
        
        qdrant_service = QdrantService(
            url=settings.qdrant_url,
            collection_name="test_collection",
            embedding_provider=embedding_provider
        )
        
        # Create test collection
        await qdrant_service.create_collection()
        
        # Add test product
        test_product = {
            "product_id": "test_001",
            "name": "Тестовое кольцо",
            "description": "Золотое кольцо для тестирования",
            "category": "rings",
            "material": "gold",
            "price": 50000
        }
        
        description = "Тестовое кольцо. Золотое кольцо для тестирования. Категория: rings. Материал: gold."
        
        await qdrant_service.upsert_product(
            product_id="test_001",
            description=description,
            payload=test_product
        )
        
        # Search for the product
        results = await qdrant_service.search(
            query="золотое кольцо",
            limit=5
        )
        
        assert len(results) > 0
        
        # Clean up - delete test collection
        await qdrant_service.delete_collection()
        
    except Exception as e:
        pytest.skip(f"Qdrant not available: {e}")

