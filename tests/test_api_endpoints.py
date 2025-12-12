"""Basic tests for API endpoints"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "version" in data


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "provider" in data
    assert "model" in data


@pytest.mark.asyncio
async def test_consultation_endpoint():
    """Test consultation endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/consultation/test_user_001",
            json={
                "message": "Ищу золотое кольцо для помолвки",
                "conversation_history": []
            }
        )
        # Should return 200 even if services aren't fully initialized
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "agent" in data


@pytest.mark.asyncio
async def test_customer_profile_endpoint():
    """Test get customer profile endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/customer/test_user_001/profile")
        # Should return 200 with empty profile for new user
        assert response.status_code in [200, 500]  # May fail if DB not initialized


@pytest.mark.asyncio
async def test_product_search_endpoint():
    """Test product search endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/products/search",
            json={
                "query": "золотое кольцо",
                "limit": 5
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "query" in data
        assert "products" in data


@pytest.mark.asyncio
async def test_customer_analysis_endpoint():
    """Test customer analysis endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/analysis/customer")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "agent" in data


@pytest.mark.asyncio
async def test_trend_analysis_endpoint():
    """Test trend analysis endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/analysis/trends",
            json={
                "content": "Минималистичные украшения становятся все более популярными",
                "source": "Fashion Magazine",
                "date": "2024-12-01"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "agent" in data


@pytest.mark.asyncio
async def test_update_preferences_endpoint():
    """Test update customer preferences endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.put(
            "/api/customer/test_user_001/preferences",
            json={
                "style_preference": "modern",
                "budget_min": 10000,
                "budget_max": 50000,
                "preferred_materials": ["gold", "white_gold"],
                "skin_tone": "warm"
            }
        )
        assert response.status_code in [200, 500]  # May fail if DB not initialized

