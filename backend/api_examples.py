"""
API Usage Examples for AI Jewelry Consultation System

This file contains examples of how to use the API endpoints.
Run the server first: python main.py or uvicorn main:app --reload

Available Endpoints:
-------------------

1. GET / - Root endpoint
2. GET /api/health - Health check
3. POST /api/consultation/{user_id} - User consultation
4. GET /api/customer/{user_id}/profile - Get customer profile
5. PUT /api/customer/{user_id}/preferences - Update preferences
6. POST /api/products/search - Search products
7. POST /api/analysis/customer - Run customer analysis
8. POST /api/analysis/trends - Run trend analysis

Interactive API Documentation:
-----------------------------
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
"""

import asyncio
import httpx


API_BASE_URL = "http://localhost:8000"


async def example_consultation():
    """Example: User consultation with AI agent"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/consultation/user_123",
            json={
                "message": "Ищу подарок для жены - золотой браслет",
                "conversation_history": []
            }
        )
        print("Consultation Response:")
        print(response.json())


async def example_get_profile():
    """Example: Get customer profile"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/customer/user_123/profile"
        )
        print("Customer Profile:")
        print(response.json())


async def example_update_preferences():
    """Example: Update customer preferences"""
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{API_BASE_URL}/api/customer/user_123/preferences",
            json={
                "style_preference": "modern",
                "budget_min": 20000,
                "budget_max": 100000,
                "preferred_materials": ["gold", "platinum"],
                "skin_tone": "neutral",
                "occasion_types": ["gift", "formal"]
            }
        )
        print("Update Response:")
        print(response.json())


async def example_search_products():
    """Example: Search for products"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/products/search",
            json={
                "query": "золотой браслет для женщины",
                "limit": 5,
                "filters": {
                    "category": "bracelets",
                    "price_min": 20000,
                    "price_max": 50000
                }
            }
        )
        print("Search Results:")
        print(response.json())


async def example_customer_analysis():
    """Example: Run customer analysis"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/analysis/customer"
        )
        print("Customer Analysis:")
        print(response.json())


async def example_trend_analysis():
    """Example: Run trend analysis"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/analysis/trends",
            json={
                "content": """
                В новом сезоне дизайнеры делают акцент на натуральных камнях
                и органических формах. Особенно популярны украшения с изумрудами
                и сапфирами в простых геометрических оправах из желтого золота.
                """,
                "source": "Vogue Jewelry",
                "date": "2024-12-12"
            }
        )
        print("Trend Analysis:")
        print(response.json())


async def example_health_check():
    """Example: Health check"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/health")
        print("Health Status:")
        print(response.json())


async def run_all_examples():
    """Run all examples"""
    print("=== API Usage Examples ===\n")
    
    print("1. Health Check")
    await example_health_check()
    print("\n" + "="*50 + "\n")
    
    print("2. User Consultation")
    await example_consultation()
    print("\n" + "="*50 + "\n")
    
    print("3. Get Customer Profile")
    await example_get_profile()
    print("\n" + "="*50 + "\n")
    
    print("4. Update Preferences")
    await example_update_preferences()
    print("\n" + "="*50 + "\n")
    
    print("5. Search Products")
    await example_search_products()
    print("\n" + "="*50 + "\n")
    
    print("6. Customer Analysis")
    await example_customer_analysis()
    print("\n" + "="*50 + "\n")
    
    print("7. Trend Analysis")
    await example_trend_analysis()
    print("\n" + "="*50 + "\n")


if __name__ == "__main__":
    # Run all examples
    asyncio.run(run_all_examples())
    
    # Or run individual examples:
    # asyncio.run(example_consultation())
    # asyncio.run(example_search_products())

